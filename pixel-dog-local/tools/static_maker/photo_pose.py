"""Compile a manually registered visible pose into standing64-v2 authoring data."""
from itertools import groupby
from PIL import Image, ImageColor, ImageDraw, ImageFilter
import maker
import standing64


def check_visible_features(profile):
    """Check the actual pigment of each visible structure on the final native grid."""
    image = standing64.render(profile)
    palette = profile["palette"]
    no_eyes = standing64.render({**profile, "eyes":[]})
    for eye in profile["eyes"]:
        dark_changes = 0
        cx,cy = eye["center"]
        dx,dy = eye["offset"]
        for row,pattern in enumerate(eye["rows"]):
            for col,symbol in enumerate(pattern):
                if symbol==".":
                    continue
                role={"i":"outline","d":"dark","l":"light"}[symbol]
                xy = (cx+dx+col,cy+dy+row)
                dark_changes += symbol in ("i","d") and image.getpixel(xy) != no_eyes.getpixel(xy)
                if image.getpixel(xy)[:3]!=ImageColor.getrgb(palette[role]):
                    raise ValueError(f"{profile['dog_id']} clipped eye pigment")
        if not dark_changes:
            raise ValueError(f"{profile['dog_id']} indistinct eye core")
    for feature,blank in (("mouth",{"mouth":[],"mouth_contact":None}),("nose",{"nose":[[0,0]]*3,"nose_surface":None})):
        if not profile[feature]:
            continue
        without=standing64.render({**profile,**blank})
        role=profile["mouth_color"] if feature=="mouth" else profile["nose_surface"]["color"]
        color=ImageColor.getrgb(palette[role])
        count=sum(a!=b and a[:3]==color for a,b in zip(image.get_flattened_data(),without.get_flattened_data()))
        if count < (2 if feature=="nose" else 1):
            raise ValueError(f"{profile['dog_id']} indistinct {feature}: {count}")


def place_face(profile, registration, project):
    # Registration is in the original photograph. Round once, after both the
    # fit and the head enlargement, to avoid moving the mouth onto the neck.
    scale=standing64.head_scale(profile)
    ax,ay=profile["head_anchor"]
    def native(p):
        x,y=project(p)
        return (round(ax+(x-ax)*scale),round(ay+(y-ay)*scale))

    tx,ty=native(registration["nose"])
    sx,sy=registration["nose"]
    ex,_=native([sx+registration["nose_width"],sy])
    width=max(2,min(6,abs(ex-tx)))
    height=1 if width==2 else max(2,width//2)
    nose_offsets=[(x-width//2,y) for y in range(height) for x in range(width)
                  if not (width>=4 and y==height-1 and x in (0,width-1))]
    # Add the observed muzzle plane where the coarse head polygon cuts it off.
    # Reserve a one-cell contour around the projected nose and lip, so an
    # external landmark is not translated back into the cheek to fit its ink.
    contours=[]
    if registration.get("muzzle_edge"):
        contours.append([native(p) for p in registration["muzzle_edge"]])
    contours[:]=[[(max(1,min(62,x)),max(1,min(62,y))) for x,y in polygon] for polygon in contours]
    profile["native_face_contours"]=contours
    stages={}
    standing64.render(profile,stages=stages)
    owner=stages["ownership"]
    head_id=1+next(i for i,p in enumerate(profile["parts"]) if p["name"]=="head")
    support=owner.point(lambda i:255 if i==head_id else 0)
    lip_mask=Image.new("1",(64,64))
    if registration["mouth"]:
        ImageDraw.Draw(lip_mask).line([native(p) for p in registration["mouth"]],fill=1)
    def reserve(target, offsets, occupied=frozenset()):
        # Prefer the photographed head surface within one native cell. A thin
        # projecting tip can share its perimeter with the single outline ink.
        x,y=target
        fits=[]
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                core={(x+dx+a,y+dy+b) for a,b in offsets}
                if core & occupied:
                    continue
                rim={(u+i,v+j) for u,v in core for i in (-1,0,1) for j in (-1,0,1)}
                if any(not (1<=u<=62 and 1<=v<=62) for u,v in rim):
                    continue
                missing={p for p in rim if not support.getpixel(p) and owner.getpixel(p)==0}
                fits.append((len(missing),dx*dx+dy*dy,dy,dx,sorted(missing),core))
        if fits:
            chosen=min(fits)
            for u,v in chosen[-2]:
                support.putpixel((u,v),255)
                contours.append([(u,v)]*3)
            return chosen[-1]
        return set()
    reserved_nose=reserve((tx,ty),nose_offsets)
    reserved_nose.update((tx+a,ty+b) for a,b in nose_offsets)
    targets=set()
    targets.update((x,y) for y in range(64) for x in range(64) if lip_mask.getpixel((x,y)))
    targets.update(native(p) for p in registration["eyes"])
    for x,y in sorted(targets):
        reserve((x,y),[(0,0)],reserved_nose)
    base=standing64.render(profile,stages=stages)
    owner=stages["ownership"]
    interior=base.getchannel("A").filter(ImageFilter.MinFilter(3))
    legal={(x,y) for y in range(1,63) for x in range(1,63)
           if owner.getpixel((x,y))==head_id and interior.getpixel((x,y))}
    # Ear folds are drawn after the face and can vary independently.
    fold=Image.new("1",(64,64))
    ImageDraw.Draw(fold).line([(round(ax+(x-ax)*scale),round(ay+(y-ay)*scale))
                              for x,y in profile["details"][0]["polygon"]],fill=1)
    legal={p for p in legal if not fold.getpixel(p)}
    palette=profile["palette"]
    rgb={k:ImageColor.getrgb(c) for k,c in palette.items()}
    def brightness(role):
        r,g,b=rgb[role]
        return .299*r+.587*g+.114*b
    deep=sorted(("dark","outline"),key=brightness)
    used=set()
    planes={}
    def nearest(target,offsets):
        available=legal-used
        choices=[p for p in available if all((p[0]+dx,p[1]+dy) in available for dx,dy in offsets)]
        if not choices:
            raise ValueError("registered face has insufficient visible interior")
        return min(choices,key=lambda p:((p[0]-target[0])**2+(p[1]-target[1])**2,p[1],p[0]))
    def ink(pixels):
        # Choose a deep palette role that is distinguishable from the underlying coat.
        counts={role:sum(base.getpixel(p)[:3]!=rgb[role] for p in pixels) for role in deep}
        return max(deep,key=lambda role:counts[role])
    def contour_light(points,role,side):
        # Keep a short edge on the lit brow, bridge or lower lip when dark fur merges.
        for x,y in points:
            q=x+side[0],y+side[1]
            if q in legal and q not in used and max(abs(a-b) for a,b in zip(base.getpixel(q)[:3],rgb[role]))<38:
                shades=[r for r in ("grey","light") if brightness(r)-brightness(role)>=32]
                if shades:
                    planes[q]=shades[0]
    profile["face_coordinates"]="native"
    for i,landmark in enumerate(registration["eyes"]):
        partial=i in registration.get("partial_eyes",[])
        target=native(landmark)
        offsets=[(0,0)] if partial else [(0,0),(1,0),(1,-1)]
        x,y=nearest(target,offsets)
        if not partial and (x-target[0])**2+(y-target[1])**2>2:
            # Small side-view sockets cannot always fit a two-cell eye plus catchlight.
            # Retain the pupil's position before spending another cell on its highlight.
            offsets=[(0,0)]
            x,y=nearest(target,offsets)
        core=[(x,y)] if len(offsets)==1 else [(x,y),(x+1,y)]
        role=ink(core)
        symbol="d" if role=="dark" else "i"
        profile["eyes"].append(dict(center=[x,y],offset=[0,0] if len(core)==1 else [0,-1],
                                    rows=[symbol] if len(core)==1 else [".l",symbol*2]))
        used.update((x+dx,y+dy) for dx,dy in offsets)
        contour_light(core,role,(0,1))
    # The ink width follows the observed nose width on this specific photograph.
    offsets=nose_offsets
    x,y=nearest((tx,ty),offsets)
    nose=[(x+a,y+b) for a,b in offsets]
    profile["nose"]=[[x-width//2,y],[x-width//2+width-1,y],
                     [max(a for a,b in nose if b==y+height-1),y+height-1],
                     [min(a for a,b in nose if b==y+height-1),y+height-1]]
    role=ink(nose)
    profile["nose_surface"]=dict(color=role)
    if width>=4:
        profile["nose_surface"]["reflection"]=dict(at=[x,y],color="grey")
    used.update(nose)
    contour_light(nose,role,(0,-1))
    # Clip each sampled point of the lip to visible jaw, preserving open-mouth direction.
    if registration["mouth"]:
        line=[]
        for start,end in zip(registration["mouth"],registration["mouth"][1:]):
            x0,y0=native(start)
            x1,y1=native(end)
            steps=max(abs(x1-x0),abs(y1-y0),1)
            for step in range(steps+1):
                target=round(x0+(x1-x0)*step/steps),round(y0+(y1-y0)*step/steps)
                pos=nearest(target,[(0,0)])
                if not line or line[-1]!=pos:
                    line.append(pos)
        profile["mouth"]=[list(p) for p in line] if len(line)>1 else [list(line[0])]*2
        role=ink(line)
        profile["mouth_color"]=role
        used.update(line)
        contour_light(line,role,(0,1))
    profile["face_planes"]={}
    for p,role in planes.items():
        if p not in used:
            profile["face_planes"].setdefault(role,[]).append(list(p))


def simplify_face_shading(profile, regions, project, reach, tones):
    """Keep continuous secondary coat tones within photo-registered facial planes."""
    if reach < 1 or not regions:
        raise ValueError("facial shading requires observed regions and a positive radius")
    ax, ay = profile["head_anchor"]
    scale = standing64.head_scale(profile)
    def native(vertex):
        x, y = project(vertex)
        return round(ax+(x-ax)*scale), round(ay+(y-ay)*scale)

    # Sample the coat beneath the features. Counting the eyes or lip as fur
    # would preserve the very dark patches that obscure those features.
    stages = {}
    bare = standing64.render({**profile, "eyes":[], "nose":[[-1,-1]]*3,
                              "nose_surface":None, "mouth":[], "face_planes":{}}, stages=stages)
    owner = stages["ownership"]
    head = 1+next(i for i,p in enumerate(profile["parts"]) if p["name"]=="head")
    inner = bare.getchannel("A").filter(ImageFilter.MinFilter(3))
    interior = {(x,y) for y in range(1,63) for x in range(1,63)
                if owner.getpixel((x,y))==head and inner.getpixel((x,y))}
    planes = {tuple(p):role for role,pixels in profile["face_planes"].items() for p in pixels}
    eye_centers = [tuple(e["center"]) for e in profile["eyes"]]
    feature = Image.new("1", standing64.SIZE)
    pen = ImageDraw.Draw(feature)
    if eye_centers:
        pen.point(eye_centers, fill=1)
    nose_mask = Image.new("1", standing64.SIZE)
    ImageDraw.Draw(nose_mask).polygon([tuple(v) for v in profile["nose"]], fill=1)
    pen.polygon([tuple(v) for v in profile["nose"]], fill=1)
    if profile["mouth"]:
        pen.line([tuple(v) for v in profile["mouth"]], fill=1)
    nearby = {p for p in interior if feature.getpixel(p)}
    for _ in range(reach):
        nearby |= {(x+dx,y+dy) for x,y in nearby for dx,dy in ((0,1),(0,-1),(1,0),(-1,0))} & interior
    observed_base = {}
    for region in regions:
        mask = Image.new("1", standing64.SIZE)
        ImageDraw.Draw(mask).polygon([native(p) for p in region["vertices"]], fill=1)
        base, alternate = region["base"], region["alternate"]
        secondary = ImageColor.getrgb(profile["palette"][alternate])
        surface = {p for p in interior if mask.getpixel(p)}
        matching = {p for p in surface if bare.getpixel(p)[:3]==secondary}
        forbidden = {ImageColor.getrgb(profile["palette"][role]) for role in region.get("exclude", [])}
        for x,y in surface:
            observed_base[x,y] = base
            swatch = bare.getpixel((x,y))[:3]
            invalid = swatch in forbidden
            if (x,y) not in nearby and not invalid:
                continue
            adjacent = sum((x+dx,y+dy) in matching for dx in (-1,0,1) for dy in (-1,0,1))
            planes[x,y] = alternate if (x,y) in matching and adjacent>=5 else base
    # At the edge of a cleaned patch, a single leftover dark fur pixel can read
    # as a second pupil. Resolve it only if the neighbouring coat was treated.
    deep = {ImageColor.getrgb(profile["palette"][r]) for r in ("dark","outline")}
    remaining = {p for p in observed_base if p not in planes and bare.getpixel(p)[:3] in deep}
    for x,y in remaining:
        ring = {(x+dx,y+dy) for dx in (-1,0,1) for dy in (-1,0,1) if (dx,dy)!=(0,0)}
        if ring.issubset(interior) and not ring & remaining and len(ring & planes.keys())>=3:
            planes[x,y] = observed_base[x,y]
    # Contact ink is part of the observed lip or nose, on its original pixels.
    # This permits a lip to meet a nose without both forming one dark blob.
    if "nose" in tones:
        profile["nose_surface"]["color"] = tones["nose"]
    if "mouth" in tones:
        profile["mouth_color"] = tones["mouth"]
    if "lip_contact" in tones and profile["mouth"]:
        near_nose = nose_mask.filter(ImageFilter.MaxFilter(3))
        line = Image.new("1", standing64.SIZE)
        ImageDraw.Draw(line).line([tuple(p) for p in profile["mouth"]], fill=1)
        pixels = [[x,y] for x,y in interior if line.getpixel((x,y)) and near_nose.getpixel((x,y))]
        if pixels:
            profile["mouth_contact"] = {"color":tones["lip_contact"], "pixels":sorted(pixels)}
    profile["face_planes"] = {}
    for pixel,role in sorted(planes.items()):
        profile["face_planes"].setdefault(role,[]).append(list(pixel))


def compile_pose(photo, observation, revision, registration):
    # Normalized annotation coordinates are independent along the two photo axes.
    # Map both back to source pixels before fitting the dog to the square canvas.
    w, h = photo.size
    points = [p for part in registration["parts"] for p in part["vertices"]]
    xs, ys = zip(*points)
    left, right = min(xs)*w/64, max(xs)*w/64
    top, bottom = min(ys)*h/64, max(ys)*h/64
    scale = 50 / max(right-left, bottom-top)
    ox, oy = 31.5 - (left+right)*scale/2, 31.5 - (top+bottom)*scale/2

    def grid(p):
        return [round(p[0]*w/64*scale+ox), round(p[1]*h/64*scale+oy)]

    # Average the source before sampling so isolated hairs do not become noise.
    sample = photo.convert("L").resize((max(1,round(w*scale)),max(1,round(h*scale))),
                                       Image.Resampling.BOX).filter(ImageFilter.GaussianBlur(.35))
    palette = dict(zip(standing64.ROLES, registration["palette"], strict=True))
    def brightness(x, y):
        sx = max(0,min(sample.width-1,round(x-ox)))
        sy = max(0,min(sample.height-1,round(y-oy)))
        return sample.getpixel((sx,sy))

    # Exposure is relative to this dog's visible coat, not the background.
    silhouette = Image.new("1",(64,64))
    for region in registration["parts"]:
        ImageDraw.Draw(silhouette).polygon([tuple(grid(p)) for p in region["vertices"]],fill=1)
    values = sorted(brightness(x,y) for y in range(64) for x in range(64) if silhouette.getpixel((x,y)))
    low,high = (values[round((len(values)-1)*q)] for q in (.05,.95))
    thresholds = [low + (high-low)*k for k in (.19,.49,.78)]
    if "tone_quantiles" in registration:
        thresholds=[values[round((len(values)-1)*q)] for q in registration["tone_quantiles"]]
    def tone(x, y):
        value = brightness(x,y)
        return standing64.ROLES[1+sum(value>cut for cut in thresholds)]

    parts = []
    for region in registration["parts"]:
        name = region["name"]
        vertices = [grid(p) for p in region["vertices"]]
        mask = Image.new("1", (64,64))
        ImageDraw.Draw(mask).polygon([tuple(v) for v in vertices],fill=1)
        markings = []
        for y in range(64):
            row = [tone(x,y) if mask.getpixel((x,y)) else None for x in range(64)]
            for role, run in groupby(enumerate(row),key=lambda item:item[1]):
                if role is None or role=="grey":
                    continue
                cols = [x for x,_ in run]
                a,b = [cols[0],y],[cols[-1],y]
                markings.append(dict(color=role,polygon=[a,b,a]))
        for plane in region.get("coat_planes", []):
            markings.append(dict(color=plane["color"], polygon=[grid(p) for p in plane["vertices"]]))
        part = dict(name=name,shape=vertices,fill="grey",markings=markings)
        if name not in ("head","trunk"):
            part["outline_neighbors"] = 4
        parts.append(part)
    head = next(p for p in parts if p["name"]=="head")
    hx,hy = zip(*head["shape"])
    # A cropped portrait already occupies the frame. Other poses use the
    # standing renderer's default enlargement around the lower cranium.
    anchor = [round((min(hx)+max(hx))/2),round(min(hy)*.26+max(hy)*.74)]
    profile = dict(format=standing64.V2,dog_id=observation["dog_id"],source_revision=revision,
                   source_sha256=maker.digest(maker.canonical(observation).encode()),
                   head_anchor=anchor,palette=palette,parts=parts,seams=[],shadows=[],preserve_outline=True,
                   eyes=[],nose=[[0,0]]*3,nose_surface=None,mouth=[],
                   details=[dict(part="head",color="grey",polygon=[grid(p) for p in registration["ear_fold"]])],
                   observed_pose=registration["pose"])
    if "head_scale" in registration:
        profile["head_scale"]=registration["head_scale"]
    elif registration["pose"]=="portrait":
        profile["head_scale"]=1
    def project(p):
        return p[0]*w/64*scale+ox,p[1]*h/64*scale+oy
    place_face(profile,registration,project)
    if "face_shade_reach" in registration:
        simplify_face_shading(profile, registration["face_regions"], project,
                              registration["face_shade_reach"], registration.get("contact_tones", {}))
    return profile
