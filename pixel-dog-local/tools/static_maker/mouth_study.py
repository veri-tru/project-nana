"""Render a photo-registered mouth opening from a verified native head pose."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import maker
import standing64
from photo_pose import check_visible_features


def open_jaw(parent, recipe, amount):
    if parent["dog_id"] != recipe["dog_id"] or maker.digest(maker.canonical(parent).encode()) != recipe["parent_sha256"]:
        raise ValueError("mouth registration belongs to a different parent")
    p = deepcopy(parent)
    scale = standing64.head_scale(p)
    ax, ay = p["head_anchor"]

    def vertices(name):
        return [[ax+(x-ax)/scale, ay+(y-ay)/scale] for x,y in recipe[name]]

    if recipe["oral_cavity"][0] != recipe["corner"] or recipe["lower_jaw"][0] != recipe["corner"]:
        raise ValueError("both surfaces must start at the same fixed lip corner")
    x,y = recipe["notch_start"]
    dx,dy = recipe["toward_corner"]
    if amount < 1 or abs(dx)+abs(dy) != 1:
        raise ValueError("a mouth opening requires a positive depth and a cardinal direction")
    # Expose background from the free lip edge inward, keeping the lower jaw
    # supported at the cheek. Apply the cut per layer to respect occlusion.
    gap = [recipe["front_rim"]] + [[x+i*dx,y+i*dy] for i in range(amount)]
    head = next(part for part in p["parts"] if part["name"]=="head")
    head.setdefault("native_cutouts", []).extend(gap)
    p["mouth"] = []
    p.pop("mouth_contact", None)
    for name,fill in (("oral_cavity","dark"), ("lower_jaw","light")):
        p["parts"].append(dict(name=name,shape=vertices(name),fill=fill,markings=[],
                               outline_neighbors=4,native_cutouts=gap))
        p["head_parts"].append(name)
    p["details"].append(dict(part="lower_jaw",color="dark",polygon=vertices("lip_shadow")))
    p["details"].append(dict(part="oral_cavity",color="grey",polygon=vertices("tongue")))
    return p


def build(profile, database, recipe, destination):
    parent = json.loads(profile.read_text(encoding="utf-8"))
    registration = json.loads(recipe.read_text(encoding="utf-8"))
    if destination.exists():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=destination.parent) as temp:
        pending = Path(temp)/"study"
        pending.mkdir()

        def export(pair):
            label, gap = pair
            candidate = open_jaw(parent,registration,gap)
            check_visible_features(candidate)
            spec = pending/(label+".json")
            spec.write_text(json.dumps(candidate,ensure_ascii=False),encoding="utf-8")
            reader = maker.Store(database,read_only=True)
            try:
                standing64.export(reader,candidate["dog_id"],spec,pending/label)
            finally:
                reader.close()

        with ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(export,zip("ABC",registration["opening_steps"],strict=True)))
        pending.rename(destination)


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for arg in ("profile", "database", "destination"):
        parser.add_argument(arg,type=Path)
    parser.add_argument("--recipe",type=Path,default=Path(__file__).with_name("guide_registration")/"open-mouth.json")
    args=parser.parse_args()
    build(args.profile,args.database,args.recipe,args.destination)
