"""Native pixel body components from standing or seated pose landmarks."""
import math
from PIL import Image


SEATED_LIMBS = {
    name: joints
    for joints, limb in [
        (("shoulder", "elbow", "carpus", "mcp", "toe_tip"), "foreleg"),
        (("hip", "stifle", "tarsus", "mtp", "toe_tip"), "hindleg"),
    ]
    for name in (f"seated_near_{limb}", f"seated_far_{limb}")
}


def seated_limb_mask(component, profile):
    """Sweep a disc of interpolated radius along each successive bone on the grid."""
    limbs = profile.get("seated_limbs")
    limb = limbs.get(component) if isinstance(limbs, dict) else None
    joints = SEATED_LIMBS[component]
    if not isinstance(limb, dict) or set(limb) != set(joints):
        raise ValueError(f"{component} requires joint triples for {', '.join(joints)}")
    centers = []
    for joint in joints:
        value = limb[joint]
        if (not isinstance(value, (tuple, list)) or len(value) != 3
                or any(type(v) not in (int, float) or not math.isfinite(v) for v in value)):
            raise ValueError(f"{component}.{joint} requires a finite x, y and radius")
        x, y, r = value
        if r <= 0 or min(x, y) - r < 0 or max(x, y) + r > 63:
            raise ValueError(f"{component}.{joint} requires a positive radius inside the 64px grid")
        centers.append((x, y, r))

    mask = Image.new("L", (64, 64))
    pixels = mask.load()
    for (ax, ay, ar), (bx, by, br) in zip(centers, centers[1:]):
        dx, dy, dr = bx - ax, by - ay, br - ar
        # Minimize squared distance minus squared radius along this segment.
        # If one end disc contains the other, the larger disc is the full sweep.
        curvature = dx*dx + dy*dy - dr*dr
        for y in range(math.ceil(min(ay-ar, by-br)), math.floor(max(ay+ar, by+br))+1):
            for x in range(math.ceil(min(ax-ar, bx-br)), math.floor(max(ax+ar, bx+br))+1):
                if curvature > 0:
                    t = max(0, min(1, ((x-ax)*dx + (y-ay)*dy + ar*dr) / curvature))
                else:
                    t = int(br > ar)
                if (x-ax-t*dx)**2 + (y-ay-t*dy)**2 <= (ar+t*dr)**2:
                    pixels[x, y] = 255
    if mask.getbbox() is None:
        raise ValueError(f"{component} covers no native pixels")
    return mask


def point(value, label):
    if (not isinstance(value, (list, tuple)) or len(value) != 2 or
        any(type(v) not in (int, float) or not math.isfinite(v) for v in value)):
        raise ValueError(f"{label} requires a finite x,y pair")
    return value


def body_shape(component, profile):
    traits, pose = profile["morphology"], profile["stance"]
    length, depth, tuck, width = (traits[k] for k in
        ("trunk_length", "chest_depth", "belly_tuck", "foreleg_width"))
    if any(type(v) not in (float,int) or not math.isfinite(v) for v in (length,depth,tuck,width)):
        raise ValueError("body dimensions must be finite")
    if not (2 <= length <= 63 and 2 <= depth <= 63 and 0 <= tuck < depth and 1 <= width <= 32):
        raise ValueError("invalid body dimensions in native pixels")
    sx,sy = point(pose["withers"],"withers")
    direction = pose["facing"]
    if type(direction) is not int or direction not in (-1,1):
        raise ValueError("facing must be 1 (right) or -1 (left)")
    def at(back,down):
        return round(sx-direction*back), round(sy+down)

    if component == "trunk":
        nx,ny = point(profile["head_anchor"],"neck")
        coords = [(round(nx-direction*.4*width),round(ny-.22*depth)),at(0,0),at(.25*length,0),
                  at(.65*length,-.08*depth),at(.90*length,0),at(length,.2*depth),
                  at(length,.64*depth),at(.9*length,.78*depth),
                  at(.73*length,depth-tuck),at(.56*length,depth-tuck),
                  at(.27*length,depth),at(.08*length,depth),at(-width*.6,.75*depth),
                  (round(nx),round(ny+.1*depth))]
    elif component == "chest":
        nx,ny = point(profile["head_anchor"],"neck")
        coords = [(round(nx),round(ny)),at(width,.32*depth),at(width,depth*.83),
                  at(.25*width,depth),at(-.5*width,depth*.95),at(-width,.67*depth)]
    elif component in ("near_foreleg", "far_foreleg"):
        fx,fy = point(pose["feet"][component],component)
        rx,ry = at(0 if component=="near_foreleg" else .12*length,.4*depth)
        if fy <= ry+2:
            raise ValueError("forefoot must be below its shoulder")
        # Width in native pixels; interpolate the centreline from shoulder to paw.
        def edge(t, fraction):
            return (round(rx+(fx-rx)*t+direction*width*fraction),round(ry+(fy-ry)*t))
        coords = [edge(0,.45),edge(.32,.50),edge(.72,.23),edge(.90,.21),
                  edge(.96,.46),edge(1,.43),edge(1,-.39),edge(.94,-.36),
                  edge(.82,-.15),edge(.54,-.26),edge(.32,-.5),edge(.06,-.48)]
    else:
        raise ValueError(f"unknown standing component: {component}")
    if any(not (0<=x<64 and 0<=y<64) for x,y in coords):
        raise ValueError(f"{component} extends outside the 64px grid")
    return coords
