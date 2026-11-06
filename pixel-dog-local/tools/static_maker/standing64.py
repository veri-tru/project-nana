"""Native 64px standing renderer. Input coordinates belong to an authored pose profile."""
import json
import math
import re
import tempfile
import time
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageChops, __version__ as PIL_VERSION
import maker
from standing_parts import SEATED_LIMBS, body_shape, point, seated_limb_mask

VERSION = "standing64-v1"
V2 = "standing64-v2"
DEFAULT_HEAD_SCALE = 1.55
SIZE = (64, 64)
ROLES = ("outline", "dark", "grey", "light", "white")
COAT_SHADE = {"white": "light", "grey": "dark"}


def coat_region_mask(runs):
    """One 4-connected shape in the final 64px pose. Runs are [y, left, right], inclusive."""
    if not isinstance(runs, list) or not runs:
        raise ValueError("a coat region needs native pixel runs")
    mask = Image.new("L", SIZE)
    pen = ImageDraw.Draw(mask)
    for run in runs:
        if not isinstance(run, list) or len(run) != 3 or any(type(n) is not int for n in run):
            raise ValueError("expected integer coat run [y, left, right]")
        y, left, right = run
        if not (0 <= y < SIZE[1] and 0 <= left <= right < SIZE[0]):
            raise ValueError("coat run outside native grid")
        pen.line((left, y, right, y), fill=255)
    probe = mask.copy()
    ImageDraw.floodfill(probe, (left, y), 0)
    if probe.getbbox():
        raise ValueError("each coat region must be 4-connected")
    return mask


def scaled_coat(part, local, target_mask, anchor, scale):
    """Sample a filled coat field, so scaling rows cannot leave unpainted stripes."""
    source_mask = Image.new("1", SIZE)
    ImageDraw.Draw(source_mask).polygon([tuple(p) for p in part["shape"]], fill=1)
    source_pixels = [(x, y) for y in range(64) for x in range(64) if source_mask.getpixel((x, y))]
    if not source_pixels:
        raise ValueError("scaled coat requires a source shape inside the canvas")
    result = Image.new("RGB", SIZE)
    ax, ay = anchor
    for y in range(64):
        for x in range(64):
            if not target_mask.getpixel((x, y)):
                continue
            sx, sy = ax + (x-ax)/scale, ay + (y-ay)/scale
            pos = (round(sx), round(sy))
            if not (0 <= pos[0] < 64 and 0 <= pos[1] < 64 and source_mask.getpixel(pos)):
                pos = min(source_pixels, key=lambda pt: (pt[0]-sx)**2 + (pt[1]-sy)**2)
            result.putpixel((x, y), local.getpixel(pos))
    return result


def head_scale(profile):
    if profile["format"] == VERSION or "head_scale" in profile:
        return profile["head_scale"]
    # New photo-coordinate profiles: enlarge within the space available at
    # this neck anchor. Never shrink existing geometry just to add a margin.
    ax, ay = profile["head_anchor"]
    group = profile.get("head_parts", ["head"])
    scale = DEFAULT_HEAD_SCALE
    for part in profile["parts"]:
        if part["name"] in group:
            for x, y in part["shape"]:
                for position, anchor, size in ((x, ax, SIZE[0]), (y, ay, SIZE[1])):
                    offset = position - anchor
                    if offset > 0:
                        scale = min(scale, (size-2-anchor)/offset)
                    elif offset < 0:
                        scale = min(scale, (1-anchor)/offset)
    return max(1.0, scale)


def render(profile, *, stages=None):
    version = profile["format"]
    limb_masks = {}
    if version not in (VERSION, V2):
        raise ValueError("unsupported standing profile format")
    if any("component" in part for part in profile["parts"]):
        if version != V2:
            raise ValueError("generated body components require standing64-v2")
        parts = []
        for part in profile["parts"]:
            if "component" in part:
                if "shape" in part or part["name"] in profile.get("head_parts", ["head"]):
                    raise ValueError("generated body components replace body shapes only")
                component = part["component"]
                if component in SEATED_LIMBS:
                    limb_masks[part["name"]] = seated_limb_mask(component, profile)
                else:
                    part = {**part, "shape":body_shape(component,profile)}
            parts.append(part)
        profile = {**profile, "parts":parts}
    palette = profile["palette"]
    if set(palette) != set(ROLES) or not all(isinstance(c, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", c) for c in palette.values()):
        raise ValueError("expected five #RRGGBB palette roles")
    ax, ay = profile["head_anchor"]
    head_parts = profile.get("head_parts", ["head"]) if version == V2 else ["head"]
    names = [part["name"] for part in profile["parts"]]
    if (not isinstance(head_parts, list) or "head" not in head_parts
            or any(name not in names for name in head_parts)):
        raise ValueError("head_parts must name the head and any attached parts")
    scale = head_scale(profile)
    if type(scale) not in (float, int) or not math.isfinite(scale) or scale <= 0:
        raise ValueError("head_scale must be a positive finite number")

    lighting = profile.get("coat_lighting")
    if lighting is not None:
        if (version != V2 or not isinstance(lighting, dict) or
                lighting.get("direction") not in ("upper-left", "upper-right") or
                not isinstance(lighting.get("regions"), list) or profile.get("shadows")):
            raise ValueError("coat_lighting requires v2, one upper light direction and native regions")
        base_roles = set(profile.get("face_planes", {}))
        for part in profile["parts"]:
            base_roles.add(part["fill"])
            base_roles.update(m["color"] for m in part["markings"])
        if not base_roles <= COAT_SHADE.keys() or len(set(c.lower() for c in palette.values())) != 5:
            raise ValueError("use two base coat roles and distinct dedicated shade inks")
        if any(d["part"] != "head" or d.get("feature") not in ("left_eye", "right_eye", "nose", "mouth")
               for d in profile.get("details", [])):
            raise ValueError("use markings and lighting regions for coat details")

    def points(name, coords):
        if name in head_parts:
            return [(round(ax + (x-ax)*scale), round(ay + (y-ay)*scale)) for x, y in coords]
        return [tuple(pos) for pos in coords]

    # Indexed part ownership handles overlaps before markings and shade are painted.
    parts = profile["parts"]
    if "head" not in names or len(set(names)) != len(names) or len(parts) > 255:
        raise ValueError("expected unique named pose parts including head")
    protect_outline = (version == V2 and profile.get("preserve_outline") is True
                       or "head_view" in profile or any("component" in part for part in parts))
    owner = Image.new("L", SIZE)
    for index, part in enumerate(parts, 1):
        cutouts = part.get("native_cutouts", [])
        if cutouts and (version != V2 or profile.get("face_coordinates") != "native"):
            raise ValueError("native cutouts require a native-grid v2 profile")
        surface = Image.new("L", SIZE) if cutouts else owner
        pen = ImageDraw.Draw(surface)
        if part["name"] in limb_masks:
            surface.paste(index, mask=limb_masks[part["name"]])
        else:
            pen.polygon(points(part["name"], part["shape"]), fill=index)
        if version == V2 and part["name"] == "head":
            for polygon in profile.get("native_face_contours", []):
                pen.polygon([tuple(p) for p in polygon], fill=index)
        if cutouts:
            pen.point([tuple(p) for p in cutouts], fill=0)
            owner.paste(index, mask=surface.point(lambda v: 255 if v else 0))
    masks = {name: owner.point(lambda value: 255 if value == index else 0)
             for index, name in enumerate(names, 1)}
    alpha = owner.point(lambda value: 255 if value else 0)
    if alpha.getbbox() is None:
        raise ValueError("empty silhouette")

    def region_points(part, region, source=False):
        if "uv" not in region:
            return ([tuple(p) for p in region["polygon"]] if source
                    else points(part["name"],region["polygon"]))
        if "component" not in part or "polygon" in region:
            raise ValueError("uv regions require a generated body part")
        if part["name"] in limb_masks:
            left,top,right,bottom = limb_masks[part["name"]].getbbox()
            xs,ys = (left,right-1),(top,bottom-1)
        else:
            xs,ys = zip(*part["shape"])
        lo,hi = min(xs),max(xs)
        front,back = (hi,lo) if profile["stance"]["facing"]==1 else (lo,hi)
        polygon = []
        for vertex in region["uv"]:
            u,v = point(vertex,"uv")
            if not (0<=u<=1 and 0<=v<=1):
                raise ValueError("uv regions must use the unit square")
            polygon.append((round(front+u*(back-front)),round(min(ys)+v*(max(ys)-min(ys)))))
        return polygon

    flat = Image.new("RGB", SIZE)
    for part in parts:
        name = part["name"]
        local = Image.new("RGB", SIZE, palette[part["fill"]])
        sample_coat = version == V2 and name in head_parts and scale != 1
        for region in part["markings"]:
            polygon = region_points(part,region,sample_coat)
            ImageDraw.Draw(local).polygon(polygon, fill=palette[region["color"]])
        if sample_coat:
            local = scaled_coat(part, local, masks[name], (ax, ay), scale)
        flat.paste(local, mask=masks[name])

    for seam in profile["seams"]:
        name = seam["part"]
        surface = flat.copy() if version == V2 else flat
        ImageDraw.Draw(surface).line(points(name, seam["line"]), fill=palette["outline"])
        if version == V2:
            flat.paste(surface, mask=masks[name])
    for part in parts:
        for under in part.get("seam_over",[]):
            if version != V2 or under not in names or names.index(under)>=names.index(part["name"]):
                raise ValueError("seam_over must reference a part behind the current part")
            other=parts[names.index(under)]
            full = limb_masks.get(under)
            if full is None:
                full=Image.new("L",SIZE)
                ImageDraw.Draw(full).polygon(points(under,other["shape"]),fill=255)
            contact=ImageChops.multiply(masks[part["name"]],full)
            contact=ImageChops.multiply(contact,masks[under].filter(ImageFilter.MaxFilter(3)))
            flat.paste(ImageColor.getrgb(palette["outline"]),mask=contact)
    view = profile.get("head_view")
    face_mask = masks["head"]
    hidden_eye = None
    if view is not None:
        if version != V2 or view["angle"] not in ("front","oblique","profile"):
            raise ValueError("head_view requires v2 and a front, oblique or profile angle")
        near = view.get("near_eye")
        if view["angle"] != "front" and near not in ("left","right"):
            raise ValueError("turned views require the near eye's anatomical side")
        if "far_visible" in view and type(view["far_visible"]) is not bool:
            raise ValueError("far_visible must be boolean")
        if view["angle"] == "profile" and view.get("far_visible"):
            raise ValueError("a profile view cannot expose the far eye")
        if view["angle"] == "profile" or (view["angle"] == "oblique" and not view["far_visible"]):
            hidden_eye = "right" if near == "left" else "left"
        face_mask = face_mask.copy()
        for cover in view.get("foreground", []):
            ImageDraw.Draw(face_mask).polygon(points("head",cover),fill=0)
        for below in view.get("jaw_over", []):
            if below == "head" or below not in masks:
                raise ValueError("jaw_over requires another named visible part")
            # Mark only a head-to-underlying-part transition immediately below.
            neighbors = Image.new("L",SIZE)
            neighbors.paste(masks[below],(0,-1))
            flat.paste(ImageColor.getrgb(palette["outline"]),
                       mask=ImageChops.multiply(masks["head"],neighbors))
    face = flat.copy() if version == V2 else flat
    pen = ImageDraw.Draw(face)
    feature_ink = Image.new("L", SIZE) if lighting is not None else None
    feature_pen = ImageDraw.Draw(feature_ink) if feature_ink is not None else None
    # Photo landmarks are already projected onto the final grid. Pose contours
    # and the older authoring formats still use the original head-local space.
    native_face = version == V2 and profile.get("face_coordinates") == "native"
    def face_points(coords):
        return [tuple(pos) for pos in coords] if native_face else points("head", coords)
    if native_face:
        for role, pixels in profile.get("face_planes", {}).items():
            pen.point([tuple(pos) for pos in pixels], fill=palette[role])
    eye_inks = {"i":"outline","w":"white","l":"light","d":"dark"} if version==V2 else {"i":"outline","w":"white"}
    for eye in profile["eyes"]:
        if view is not None:
            if eye.get("side") not in ("left","right"):
                raise ValueError("head_view requires anatomical side on each eye")
            if eye["side"] == hidden_eye:
                continue
        cx, cy = face_points([eye["center"]])[0]
        dx, dy = eye["offset"]
        for row, pattern in enumerate(eye["rows"]):
            for col, symbol in enumerate(pattern):
                if symbol != ".":
                    role = eye_inks[symbol]
                    pen.point((cx+dx+col, cy+dy+row), fill=palette[role])
                    if feature_pen is not None:
                        feature_pen.point((cx+dx+col, cy+dy+row), fill=255)
    pen.polygon(face_points(profile["nose"]), fill=palette["outline"])
    if feature_pen is not None:
        feature_pen.polygon(face_points(profile["nose"]), fill=255)
    if version == VERSION or profile["mouth"]:
        pen.line(face_points(profile["mouth"]), fill=palette[profile.get("mouth_color","dark")])
        if feature_pen is not None:
            feature_pen.line(face_points(profile["mouth"]), fill=255)
    if native_face and profile["mouth"] and profile.get("mouth_contact"):
        contact = profile["mouth_contact"]
        pen.point([tuple(p) for p in contact["pixels"]], fill=palette[contact["color"]])
        if feature_pen is not None:
            feature_pen.point([tuple(p) for p in contact["pixels"]], fill=255)
    if version == V2:
        flat.paste(face, mask=face_mask)
        if feature_ink is not None:
            feature_ink = ImageChops.multiply(feature_ink, face_mask)
    if protect_outline:
        padded = Image.new("L",(66,66))
        padded.paste(alpha,(1,1))
        interior = padded.filter(ImageFilter.MinFilter(3)).crop((1,1,65,65))
    else:
        interior = alpha.filter(ImageFilter.MinFilter(3))
    border = ImageChops.subtract(alpha, interior)
    if version == V2:
        # Narrow diagonal legs retain coat color at corner-only contacts.
        slim = Image.new("L", SIZE)
        for part in parts:
            neighbors = part.get("outline_neighbors", 8)
            if neighbors not in (4, 8):
                raise ValueError("outline_neighbors must be 4 or 8")
            if neighbors == 4:
                slim.paste(255, mask=masks[part["name"]])
        for y in range(1, 63):
            for x in range(1, 63):
                if slim.getpixel((x,y)) and all(alpha.getpixel(p) for p in
                        ((x-1,y),(x+1,y),(x,y-1),(x,y+1))):
                    border.putpixel((x,y), 0)
    flat.paste(ImageColor.getrgb(palette["outline"]), mask=border)

    def feature_mask(layer):
        name=layer["part"]
        if view is None or name!="head":
            return masks[name]
        feature=layer.get("feature")
        if feature not in ("coat","nose","mouth","left_eye","right_eye"):
            raise ValueError("tag head details and shadows when using head_view")
        if hidden_eye and feature==hidden_eye+"_eye":
            return None
        return masks[name] if feature=="coat" else face_mask

    shaded = flat.copy()
    if lighting is not None:
        materials = {}
        for base, shade in COAT_SHADE.items():
            rgb = ImageColor.getrgb(palette[base])
            mask = Image.new("L", SIZE)
            mask.putdata([255 if flat.getpixel((x, y)) == rgb else 0
                          for y in range(SIZE[1]) for x in range(SIZE[0])])
            materials[base] = mask
        for region in lighting["regions"]:
            part, base = region["part"], region["base"]
            if part not in masks or base not in COAT_SHADE:
                raise ValueError("unknown coat region part or base")
            mask = ImageChops.multiply(coat_region_mask(region["runs"]), masks[part])
            mask = ImageChops.multiply(mask, materials[base])
            if part == "head":
                mask = ImageChops.subtract(mask, feature_ink)
            shaded.paste(ImageColor.getrgb(palette[COAT_SHADE[base]]), mask=mask)
    for shade in profile.get("shadows", []):
        name = shade["part"]
        area = Image.new("1", SIZE)
        shade_mask=feature_mask(shade)
        if shade_mask is None:
            continue
        ImageDraw.Draw(area).polygon(region_points(parts[names.index(name)],shade), fill=1)
        source = ImageColor.getrgb(palette[shade["from"]])
        target = ImageColor.getrgb(palette[shade["to"]])
        bounds = area.getbbox()
        if bounds is None:
            continue
        left, top, right, bottom = bounds
        for y in range(top, bottom):
            for x in range(left, right):
                pos = (x, y)
                if area.getpixel(pos) and shade_mask.getpixel(pos) and flat.getpixel(pos) == source:
                    shaded.putpixel(pos, target)
    if protect_outline:
        shaded.paste(ImageColor.getrgb(palette["outline"]), mask=border)
    if stages is not None:
        shadow_only = shaded.copy()
    if version == V2:
        surface = profile.get("nose_surface")
        if surface is not None:
            nose_mask = Image.new("L", SIZE)
            ImageDraw.Draw(nose_mask).polygon(face_points(profile["nose"]), fill=255)
            nose_mask = ImageChops.multiply(nose_mask, face_mask)
            shaded.paste(ImageColor.getrgb(palette[surface["color"]]), mask=nose_mask)
            if "reflection" in surface:
                accent = surface["reflection"]
                (x, y), = face_points([accent["at"]])
                if 0 <= x < 64 and 0 <= y < 64 and nose_mask.getpixel((x, y)):
                    shaded.putpixel((x, y), ImageColor.getrgb(palette[accent["color"]]))
        # Final palette accents (e.g. a closed lip, glint or overlap) belong
        # only to the visible part. Later details win without growing its alpha.
        for detail in profile.get("details", []):
            name = detail["part"]
            detail_mask = feature_mask(detail)
            if detail_mask is None:
                continue
            polygon = points(name, detail["polygon"])
            if not polygon:
                raise ValueError("empty detail polygon")
            area = Image.new("L", SIZE)
            draw = ImageDraw.Draw(area)
            if len(polygon) == 1:
                draw.point(polygon[0], fill=255)
            elif len(polygon) == 2:
                draw.line(polygon, fill=255)
            else:
                draw.polygon(polygon, fill=255)
            shaded.paste(ImageColor.getrgb(palette[detail["color"]]),
                         mask=ImageChops.multiply(area, detail_mask))
        if protect_outline:
            shaded.paste(ImageColor.getrgb(palette["outline"]), mask=border)
    # A few gaps between overlapping strands reveal the ground without a
    # second heavy outline. Clip them to the visible part that owns the fur.
    for part in parts:
        name = part["name"]
        for pos in points(name, part.get("fur_gaps", [])):
            if 0 <= pos[0] < SIZE[0] and 0 <= pos[1] < SIZE[1] and masks[name].getpixel(pos):
                alpha.putpixel(pos, 0)
    result = Image.new("RGBA", SIZE)
    result.paste(shaded, mask=alpha)
    if stages is not None:
        for name, surface in (("S1", ImageColor.getrgb(palette["outline"])),
                              ("S2", flat), ("shade", shadow_only)):
            stage = Image.new("RGBA", SIZE)
            stage.paste(surface, (0,0,64,64), mask=alpha)
            stages[name] = stage
        stages["S3"] = result
        stages["ownership"] = ImageChops.multiply(owner, alpha)
    return result


def baseline_catalog():
    path = Path(__file__).with_name("standing-baselines.json")
    return json.loads(path.read_text(encoding="utf-8"))


def baseline_for_pose(dog, pose=None):
    entry = baseline_catalog().get(dog)
    if pose is not None and not re.fullmatch(r"[a-zA-Z0-9_-]+", pose):
        raise ValueError("invalid registered pose name")
    if entry is not None and (pose is None or pose == entry.get("pose")):
        return entry
    if entry is not None and pose in entry.get("poses", {}):
        alt = entry["poses"][pose]
        if alt["pose"] == pose:
            return alt
    raise ValueError(f"no working standing baseline for dog {dog!r}, pose {pose!r}")


def baseline_database(dog):
    entry = baseline_catalog().get(dog)
    if entry is None:
        raise ValueError("no working standing baseline registered for this dog; specify --db and --profile")
    path = Path(__file__).parent / entry["database"]
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def export_roster(destination):
    """Publish the complete roster only after every registered pixel hash matches."""
    out = Path(destination)
    if out.exists():
        raise FileExistsError(out)
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out.parent) as work:
        pending = Path(work)/"roster"
        pending.mkdir()
        manifest = {}
        for dog, entry in baseline_catalog().items():
            store = maker.Store(baseline_database(dog),read_only=True)
            try:
                export(store,dog,None,pending/dog)
                for pose in entry.get("poses", {}):
                    export(store,dog,None,pending/dog/pose,pose=pose)
            finally:
                store.close()
            manifest[dog] = {key:entry[key] for key in ("status","pose","rgba_sha256")}
            if entry.get("poses"):
                manifest[dog]["poses"] = {
                    key: {field: alt[field] for field in ("status","pose","rgba_sha256")}
                    for key,alt in entry["poses"].items()
                }
        (pending/"index.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
        pending.rename(out)


def export(store, dog, profile_file, destination, *, include_stages=False, pose=None):
    baseline = None
    if profile_file is None:
        baseline = baseline_for_pose(dog, pose)
        profile_file = Path(__file__).parent / baseline["profile"]
    elif pose is not None:
        raise ValueError("select a registered pose or an explicit profile")
    profile = json.loads(Path(profile_file).read_text(encoding="utf-8"))
    authoring_hash = maker.digest(maker.canonical(profile).encode())
    if baseline is not None and authoring_hash != baseline["authoring_sha256"]:
        raise ValueError("working baseline profile differs from the registered revision")
    if profile["dog_id"] != dog or type(profile["source_revision"]) is not int or profile["source_revision"] < 1:
        raise ValueError("standing profile dog or source revision mismatch")
    source, revision = store.get(dog, profile["source_revision"])
    source_hash = maker.digest(maker.canonical(source).encode())
    if source_hash != profile["source_sha256"]:
        raise ValueError("observation revision hash mismatch")
    stages = {} if include_stages else None
    image = render(profile, stages=stages)
    rgba_hash = maker.digest(image.tobytes())
    if baseline is not None and rgba_hash != baseline["rgba_sha256"]:
        raise ValueError("rendered pixels differ from the registered working baseline")
    out = Path(destination)
    if out.exists():
        raise FileExistsError(str(out))
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out.parent) as work:
        pending = Path(work)/"export"
        pending.mkdir()
        image.save(pending/"standing.png")
        report = {"renderer":profile["format"], "dog_id":dog, "source_revision":revision, "source_sha256":source_hash,
                  "authoring_sha256":authoring_hash, "pillow":PIL_VERSION,
                  "rgba_sha256":rgba_hash,
                  "png_sha256":maker.digest((pending/"standing.png").read_bytes())}
        if baseline is not None:
            report["working_baseline"] = baseline["profile"]
            if "status" in baseline:
                report.update(status=baseline["status"],pose=baseline["pose"])
        if profile["format"] == V2:
            report["applied_head_scale"] = head_scale(profile)
        if profile.get("coat_lighting") is not None:
            lighting = profile["coat_lighting"]
            report["coat_lighting"] = {"direction":lighting["direction"], "shade_pairs":COAT_SHADE,
                                       "connected_regions":len(lighting["regions"])}
        if stages is not None:
            report["stages"] = {}
            for name, stage in stages.items():
                file = pending/(name+".png")
                stage.save(file)
                report["stages"][name] = maker.digest(file.read_bytes())
            report["owner_ids"] = {p["name"]: i for i,p in enumerate(profile["parts"],1)}
            if profile.get("head_view") is not None:
                # Measure the eye's actual contribution after ink, clipping, shadows and outlines.
                contributions = {}
                for eye in profile["eyes"]:
                    side = eye["side"]
                    without = {**profile, "eyes":[other for other in profile["eyes"] if other["side"] != side]}
                    for field in ("shadows","details"):
                        without[field] = [layer for layer in profile.get(field,[])
                                          if layer.get("feature") != side+"_eye"]
                    probe = render(without)
                    contributions[side] = sum(a != b for a,b in zip(image.getdata(),probe.getdata()))
                report["eye_contribution_px"] = contributions
        (pending/"review.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

        # Windows can briefly lock a just-written PNG directory before publish.
        for delay in (0.05, 0.1, 0.2, None):
            try:
                pending.rename(out)
                break
            except PermissionError as error:
                if delay is None or getattr(error, "winerror", None) not in (5, 32) or out.exists():
                    raise
                time.sleep(delay)
