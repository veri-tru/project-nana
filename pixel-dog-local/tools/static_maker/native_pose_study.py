"""Compare three leg overlaps on a standing pose authored on the native grid."""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

import maker
import standing64
from photo_pose import check_visible_features


def native_pose(recipe, observation, revision, offset):
    parts = deepcopy(recipe["parts"])
    upper = recipe["fixed_above"]
    lower = recipe["full_offset_below"]
    if lower <= upper:
        raise ValueError("the distal station must be below the hip or shoulder")

    for part in parts:
        if part["name"] in recipe["far_legs"]:
            polygons = [part["shape"]] + [m["polygon"] for m in part["markings"]]
            for polygon in polygons:
                for point in polygon:
                    weight = min(1, max(0, (point[1] - upper) / (lower - upper)))
                    point[0] += round(weight * offset)

    fields = ("head_anchor", "head_parts", "seams", "eyes", "nose", "nose_surface", "palette")
    return {
        **{name: deepcopy(recipe[name]) for name in fields},
        "parts": parts,
        "format": standing64.V2,
        "head_scale": 1,
        "face_coordinates": "native",
        "dog_id": observation["dog_id"],
        "source_revision": revision,
        "source_sha256": maker.digest(maker.canonical(observation).encode()),
        "mouth": [],
        "preserve_outline": True,
        "shadows": [],
    }


def build(database, registration, destination):
    recipe = json.loads(registration.read_text(encoding="utf-8"))
    source = maker.Store(database, read_only=True)
    try:
        observation, revision = source.get(recipe["dog_id"], recipe["source_revision"])
    finally:
        source.close()
    if destination.exists():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=destination.parent) as temp:
        pending = Path(temp) / "study"
        pending.mkdir()

        def export(label, offset):
            profile = native_pose(recipe, observation, revision, offset)
            check_visible_features(profile)
            spec = pending / f"{label}.json"
            spec.write_text(json.dumps(profile, ensure_ascii=False), encoding="utf-8")
            reader = maker.Store(database, read_only=True)
            try:
                standing64.export(reader, profile["dog_id"], spec, pending / label)
            finally:
                reader.close()

        with ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(export, "ABC", range(3)))
        pending.rename(destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("database", "registration", "destination"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    build(args.database, args.registration, args.destination)
