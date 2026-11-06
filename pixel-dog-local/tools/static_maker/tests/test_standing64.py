import json
from copy import deepcopy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import maker
import standing64


def pose():
    return {
        "format": "standing64-v2", "head_scale": 2, "head_anchor": [20, 20],
        "head_parts": ["head","ear"],
        "palette": dict(outline="#221122",dark="#333333",grey="#999999",light="#dddddd",white="#ffffff"),
        "parts": [
            dict(name="head", fill="grey", shape=[[16,16],[24,16],[24,24],[16,24]],
                 markings=[dict(color="light",polygon=[[16,18],[24,18],[16,18]])]),
            dict(name="ear", fill="light", shape=[[24,16],[26,16],[26,20],[24,20]],markings=[]),
            dict(name="leg", fill="grey", shape=[[36,30],[39,30],[44,40],[41,40]],markings=[])
        ],
        "seams": [], "eyes": [], "nose": [[20,20]]*3, "mouth": [[20,21],[21,21]], "shadows": [],
    }


class StandingRenderTest(unittest.TestCase):
    def test_seated_hindleg_follows_fold_and_local_foot_edits(self):
        profile = pose()
        component = "seated_near_hindleg"
        profile["parts"][-1] = dict(name="leg", component=component, fill="grey", markings=[])
        joints = dict(hip=[43,36,3], stifle=[32,43,3], tarsus=[46,50,2],
                      mtp=[40,54,2], toe_tip=[36,54,1])
        profile["seated_limbs"] = {component: joints}
        stages = {}
        original = standing64.render(profile, stages=stages)
        for x,y,_ in joints.values():
            self.assertEqual(stages["ownership"].getpixel((x,y)), 3)
        self.assertEqual(original.getpixel((45,43))[3], 0)
        joints["toe_tip"] = [33,54,1]
        changed = standing64.render(profile)
        self.assertEqual(original.crop((0,0,64,51)).tobytes(), changed.crop((0,0,64,51)).tobytes())
        self.assertEqual(changed.getpixel((33,54))[3], 255)
        self.assertEqual(original.getpixel((33,54))[3], 0)
        joints.pop("stifle")
        with self.assertRaisesRegex(ValueError, "stifle"):
            standing64.render(profile)

    def test_coat_regions_clip_to_material_and_preserve_the_eye(self):
        p = pose()
        p["head_scale"] = 1
        p["parts"][0]["markings"][0]["color"] = "white"
        p["parts"][1]["fill"] = "grey"
        p["eyes"] = [dict(center=[19,18], offset=[0,0], rows=["w"])]
        region = dict(part="head", base="white", runs=[[18,17,21],[19,17,20]])
        p["coat_lighting"] = dict(direction="upper-left", regions=[region])
        im = standing64.render(p)
        self.assertEqual(im.getpixel((18,18)), (221,221,221,255))
        self.assertEqual(im.getpixel((19,18)), (255,255,255,255))
        self.assertEqual(im.getpixel((18,19)), (153,153,153,255))
        p["eyes"][0]["side"] = "left"
        p["head_view"] = dict(angle="front", foreground=[[[18,17],[20,17],[20,19],[18,19]]])
        self.assertEqual(standing64.render(p).getpixel((19,18)), (221,221,221,255))
        region["runs"] = [[18,17,18],[19,19,20]]
        with self.assertRaisesRegex(ValueError, "4-connected"):
            standing64.render(p)
        p["parts"][1]["fill"] = "light"
        with self.assertRaisesRegex(ValueError, "base coat roles"):
            standing64.render(p)

    def test_alternate_pose_does_not_replace_default_or_fall_back(self):
        seated = dict(pose="seated", profile="seated.json")
        default = dict(pose="stand", profile="stand.json", poses={"seated": seated})
        with patch.object(standing64, "baseline_catalog", return_value={"dog": default}):
            self.assertEqual(standing64.baseline_for_pose("dog"), default)
            self.assertEqual(standing64.baseline_for_pose("dog", "seated"), seated)
            with self.assertRaises(ValueError):
                standing64.baseline_for_pose("dog", "lying")

    def test_shading_only_changes_registered_coat_and_retains_eye_ink(self):
        from photo_pose import simplify_face_shading

        profile=pose()
        profile.update(head_scale=1, face_coordinates="native", face_planes={},
                       eyes=[dict(center=[19,20],offset=[0,0],rows=["d"])])
        prior=standing64.render(profile)
        zones=[dict(base="light",alternate="white",vertices=[[18,19],[22,19],[22,22],[18,22]])]
        simplify_face_shading(profile,zones,lambda p:p,1,{})
        result=standing64.render(profile)
        self.assertEqual(result.getpixel((19,20)),prior.getpixel((19,20)))
        self.assertNotEqual(result.getpixel((19,19)),prior.getpixel((19,19)))
        self.assertEqual(result.getpixel((17,20)),prior.getpixel((17,20)))
        self.assertEqual(result.getchannel("A").tobytes(),prior.getchannel("A").tobytes())

    def test_native_aperture_reveals_the_part_behind_the_lip(self):
        profile = pose()
        profile.update(head_scale=1, face_coordinates="native")
        head = profile["parts"][0]
        head["native_cutouts"] = [[19,19],[21,19]]
        profile["parts"].insert(0, dict(name="behind",fill="light",
            shape=[[18,18],[20,18],[20,20],[18,20]],markings=[]))
        stages = {}
        frame = standing64.render(profile, stages=stages)
        self.assertEqual(stages["ownership"].getpixel((19,19)), 1)
        self.assertEqual(frame.getpixel((21,19))[3], 0)
        self.assertEqual(stages["ownership"].getpixel((19,20)), 2)

    def test_native_eye_keeps_its_grid_position_and_glint_alone_fails_review(self):
        from photo_pose import check_visible_features

        profile = pose()
        profile.update(dog_id="fixture", face_coordinates="native", mouth=[],
                       nose_surface={"color":"outline"}, nose=[[18,22],[20,22],[19,23]],
                       eyes=[dict(center=[21,20], offset=[0,-1], rows=[".l","dd"])])
        check_visible_features(profile)
        self.assertEqual(standing64.render(profile).getpixel((21,20)), (51,51,51,255))
        profile["face_planes"] = {"dark":[[21,20],[22,20]]}
        with self.assertRaisesRegex(ValueError, "indistinct eye core"):
            check_visible_features(profile)

    def test_final_ink_cannot_repaint_protected_outer_contour(self):
        profile = pose()
        profile.update(head_scale=1,preserve_outline=True,
                       details=[dict(part="head",color="white",polygon=[[16,18],[18,18]])])
        img = standing64.render(profile)
        self.assertEqual(img.getpixel((16,18)), (34,17,34,255))
        self.assertEqual(img.getpixel((17,18)), (255,255,255,255))

    def test_roster_does_not_publish_partial_results(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = json.loads((ROOT/"example.json").read_text(encoding="utf-8"))
            store = maker.Store(root/"profiles.sqlite")
            try:
                store.save(base,0,"fixture")
            finally:
                store.close()
            profile = dict(pose(),dog_id=base["dog_id"],source_revision=1,
                           source_sha256=maker.digest(maker.canonical(base).encode()))
            (root/"pose.json").write_text(json.dumps(profile),encoding="utf-8")
            entry = dict(profile="pose.json",database="profiles.sqlite",status="candidate",pose="stand",
                         authoring_sha256=maker.digest(maker.canonical(profile).encode()),
                         rgba_sha256=maker.digest(standing64.render(profile).tobytes()))
            catalog = {base["dog_id"]:entry,"missing":{**entry,"database":"missing.sqlite"}}
            (root/"standing-baselines.json").write_text(json.dumps(catalog),encoding="utf-8")
            with patch.object(standing64,"__file__",str(root/"standing64.py")):
                with self.assertRaises(FileNotFoundError):
                    standing64.export_roster(root/"all")
                self.assertFalse((root/"all").exists())

    def test_registered_baseline_rejects_stale_profile_or_changed_pixels(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            observation = {"dog_id": "fixture"}
            store = Mock()
            store.get.return_value = observation, 1
            profile = dict(pose(), dog_id="fixture", source_revision=1,
                           source_sha256=maker.digest(maker.canonical(observation).encode()))
            spec = root / "pose.json"
            spec.write_text(json.dumps(profile), encoding="utf-8")
            entry = {"profile": spec.name,
                     "authoring_sha256": maker.digest(maker.canonical(profile).encode()),
                     "rgba_sha256": maker.digest(standing64.render(profile).tobytes())}
            catalog = root / "standing-baselines.json"
            with patch.object(standing64, "__file__", str(root / "standing64.py")):
                catalog.write_text(json.dumps({"fixture": entry}), encoding="utf-8")
                standing64.export(store, "fixture", None, root / "ok")
                with self.assertRaisesRegex(ValueError, "no working standing baseline"):
                    standing64.export(store, "unknown", None, root / "bad")
                for field, message in (("authoring_sha256", "profile differs"),
                                       ("rgba_sha256", "pixels differ")):
                    stale = {**entry, field: "0" * 64}
                    catalog.write_text(json.dumps({"fixture": stale}), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, message):
                        standing64.export(store, "fixture", None, root / "bad")
                    self.assertFalse((root / "bad").exists())

    def test_stages_share_final_alpha_including_fur_gaps(self):
        p = pose()
        p["head_scale"] = 1
        p["parts"][0]["fur_gaps"] = [[17,17]]
        p["shadows"] = [{"part":"head","polygon":[[16,18],[23,18],[20,24]],
                         "from":"grey","to":"dark"}]
        p["details"] = [{"part":"head","polygon":[[20,22]],"color":"white"}]
        stages = {}
        final = standing64.render(p, stages=stages)
        for name in ("S1","S2","shade","S3"):
            self.assertEqual(stages[name].getchannel("A").tobytes(),final.getchannel("A").tobytes())
        self.assertEqual(stages["ownership"].getpixel((17,17)),0)
        self.assertEqual(stages["S3"].tobytes(),standing64.render(p).tobytes())
        self.assertNotEqual(stages["S2"].tobytes(),stages["shade"].tobytes())
        self.assertNotEqual(stages["shade"].tobytes(),final.tobytes())

    def test_common_body_dimensions_change_parts_at_fixed_pose(self):
        p = pose()
        p["morphology"] = dict(trunk_length=22,chest_depth=12,belly_tuck=3,foreleg_width=4)
        p["stance"] = dict(withers=[25,24],facing=-1,feet={"near_foreleg":[26,54]})
        p["parts"] = [dict(name=k,component=k,fill="grey",markings=[])
                      for k in ("trunk","chest","near_foreleg")] + [p["parts"][0]]
        p["head_parts"] = ["head"]
        p["parts"][0]["markings"] = [dict(color="light",uv=[[0,0],[.2,.5],[0,1]])]
        a,b = {},{}
        standing64.render(p,stages=a)
        other = deepcopy(p)
        other["morphology"].update(trunk_length=29,chest_depth=10,foreleg_width=2)
        standing64.render(other,stages=b)
        self.assertNotEqual(a["ownership"].getbbox(),b["ownership"].getbbox())
        for stages in (a,b):
            self.assertEqual(stages["ownership"].getpixel((26,54)),3)
            self.assertEqual(stages["ownership"].getpixel((20,20)),4)
        self.assertNotIn("shape",p["parts"][0])

    def test_view_hides_far_eye_and_clips_features_to_foreground(self):
        p = pose()
        p.update(head_scale=1,eyes=[dict(side=s,center=[x,19],offset=[0,0],rows=["i"])
                                    for s,x in [("left",18),("right",22)]],
                 details=[dict(part="head",feature="right_eye",color="white",polygon=[[22,19]])])
        p["head_view"] = dict(angle="profile",near_eye="left")
        p["shadows"] = [dict(part="head",feature="right_eye",polygon=[[22,19]]*3,
                              **{"from":"grey","to":"white"})]
        profile = standing64.render(p)
        p["head_view"] = dict(angle="front")
        front = standing64.render(p)
        self.assertEqual(profile.getpixel((18,19)),front.getpixel((18,19)))
        self.assertNotEqual(profile.getpixel((22,19)),front.getpixel((22,19)))
        p["head_view"]["foreground"] = [[[17,18],[21,18],[21,22],[17,22]]]
        p["nose_surface"] = {"color":"dark","reflection":{"at":[20,20],"color":"white"}}
        covered = standing64.render(p)
        self.assertEqual(covered.getpixel((20,20))[:3],(153,153,153))
        self.assertEqual(covered.getpixel((18,19))[:3],(153,153,153))

    def test_jaw_is_marked_only_where_its_underside_touches_the_bib(self):
        p = pose()
        p.update(head_scale=1, head_view=dict(angle="front",jaw_over=["bib"]))
        p["parts"].insert(0,dict(name="bib",fill="light",markings=[],
                                 shape=[[14,22],[20,22],[20,28],[14,28]]))
        with_edge = standing64.render(p)
        del p["head_view"]["jaw_over"]
        base = standing64.render(p)
        changes=[(x,y) for y in range(64) for x in range(64)
                 if with_edge.getpixel((x,y))!=base.getpixel((x,y))]
        self.assertTrue(changes)
        self.assertTrue(all(y==24 and x<=20 for x,y in changes))

    def test_generated_body_retains_outline_at_canvas_edge_after_shading(self):
        p = pose()
        p["stance"] = dict(withers=[23,22],facing=1)
        p["morphology"] = dict(trunk_length=23,chest_depth=9,belly_tuck=2,foreleg_width=3)
        p["parts"].insert(0,dict(name="trunk",component="trunk",markings=[],fill="grey"))
        p["shadows"] = [{"part":"trunk","uv":[[.5,0],[1,0],[1,1],[.5,1]],
                         "from":"outline","to":"dark"}]
        im=standing64.render(p)
        edge=[im.getpixel((0,y)) for y in range(64) if im.getpixel((0,y))[3]]
        self.assertTrue(edge)
        self.assertEqual(set(edge),{(34,17,34,255)})
    def test_omitted_head_scale_enlarges_new_profiles_and_fits_the_whole_group(self):
        p = pose()
        del p["head_scale"]
        self.assertEqual(standing64.head_scale(p), 1.55)
        auto = standing64.render(p)
        self.assertEqual(auto.tobytes(), standing64.render({**p, "head_scale":1.55}).tobytes())
        self.assertNotEqual(auto.tobytes(), standing64.render({**p, "head_scale":1}).tobytes())
        # A separate ear near the right edge limits the whole group's scale.
        p["head_anchor"] = [20,20]
        p["parts"][1]["shape"] = [[52,16],[56,16],[56,20],[52,20]]
        self.assertAlmostEqual(standing64.head_scale(p), (62-20)/(56-20))
        self.assertEqual(standing64.render(p).getbbox()[2],63)
        self.assertEqual(standing64.head_scale({**p,"head_scale":1.42}),1.42)
        with self.assertRaises(KeyError):
            standing64.render({**p,"format":"standing64-v1"})

    def test_export_recovers_from_transient_windows_directory_lock(self):
        p = pose()
        observation = json.loads((ROOT/"example.json").read_text(encoding="utf-8"))
        p.update(dog_id=observation["dog_id"], source_revision=1,
                 source_sha256=maker.digest(maker.canonical(observation).encode()))
        store = Mock()
        store.get.return_value = (observation,1)
        rename = Path.rename
        calls = []
        def locked_once(source, target):
            calls.append(target)
            if len(calls) == 1:
                error = PermissionError("sharing violation")
                error.winerror = 32
                raise error
            return rename(source,target)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"profile.json"
            path.write_text(json.dumps(p),encoding="utf-8")
            out = Path(directory)/"out"
            with patch.object(Path,"rename",locked_once):
                standing64.export(store,p["dog_id"],path,out)
            self.assertEqual(calls,[out,out])
            self.assertTrue((out/"review.json").is_file())

    def test_attached_ear_and_coat_use_same_head_scale(self):
        p = pose()
        im = standing64.render(p)
        self.assertEqual(im.getpixel((32,14))[3], 255)  # scaled far ear
        self.assertEqual(im.getpixel((20,16))[:3], (221,221,221))
        self.assertEqual(im.getpixel((20,17))[:3], (221,221,221))  # no skipped scanline
        p["head_parts"] = ["head","missing"]
        with self.assertRaises(ValueError):
            standing64.render(p)

    def test_details_are_ordered_and_clipped_at_part_overlaps(self):
        p = pose()
        before = standing64.render(p)
        p["details"] = [
            dict(part="head",color="dark",polygon=[[20,17],[26,17]]),
            dict(part="head",color="white",polygon=[[21,17]]),
        ]
        im = standing64.render(p)
        self.assertEqual(im.getpixel((20,14))[:3], (51,51,51))
        self.assertEqual(im.getpixel((22,14))[:3], (255,255,255))
        self.assertEqual(im.getpixel((30,14)), before.getpixel((30,14)))  # ear occludes head
        self.assertEqual(im.getchannel("A").tobytes(), before.getchannel("A").tobytes())

    def test_thin_diagonal_leg_preserves_interior_not_outer_edge(self):
        p = pose()
        before = standing64.render(p)
        p["parts"][-1]["outline_neighbors"] = 4
        after = standing64.render(p)
        self.assertEqual(after.getchannel("A").tobytes(), before.getchannel("A").tobytes())
        changes = [(x,y) for y in range(64) for x in range(64)
                   if before.getpixel((x,y)) != after.getpixel((x,y))]
        self.assertTrue(changes)
        for x,y in changes:
            self.assertGreaterEqual(y,30)
            self.assertEqual(after.getpixel((x,y))[:3], (153,153,153))
            self.assertTrue(all(after.getpixel(pos)[3] for pos in ((x-1,y),(x+1,y),(x,y-1),(x,y+1))))

    def test_nose_surface_reaches_outline_but_reflection_stays_on_visible_nose(self):
        p = pose()
        p.update(head_scale=1, nose=[[16,20],[19,20],[18,22],[16,21]], mouth=[],
                 nose_surface={"color":"dark","reflection":{"at":[17,21],"color":"white"}})
        im = standing64.render(p)
        self.assertEqual(im.getpixel((16,20))[:3], (51,51,51))
        self.assertEqual(im.getpixel((17,21))[:3], (255,255,255))
        p["nose_surface"]["reflection"]["at"] = [20,20]
        self.assertEqual(standing64.render(p).getpixel((20,20))[:3], (153,153,153))

    def test_cli_draws_from_bound_profile_without_reference_pixels(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            observed = json.loads((ROOT/"example.json").read_text(encoding="utf-8"))
            db = work/"profiles.sqlite"
            store = maker.Store(db)
            try:
                store.save(observed, 0, "fixture")
            finally:
                store.close()
            profile = {
                "format": "standing64-v1", "dog_id": observed["dog_id"], "source_revision": 1,
                "source_sha256": maker.digest(maker.canonical(observed).encode()),
                "head_scale": 1, "head_anchor": [20, 20],
                "palette": {"outline":"#221122","dark":"#333333","grey":"#999999","light":"#dddddd","white":"#ffffff"},
                "parts": [{"name":"head","fill":"grey","shape":[[10,10],[30,10],[30,30],[10,30]],"markings":[]}],
                "seams": [], "eyes": [{"center":[16,16],"offset":[0,0],"rows":["iw"]}],
                "nose": [[18,22],[20,22],[19,24]], "mouth": [[18,25],[20,25]], "shadows": []
            }
            def render(out):
                spec = work/"pose.json"
                spec.write_text(json.dumps(profile), encoding="utf-8")
                return subprocess.run([sys.executable, str(ROOT/"render_v03.py"), "--db", str(db),
                                       "render-standing", observed["dog_id"], "--profile", str(spec),
                                       "--out", str(work/out),"--stages"], capture_output=True)
            result = render("one")
            self.assertEqual(result.returncode, 0, result.stderr)
            for stage in ("S1","S2","shade","S3","ownership"):
                self.assertTrue((work/"one"/(stage+".png")).is_file())
            self.assertEqual((work/"one/S3.png").read_bytes(),(work/"one/standing.png").read_bytes())
            with Image.open(work/"one/standing.png") as image:
                self.assertEqual(image.size,(64,64))
                self.assertEqual(image.getpixel((0,0)),(0,0,0,0))
                self.assertEqual(image.getpixel((16,16)),(34,17,34,255))
                self.assertEqual(image.getpixel((17,16)),(255,255,255,255))
            self.assertNotEqual(render("one").returncode, 0)
            profile["parts"][0]["fur_gaps"] = [[14, 16]]
            self.assertEqual(render("gap").returncode, 0)
            with Image.open(work/"gap/standing.png") as image:
                self.assertEqual(image.getpixel((14,16)), (0,0,0,0))
                self.assertEqual(image.getpixel((15,16)), (153,153,153,255))
            profile["source_sha256"] = "0"*64
            self.assertNotEqual(render("invalid").returncode, 0)
            self.assertFalse((work/"invalid").exists())

