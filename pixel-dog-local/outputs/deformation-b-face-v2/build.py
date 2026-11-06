"""Revise the three heads in the compact B standing preset, in authored face-grid units."""
import json
import runpy
from math import dist, isclose
from pathlib import Path

OUT = Path(__file__).resolve().parent
RIG = runpy.run_path(str(OUT.parent / "integrated-rig-b-v1/build.py"))

# x = anatomical left, y = down, z = forward. The midpoint of the ear flap
# describes its fold; the renderer derives the surface around that chain.
MIDLINE = {
    "whippet": dict(crown=(0, 8, -4), occiput=(0, 13, -13), stop=(0, 17, 9),
                    nose=(0, 22, 30), nose_bottom=(0, 25.5, 30), upper_lip=(0, 27, 28),
                    chin=(0, 31, 26)),
    "dachshund": dict(crown=(0, 7, -4), occiput=(0, 12, -14), stop=(0, 17, 8),
                      nose=(0, 22, 32), nose_bottom=(0, 26, 32), upper_lip=(0, 28.5, 30.5),
                      chin=(0, 32, 28)),
    "golden": dict(crown=(0, 6.5, -5), occiput=(0, 11, -16), stop=(0, 18, 7),
                   nose=(0, 19.5, 29), nose_bottom=(0, 25, 29.5), upper_lip=(0, 30, 27),
                   chin=(0, 34.5, 25)),
}
PAIRED = {
    "whippet": dict(brow=(8.2, 12, 4.7), cheek=(10.8, 25, 1.5), muzzle_side=(6.3, 25, 19),
                    jaw_side=(5.5, 29.5, 17), nose_wing=(4, 23, 29), mouth_corner=(8.1, 27.5, 8)),
    "dachshund": dict(brow=(9.6, 12.7, 4.1), cheek=(12.7, 26.5, 2), muzzle_side=(7.8, 25.5, 20),
                      jaw_side=(7, 31, 18.5), nose_wing=(4.9, 23.5, 31), mouth_corner=(9.4, 28.7, 8),
                      ear_root=(12, 16, -4), ear_fold=(16, 24, -10), ear_tip=(14, 39, -8)),
    "golden": dict(brow=(12, 12.5, 4.3), temple=(18, 14.5, -4), cheek=(16.7, 27.3, 1.3),
                   muzzle_side=(12.2, 26.2, 17.5), jaw_side=(10.7, 33, 16.5),
                   nose_wing=(7.7, 21.2, 28.2), mouth_corner=(12.7, 29, .5),
                   jaw_hinge=(14.5, 25, -8), ear_root=(15.4, 16.8, -11.5),
                   ear_fold=(18.7, 22, -13.8), ear_tip=(16.5, 33, -6.8)),
}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def revised_head(rig, breed, original, scale):
    anchors = dict(original["anchors"], **MIDLINE[breed])
    for side, sign in (("L_", 1), ("R_", -1)):
        for part, (x, y, z) in PAIRED[breed].items():
            anchors[side + part] = (sign * x, y, z)
        # Move lids, corners and pupil together around their own eye.
        eye_shift = {"whippet": (.2, -.7, 1), "dachshund": (.4, -1.4, 1), "golden": (.6, -1.7, -5.9)}[breed]
        for part in ("eye", "eye_inner", "eye_outer", "upper_lid", "lower_lid", "pupil"):
            x, y, z = anchors[side + part]
            dx, dy, dz = eye_shift
            anchors[side + part] = (x + sign * dx, y + dy, z + dz)
    anchors["jaw_axis"] = tuple((a+b)/2 for a, b in zip(anchors["L_jaw_hinge"], anchors["R_jaw_hinge"]))
    mount = anchors["neck_mount"]
    neutral = RIG["world_pose"](rig)
    hx, hy, hz = neutral["body.head"]
    for name, (x, y, z) in anchors.items():
        neutral["face." + name] = hx-(z-mount[2])*scale, hy-(y-mount[1])*scale, hz+(x-mount[0])*scale
    for name in anchors:
        key = "face." + name
        node = rig["nodes"][key]
        node["offset"] = RIG["delta"](neutral[key], neutral[node["parent"]])
    RIG["verify"](rig)
    if breed == "golden":
        assert isclose((anchors["nose"][2]-anchors["stop"][2]) /
                       (anchors["stop"][2]-anchors["occiput"][2]), 22/23)
    for angles in ({}, {"face.jaw_axis": 12}, {"body.head": -15, "face.L_ear_root": 8}):
        posed = RIG["world_pose"](rig, angles)
        assert dist(posed["body.head"], posed["face.neck_mount"]) < 1e-7


def main():
    model = load(OUT.parent / "deformation-rig-b-v1/B.json")
    faces = load(OUT.parent / "face-rig-breeds-v1/rigs.json")
    for breed, rig in model["breeds"].items():
        revised_head(rig, breed, faces[breed], model["face_scale"])
    model["version"] = "deformation-b-face-v2"
    (OUT / "B.json").write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
