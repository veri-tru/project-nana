"""Compare three head scales using the same manually registered full-body contours."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image

import maker
from photo_pose import check_visible_features, compile_pose
import standing64


def refine_registered_features(profile, recipe, level):
    """Apply a photo-traced study only on its verified native-grid parent."""
    if maker.digest(maker.canonical(profile).encode()) != recipe["parent_sha256"]:
        raise ValueError("facial detail registration belongs to a different base")
    pixels = {tuple(xy):role for role,group in profile["face_planes"].items() for xy in group}
    for step in recipe["coat_steps"][:level]:
        for role, group in step.items():
            pixels.update({tuple(xy):role for xy in group})
    planes = {}
    for xy, role in sorted(pixels.items()):
        planes.setdefault(role, []).append(list(xy))
    return {**profile, **recipe["features"], "face_planes":planes}


def register_ear(profile, recipe, level):
    """Lay the observed pinna over the cheek with a free edge and an open root."""
    if maker.digest(maker.canonical(profile).encode()) != recipe["parent_sha256"]:
        raise ValueError("ear registration belongs to a different base")
    part = recipe["part"]
    edge = recipe["free_edge"]
    tip = edge[:recipe["edge_stops"][level-1]]
    return {**profile,
            "parts":[*profile["parts"], part],
            "head_parts":[*profile.get("head_parts", ["head"]), part["name"]],
            "seams":[*profile["seams"],dict(part=part["name"],line=tip)]}


def build(source, destination, *, face_shading=False, face_details=False, ear_fold=False):
    registrations = json.loads(Path(__file__).with_name("guide_registration").joinpath(
        "body-pilot.json").read_text(encoding="utf-8"))
    details = {}
    ears = {}
    if face_details or ear_fold:
        details = json.loads(Path(__file__).with_name("guide_registration").joinpath(
            "face-detail.json").read_text(encoding="utf-8"))
        registrations = {key:registrations[key] for key in details}
    if ear_fold:
        ears = json.loads(Path(__file__).with_name("guide_registration").joinpath(
            "ear-fold.json").read_text(encoding="utf-8"))
        registrations = {key:registrations[key] for key in ears}
    if destination.exists():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    database = maker.Store(source / "profiles.sqlite", read_only=True)
    try:
        with TemporaryDirectory(dir=destination.parent) as work:
            root = Path(work) / "pilot"
            root.mkdir()
            for key, registration in registrations.items():
                dog = "guide-" + key
                observation, revision = database.get(dog)
                with Image.open(source / key / "source-image") as original:
                    photo = original.convert("RGB")
                folder = root / key
                folder.mkdir()

                def render_variant(pair):
                    label, value = pair
                    settings = (dict(head_scale=1.08, face_shade_reach=value) if face_shading
                                else dict(head_scale=value))
                    if face_details or ear_fold:
                        settings = dict(head_scale=1.08, face_shade_reach=5)
                    profile = compile_pose(photo.copy(), observation, revision,
                                           {**registration, **settings})
                    if face_details or ear_fold:
                        profile = refine_registered_features(profile, details[key], 2 if ear_fold else value)
                    if ear_fold:
                        profile = register_ear(profile, ears[key], value)
                    check_visible_features(profile)
                    spec = folder / (label + ".json")
                    spec.write_text(json.dumps(profile, ensure_ascii=False), encoding="utf-8")
                    reader = maker.Store(source / "profiles.sqlite", read_only=True)
                    try:
                        standing64.export(reader, dog, spec, folder / label)
                    finally:
                        reader.close()

                with ThreadPoolExecutor(max_workers=3) as pool:
                    values = (1, 2, 5) if face_shading else (1.0, 1.08, 1.16)
                    if face_details or ear_fold:
                        values = (1, 2, 3)
                    list(pool.map(render_variant, zip("ABC", values)))
            root.rename(destination)
    finally:
        database.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="guide registration export containing the photos and database")
    parser.add_argument("destination", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--face-shading", action="store_true",
                        help="hold the previous B geometry fixed and vary facial coat shading")
    mode.add_argument("--face-details", action="store_true",
                      help="compare facial details on the selected R4 C photo profiles")
    mode.add_argument("--ear-fold", action="store_true",
                      help="compare the free edge of the near ear on a registered face")
    args = parser.parse_args()
    build(args.source, args.destination, face_shading=args.face_shading, face_details=args.face_details, ear_fold=args.ear_fold)
