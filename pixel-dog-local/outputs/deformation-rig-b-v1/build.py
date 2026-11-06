"""Derive standing style rigs from the selected B hierarchy in its original units."""
import json
import runpy
from copy import deepcopy
from math import dist, isclose
from pathlib import Path

OUT = Path(__file__).resolve().parent
SOURCE = OUT.parent / "integrated-rig-b-v1"
base = runpy.run_path(str(SOURCE / "build.py"))
world_pose, verify = base["world_pose"], base["verify"]
STYLES = {
    "A": dict(head_scale=1.42, trunk_span=.98, lower_leg=.96, neck=.97, paw_scale=1.04),
    "B": dict(head_scale=1.70, trunk_span=.85, lower_leg=.82, neck=.85, paw_scale=1.22),
    "C": dict(head_scale=2.10, trunk_span=.75, lower_leg=.70, neck=.73, paw_scale=1.34),
}


def scale_between(point, old_anchor, anchor, scale):
    return tuple(b + (p - a) * s for p, a, b, s in zip(point, old_anchor, anchor, scale, strict=True))


def styled_rig(source, breed, style):
    rig = deepcopy(source)
    rest = world_pose(source)
    span, leg = style["trunk_span"], style["lower_leg"]
    elbow = rest["body.left_elbow"][1]
    sx = rest["body.left_shoulder"][0]
    # Raise or lower the trunk rigidly. Only the region below elbow level compresses vertically.
    pose = {k: (sx + (x - sx) * span, y - min(elbow, y) * (1 - leg), z)
            for k, (x, y, z) in rest.items()}
    for node, owner in [("body.neck", "body.ribcage"), ("body.head", "body.neck")]:
        pose[node] = scale_between(rest[node], rest[owner], pose[owner], (style["neck"],) * 3)
    for key in rest:
        if key.startswith("face."):
            pose[key] = scale_between(rest[key], rest["body.head"], pose["body.head"], (style["head_scale"],) * 3)
    # Change pad reach around each pad joint, keeping the toes on their contact plane.
    for side in ("left_", "right_"):
        for toe, joint in (("foretoe", "mcp"), ("hindtoe", "mtp")):
            key, owner = "body." + side + toe, "body." + side + joint
            x, _, z = scale_between(rest[key], rest[owner], pose[owner], (style["paw_scale"], 1, 1))
            pose[key] = x, pose[key][1], z

    tail = rig["tail_profile"]
    root = tail["chain"][0]
    scale = span
    if breed == "golden":
        scale = (pose[root][1] - pose["body.left_tarsus"][1]) / sum(tail["segment_lengths"])
    for key in tail["chain"][1:]:
        pose[key] = scale_between(rest[key], rest[root], pose[root], (scale,) * 3)
    for field in ("segment_lengths", "core_radius", "underside_feather"):
        tail[field] = [v * scale for v in tail[field]]
    tail["evidence"] = "../integrated-rig-b-v1/review.md#꼬리-후속-조사--2026-11-05"
    for node, entry in rig["nodes"].items():
        origin = pose[entry["parent"]] if entry["parent"] else (0, 0, 0)
        entry["offset"] = [round(a - b, 9) for a, b in zip(pose[node], origin)]
    for surface in rig["surfaces"].values():
        for field in ("offsets", "top_offsets"):
            surface[field] = [[x * span, y, z] for x, y, z in surface[field]]
    for key in ("pelvic_dorsum", "rear_brisket", "belly_guide"):
        rig[key]["offset"][0] *= span

    verify(rig)
    actual = world_pose(rig)
    assert all(actual[key][1] >= 0 for key in tail["chain"])
    assert min(actual[k][1] for k in actual if k.startswith("face.")) > 0
    for key in actual:
        if key.startswith("face."):
            assert isclose(dist(actual[key], actual["body.head"]), style["head_scale"] * dist(rest[key], rest["body.head"]), abs_tol=1e-7)
    if breed == "golden":
        assert isclose(sum(tail["segment_lengths"]), actual[root][1] - actual["body.left_tarsus"][1], abs_tol=1e-7)
    return rig


def main():
    source = json.loads((SOURCE / "rigs.json").read_text(encoding="utf-8"))
    for letter, style in STYLES.items():
        model = dict(source, version=f"deformation-rig-b-v1/{letter}", deformation=style,
                     units="original integrated B design units; pre-style shoulder-to-hip span = 30",
                     face_scale=source["face_scale"] * style["head_scale"],
                     breeds={b: styled_rig(r, b, style) for b, r in source["breeds"].items()})
        (OUT / f"{letter}.json").write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{letter}: verified {len(model['breeds'])} breed rigs")


if __name__ == "__main__":
    main()
