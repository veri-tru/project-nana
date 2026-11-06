"""Compare ranked coat planes on the same native-grid parent pose."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, ImageDraw

import maker
import standing64
from photo_pose import check_visible_features


def reduce_coat(parent, recipe, level):
    if maker.digest(maker.canonical(parent).encode()) != recipe["parent_sha256"]:
        raise ValueError("coat registration belongs to a different pose")
    profile = deepcopy(parent)
    for part in profile["parts"]:
        plan = recipe["parts"].get(part["name"])
        if plan is None:
            continue
        part["fill"] = plan["fill"]
        part["markings"] = [dict(color=p["color"], polygon=p["polygon"])
                            for p in plan["planes"] if level <= p["last"]]
        part["markings"].extend(recipe["required_planes"].get(part["name"], []))
    if recipe["clear_face_planes"]:
        profile["face_planes"] = {}
    profile["details"] = [d for d in profile["details"] if d["part"] not in recipe["omit_details_from"]]
    return profile


def verify_identity_pixels(parent, candidate, recipe):
    """Reject texture reductions that erase a protected identifying structure."""
    stages = {}
    before = standing64.render(parent, stages=stages)
    after = standing64.render(candidate)
    if before.getchannel("A").tobytes() != after.getchannel("A").tobytes():
        raise ValueError("coat simplification changed the silhouette or an opening")
    names = [p["name"] for p in parent["parts"]]
    fixed = {1+names.index(name) for name in recipe["fixed_pigment_parts"]}
    mask = stages["ownership"].point(lambda v:255 if v in fixed else 0)
    pen = ImageDraw.Draw(mask)
    pen.polygon([tuple(p) for p in parent["nose"]], fill=255)
    for eye in parent["eyes"]:
        x,y = eye["center"]
        dx,dy = eye["offset"]
        for row,pattern in enumerate(eye["rows"]):
            for col,ink in enumerate(pattern):
                if ink != ".":
                    pen.point((x+dx+col,y+dy+row), fill=255)
    if before.tobytes() != Image.composite(after,before,mask).tobytes():
        raise ValueError("coat simplification changed protected feature ink")


def build(parent_path, database, recipe_path, destination):
    parent = json.loads(parent_path.read_text(encoding="utf-8"))
    recipe = json.loads(recipe_path.read_text(encoding="utf-8"))
    if destination.exists():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=destination.parent) as temp:
        pending = Path(temp)/"study"
        pending.mkdir()

        def export(pair):
            label, level = pair
            profile = reduce_coat(parent, recipe, level)
            check_visible_features(profile)
            verify_identity_pixels(parent,profile,recipe)
            spec = pending/(label+".json")
            spec.write_text(json.dumps(profile,ensure_ascii=False),encoding="utf-8")
            reader = maker.Store(database,read_only=True)
            try:
                standing64.export(reader,profile["dog_id"],spec,pending/label)
            finally:
                reader.close()

        with ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(export, zip("ABC", (1,2,3))))
        pending.rename(destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("parent", "database", "recipe", "destination"):
        parser.add_argument(arg, type=Path)
    args = parser.parse_args()
    build(args.parent,args.database,args.recipe,args.destination)
