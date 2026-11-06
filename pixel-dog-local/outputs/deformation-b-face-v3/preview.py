"""Render photograph-registered head profiles and broad, thin pinna surfaces."""
import importlib.util
import json
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.interpolate import PchipInterpolator, CubicSpline
from scipy.ndimage import gaussian_filter, gaussian_filter1d

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("nana_face_v2", HERE.parent / "deformation-b-face-v2/preview.py")
old = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = old
spec.loader.exec_module(old)
BG, INK, MUTED, LINE = old.BG, old.INK, old.MUTED, old.LINE
BREEDS, NAMES = old.BREEDS, old.NAMES
label, pose, paint, polys = old.label, old.pose, old.paint, old.polys
NOSE_COLOR = (47, 44, 40)
NOSE_WIDTH = 4.1
NOSE_HEIGHT = 2.2
NOSE_FRONT_ROUND = NOSE_WIDTH
NOSE_HEIGHT_ROUND = 1.35
NOSE_TOP_DEPTH = 3.6


def smoothstep(value):
    value = np.clip(value, 0, 1)
    return value**3*(3-2*value)


def nose_depth(cosine):
    """One shared three-dimensional leather boundary, deepest dorsally."""
    return 2.5 + (NOSE_TOP_DEPTH-2.5)*cosine + 1.4*(1-cosine**2)


def load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def curve_at(points, xs):
    points = np.array(sorted(points, key=lambda p: p[0]), dtype=float)
    xx, index = np.unique(points[:, 0], return_index=True)
    return PchipInterpolator(xx, points[index, 1], extrapolate=True)(np.clip(xs, xx[0], xx[-1]))


def point_segment_distance(x, y, points):
    points = np.asarray(points)
    distance = np.full_like(x, np.inf)
    for a, b in zip(points[:-1], points[1:]):
        dx, dy = b-a
        t = np.clip(((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy), 0, 1)
        distance = np.minimum(distance, np.hypot(x-a[0]-t*dx, y-a[1]-t*dy))
    return distance


def periodic_boundary(points, count=129):
    points = np.array(points, dtype=float)
    keep = np.r_[True, np.linalg.norm(np.diff(points, axis=0), axis=1)>1e-8]
    points = points[keep]
    if np.linalg.norm(points[-1]-points[0])<1e-8:
        points = points[:-1]
    points = np.vstack((points, points[0]))
    arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    return CubicSpline(arc, points, bc_type="periodic")(np.linspace(0, arc[-1], count))


def contour_sections(top, bottom, count=241):
    # Use intersections of the entire closed contour. A rotated nose or rear
    # profile can turn back on x, so independently interpolating two functions
    # would turn the nose edge into a spur or truncate the ear attachment.
    boundary = periodic_boundary(top + bottom[::-1], 1201)
    xmin, xmax = boundary[:, 0].min(), boundary[:, 0].max()
    xs = np.linspace(xmin+.001, xmax-.001, count)
    a, b = boundary[:-1], boundary[1:]
    dx = b[:, 0]-a[:, 0]
    high, low = [], []
    for x in xs:
        t = np.divide(x-a[:, 0], dx, out=np.full_like(dx, -1), where=np.abs(dx)>1e-9)
        intersections = a[:, 1]+t*(b[:, 1]-a[:, 1])
        vals = intersections[(t>=0)&(t<=1)]
        high.append(vals.max())
        low.append(vals.min())
    return xs, np.asarray(high), np.asarray(low)


def local_profile(rig, raw):
    world = pose(rig)
    origin = np.array(world['body.head'])
    local = {key: (np.array(raw[key])-origin)[:, :2].tolist() for key in ('top', 'bottom', 'mouth', 'nose')}
    local['ear_boundary'] = (np.array(raw['ear'])-origin)[:, :2].tolist()
    local['ear_ridge'] = (np.array(raw['ridge'])-origin)[:, :2].tolist()
    p = {k[5:]: np.array(v)-origin for k, v in world.items() if k.startswith('face.')}
    w = raw['half_width']
    near = min(x for x, y in local['top'])
    far = max(x for x, y in local['top'])
    local['width'] = [(near, p['L_nose_wing'][2]*.65),
                      (p['nose'][0]+.50, p['L_nose_wing'][2]),
                      (p['L_muzzle_side'][0], p['L_muzzle_side'][2]),
                      (p['stop'][0], w*.72), (p['L_eye'][0], w*.83),
                      (p['skull'][0], w), (p['L_temple'][0], w*.93),
                      (far, w*.65)]
    local['ear_depth'] = [(min(x for x,y in local['ear_boundary'])-1, w*.83),
                          (max(x for x,y in local['ear_boundary'])+1, w*.72)]
    local['eye_radius'] = (w*.16, w*.09)
    local['nose_color'] = raw.get('nose_color', NOSE_COLOR)
    return local


def head_features(rig, breed, profile):
    """All sagittal coordinates are local to the head attachment in body units."""
    world = pose(rig)
    p = {k[5:]: np.array(v)-world['body.head'] for k, v in world.items() if k.startswith('face.')}
    color, ear_color = map(lambda v: np.asarray(v, dtype=float), old.COLORS[breed])
    top, bottom = profile['top'], profile['bottom']
    xmax = max(max(v[0] for v in top), max(v[0] for v in bottom))
    # The photographs terminate the back-of-head profile in the adjoining neck.
    # Complete that cross-section with a rounded occipital cap, behind the ear root.
    cap = .22*profile['width'][-1][1]
    back_y = float((curve_at(top, np.array([xmax]))[0]+curve_at(bottom, np.array([xmax]))[0])/2)
    # Profile arrays run from the neck end toward the nose.
    top = [[xmax+cap, back_y+.01]] + top
    bottom = [[xmax+cap, back_y-.01]] + bottom
    width_points = profile['width'] + [[xmax+cap, .025]]
    xmax += cap
    xs, hi, lo = contour_sections(top, bottom, 481)
    lo = np.minimum(lo, hi-.025)
    width = curve_at(width_points, xs)
    closure = np.sin(np.clip((xs-xs[0])/(.045*np.ptp(xs)), 0, 1)*np.pi/2)
    width *= closure
    theta = np.linspace(0, 2*np.pi, 289)
    cos, sin = np.cos(theta), np.sin(theta)
    power = {'golden': .70, 'whippet': .92, 'dachshund': .84}[breed]
    # The nasal planum has a top and lateral wings. Build its common shallow
    # rostral section inside the head mesh, then blend the dorsal bridge and
    # cheek into the source profile. There is no separate perched nose object.
    nose_y = float((hi[0]+lo[0])*.5)
    depth = xs-xs[0]
    rounding = np.sqrt(np.maximum(0, 1-(1-np.clip(depth/NOSE_FRONT_ROUND,0,1))**2))
    height_rounding = np.sqrt(np.maximum(0, 1-(1-np.clip(depth/NOSE_HEIGHT_ROUND,0,1))**2))
    top_weight = 1-smoothstep((depth-4.2)/3.0)
    width_weight = 1-smoothstep((depth-4.2)/3.0)
    hi = hi*(1-top_weight)+(nose_y+NOSE_HEIGHT*height_rounding)*top_weight
    # In dorsal view the muzzle widens over its full length. A short blend
    # into the old width samples made a parallel-sided neck and angular flare.
    skull_x = p['skull'][0]
    skull_width = float(curve_at(width_points,np.array([skull_x]))[0])
    muzzle_t = np.clip((xs-(xs[0]+4.2))/(skull_x-(xs[0]+4.2)),0,1)
    rounded_width = NOSE_WIDTH+(skull_width-NOSE_WIDTH)*smoothstep(muzzle_t)
    width = np.where(xs<=skull_x,rounded_width,width)
    width = np.where(depth<=4.2,NOSE_WIDTH*rounding,width)
    mid = ((hi+lo)/2)*(1-top_weight)+np.minimum(nose_y, hi)*top_weight
    mid = np.clip(mid,lo,hi)
    cheek_blend = smoothstep((xs-p['stop'][0])/max(1,p['skull'][0]-p['stop'][0]))
    muzzle_power = 1.0*(1-cheek_blend)+power*cheek_blend
    section_power = muzzle_power[:,None]*(1-width_weight[:,None])+.72*width_weight[:,None]
    ysection = np.where(cos[None,:]>=0,
                        mid[:,None]+(hi-mid)[:,None]*np.abs(cos)**section_power,
                        mid[:,None]-(mid-lo)[:,None]*np.abs(cos)**section_power)
    shell = np.stack(np.broadcast_arrays(
        xs[:, None], ysection,
        width[:, None]*np.sign(sin)*np.abs(sin)**section_power), axis=-1)
    centers = (shell[:-1, :-1]+shell[1:, :-1]+shell[1:, 1:]+shell[:-1, 1:])*.25
    xx, yy, zz = centers.transpose(2, 0, 1)
    colors = np.broadcast_to(color, xx.shape+(3,)).copy()
    def stain(mask, tint):
        nonlocal colors
        mask = np.clip(mask, 0, 1)[..., None]
        colors = colors*(1-mask)+np.asarray(tint)*mask
    nose_mask = smoothstep((nose_depth(np.cos((theta[:-1]+theta[1:])*.5))[None,:]-(xx-xs[0]))/.22+.5)
    lower_edge = nose_y-1.8 + .85*((xx-xs[0])/4.2)**2 + .45*(zz/NOSE_WIDTH)**2
    nose_mask *= smoothstep((yy-lower_edge)/.3)
    nose_tint = np.asarray(profile['nose_color'], dtype=float)
    stain(nose_mask, nose_tint)
    # Small paired nostril shadows follow the same shared rostral coordinates.
    # They are pigment within the leather, not ear/mouth outline strokes.
    nostril = np.exp(-2*((xx-xs[0]-1.35)/.85)**2-2*((np.abs(zz)-3.3)/.75)**2-2*((yy-nose_y-.30)/.85)**2)
    stain(nostril*nose_mask*.88, nose_tint*.35)
    for side, sign in [('L_', 1), ('R_', -1)]:
        e = p[side+'eye']
        eye_w, eye_h = profile.get('eye_radius', (1.15, .65))
        # Eye boundaries keep their observed sagittal location. The lateral
        # coordinate comes from the continuous cheek surface at that location.
        horizontal = (xx-e[0])/eye_w
        vertical = (yy-e[1]-profile.get('eye_tilt',.12)*(xx-e[0]))/eye_h
        ds = horizontal**2 + np.abs(vertical)**profile.get('eye_power',1.7)
        visible = sign*zz > 0
        stain(np.clip((1.12-ds)*4, 0, 1)*visible, (52, 42, 32))
        stain(np.exp(-4*(horizontal**2+(vertical*.8)**2))*.50*visible, (107, 77, 42))
        stain(np.exp(-12*(horizontal**2+vertical**2))*.98*visible, (27, 26, 24))
        stain(np.exp(-((horizontal+.25)**2/.023+(vertical-.21)**2/.065))*.75*visible, (242, 228, 204))
    features = [(shell, colors)]
    # Closed cross-sections run from a broad embedded root to the ear tip.
    # The two ear families use their observed hanging/backward fold axes.
    ew = max(width)
    ear = np.asarray(profile['ear_boundary'])
    backwards = breed == 'whippet'
    section_points = ear if backwards else ear[:, ::-1]
    axes, outer_hi, outer_lo = contour_sections(section_points.tolist(), [], 181)
    root = p['L_ear_root']
    start = root[0]-.18*ew if backwards else root[1]+.18*ew
    stop = axes[-1]-.01 if backwards else axes[0]+.01
    along = np.linspace(start,stop,121)
    distance = np.abs(along-start)
    source_center = np.interp(along,axes,(outer_hi+outer_lo)/2)
    source_half = np.interp(along,axes,(outer_hi-outer_lo)/2)
    root_center = root[1] if backwards else root[0]
    shape_blend = smoothstep(distance/(.65*ew))
    centerline = root_center*(1-shape_blend)+source_center*shape_blend
    halfspan = .34*ew*(1-shape_blend)+source_half*shape_blend
    centerline = gaussian_filter1d(centerline,3,mode='nearest')
    halfspan = gaussian_filter1d(halfspan,3,mode='nearest')
    # Caps are entirely inside the head at the root and close at the free tip.
    halfspan[0] = halfspan[-1] = 0
    phi = np.linspace(0,2*np.pi,161)
    transverse = centerline[:,None]+halfspan[:,None]*np.cos(phi)
    axial = np.broadcast_to(along[:,None],transverse.shape)
    rx,ry = (axial,transverse) if backwards else (transverse,axial)
    source_hi = np.interp(rx,xs,hi)
    source_lo = np.interp(rx,xs,lo)
    cap_zone = (1-smoothstep(distance/(.20*ew)))[:,None]
    cap_shift = np.minimum(0,np.min(source_hi-.18*ew-ry,axis=1))
    ry = ry+cap_zone*cap_shift[:,None]
    source_mid = np.interp(rx,xs,mid)
    source_power = np.interp(rx,xs,section_power[:,0])
    source_radius = np.where(ry>=source_mid,source_hi-source_mid,source_mid-source_lo)
    source_cos = np.clip(np.abs(ry-source_mid)/np.maximum(source_radius,.01),0,1)**(1/source_power)
    skull_depth = np.interp(rx,xs,width)*np.maximum(0,1-source_cos**2)**(source_power/2)
    u = (np.cos(phi)+1)/2
    tilt = halfspan[:,None]*(.6*(u-.5)+.12*np.sin(np.pi*u))
    support = np.maximum(ew*.92,np.max(skull_depth+.015*ew-tilt,axis=1))
    support = gaussian_filter1d(support,8,mode='nearest')
    ordinary_depth = support[:,None]+tilt
    root_zone = 1-smoothstep((distance-.18*ew)/(.62*ew))
    root_lift = -.18*ew*(1-smoothstep(distance/(.18*ew)))
    root_lift += .07*ew*smoothstep((distance-.18*ew)/(.37*ew))
    half_thickness = ew*(.032+.070*root_zone)
    half_thickness *= np.sqrt(np.clip((len(along)-1-np.arange(len(along)))/12,0,1))
    half_thickness[0] = half_thickness[-1] = 0
    # The outer root surface meets the skull tangentially; its thickness
    # extends inward, so it does not leave a raised cuff on the head.
    attachment_depth = np.maximum(.02,skull_depth+root_lift[:,None]
                                  -half_thickness[:,None]*np.abs(np.sin(phi)))
    middle_depth = ordinary_depth*(1-root_zone[:,None])+attachment_depth*root_zone[:,None]
    softened = gaussian_filter(middle_depth[:,:-1],sigma=(8,6),mode=('nearest','wrap'))
    softened = np.column_stack((softened,softened[:,0]))
    smooth_weight = smoothstep((distance-.18*ew)/(.4*ew))[:,None]
    middle_depth = middle_depth*(1-smooth_weight)+softened*smooth_weight
    middle_depth[-1] = middle_depth[-1].mean()
    for sign in (1,-1):
        surface = np.stack((rx,ry,sign*(middle_depth+half_thickness[:,None]*np.sin(phi))),axis=-1)
        # Keep the complete attachment band at the pre-rounding coordinates.
        # Only fair the free ear surface; moving the root to hide a corner
        # changes the visible insertion site even when rig nodes stay fixed.
        rounded = gaussian_filter(surface[:,:-1],sigma=(5,4,0),mode=('nearest','wrap','nearest'))
        rounded = np.concatenate((rounded,rounded[:,:1]),axis=1)
        free_weight = smoothstep((distance-.65*ew)/(.35*ew))[:,None,None]
        free_weight *= smoothstep((distance[-1]-distance)/(.20*ew))[:,None,None]
        surface = surface*(1-free_weight)+rounded*free_weight
        # In-place fillet: cut only the outer corners of the root rectangle.
        # The central attachment rail, depth, and free ear stay unchanged.
        fillet_radius = .14*ew
        edge_distance = np.abs(transverse-centerline[:,None])
        edge_u = np.clip((edge_distance-(halfspan[:,None]-fillet_radius))/fillet_radius,0,1)
        corner_cut = fillet_radius*(1-np.sqrt(np.maximum(0,1-edge_u**2)))
        corner_band = smoothstep(distance/(.12*ew))*(1-smoothstep((distance-.30*ew)/(.35*ew)))
        corner_cut *= corner_band[:,None]
        surface[:,:,0 if backwards else 1] += (1 if backwards else -1)*corner_cut
        if backwards:
            # Round the other face of the same corner in the y/z section,
            # so the fillet is visible from front and rear as well as side.
            root_rows = distance <= .90*ew
            radius = .30*ew
            corner_y = surface[root_rows,:,1].max()-radius
            corner_z = np.abs(surface[root_rows,:,2]).max()-radius
            dy = surface[:,:,1]-corner_y
            dz = np.abs(surface[:,:,2])-corner_z
            length = np.hypot(dy,dz)
            excess = np.where((dy>0)&(dz>0),np.maximum(0,1-radius/np.maximum(length,1e-9)),0)
            surface[:,:,1] -= dy*excess
            surface[:,:,2] -= sign*dz*excess
        # A continuous closed section supplies both sides and the rounded rim.
        features.append((surface,ear_color))
    return features


def draw_head(image, rig, breed, profile, angle, box, scale=None, elev=0):
    mesh = old.make_face(rig, breed) if profile is None else head_features(rig, breed, profile)
    vertices, colors = polys(mesh, angle, elev)
    xy = vertices[:, :, :2]
    low, high = xy.min(axis=(0, 1)), xy.max(axis=(0, 1))
    left, top, right, bottom = box
    if scale is None:
        scale = min((right-left)/(high[0]-low[0]), (bottom-top)/(high[1]-low[1]))
    center = np.array([(left+right)/2, (top+bottom)/2]) - (low+high)/2*np.array([scale, -scale])
    paint(image, vertices, colors, center, scale)


def board(current, profiles):
    image = Image.new('RGB', (1540, 1050), BG)
    d = ImageDraw.Draw(image)
    label(image, 36, 27, 'NANA    /    FACIAL STRUCTURE     03', 14, '#8E6247', True)
    label(image, 34, 60, 'B 압축형 · 코 형태 통일', 36, bold=True)
    label(image, 36, 116, '공통 코의 윗면·옆면을 주둥이에 연결했습니다. 측면·윗면·¾를 같은 골격에서 확인합니다.', 18, MUTED)
    columns = [(34, 387), (419, 758), (790, 1130), (1160, 1506)]
    headings = ['관찰한 사진', '수정 B  ·  측면', '수정 B  ·  위에서', '수정 B  ·  ¾']
    for (left, right), heading in zip(columns, headings):
        label(image, left, 170, heading, 19, bold=True)
    for row, (breed, name) in enumerate(zip(BREEDS, NAMES)):
        top = 207+row*258
        d.line((34, top, 1506, top), fill=LINE, width=1)
        label(image, 35, top+15, name, 21, bold=True)
        raw, rig = profiles[breed], current[breed]
        photo = Image.open(HERE.parents[1] / raw['photo']).crop(raw['crop'])
        photo_scale = min(350/photo.width, 184/photo.height)
        photo = photo.resize((round(photo.width*photo_scale), round(photo.height*photo_scale)), Image.Resampling.LANCZOS)
        image.paste(photo, (34+(350-photo.width)//2, top+57))
        profile = local_profile(rig, raw)
        cases = [(rig, profile, 90, 0), (rig, profile, 90, 90), (rig, profile, 38, 12)]
        boxes = [(left, top+35, right, top+234) for left, right in columns[1:]]
        sizes = []
        for (r, pro, angle, elev), box in zip(cases, boxes):
            mesh = old.make_face(r, breed) if pro is None else head_features(r, breed, pro)
            points, _ = polys(mesh, angle, elev)
            size = np.ptp(points[:, :, :2], axis=(0, 1))
            sizes.extend(((box[2]-box[0])/size[0], (box[3]-box[1])/size[1]))
        common_scale = min(sizes)
        for (r, pro, angle, elev), box in zip(cases, boxes):
            draw_head(image, r, breed, pro, angle, box, common_scale, elev)
    d.line((34, 987, 1506, 987), fill=LINE, width=1)
    label(image, 35, 1007, '코·귀 연결 검토용입니다. 사진 보정·닫힌 입·반대편 폭과 귀의 두께·곡률은 작화값입니다.', 15, MUTED)
    return image


def nose_top(rigs, profiles):
    image = Image.new('RGB', (1080, 290), BG)
    label(image, 28, 18, '윗모습 · 코 앞끝 확대', 26, bold=True)
    for column, (breed, name) in enumerate(zip(BREEDS, NAMES)):
        left = 22+column*354
        label(image, left, 65, name, 18, bold=True)
        panel = Image.new('RGB', (330, 170), BG)
        rig = rigs[breed]
        mesh = head_features(rig, breed, local_profile(rig, profiles[breed]))
        vertices, colors = polys(mesh, 90, 90)
        tip_x = vertices[:,:,0].min()
        paint(panel, vertices, colors, np.array([28-tip_x*17,85]),17)
        image.paste(panel, (left,96))
    return image


def standing(rigs, profiles):
    image = Image.new('RGB', (1420, 750), BG)
    d = ImageDraw.Draw(image)
    label(image, 36, 20, 'B 압축형  ·  목 길이와 어깨 연결 수정', 31, bold=True)

    def bezier(a, b, c, endpoint):
        t = np.linspace(0, 1, 23)[:, None]
        return (1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*endpoint

    for column, (breed, name) in enumerate(zip(BREEDS, NAMES)):
        left, ground = 32+column*461, 356
        label(image, left, 75, name, 20, bold=True)
        rig = rigs[breed]
        model = old.prev['Model'](rig, breed, 1.22)
        p = {key: np.asarray(value) for key, value in model.pts.items()}
        angle = np.deg2rad(82)
        scale, ox = 4.45, left+174
        def xy(v):
            return (ox+scale*(np.sin(angle)*v[0]+np.cos(angle)*v[2]), ground-scale*v[1])
        def polygon(points, color, smooth=True):
            vertices = [xy(v) for v in points]
            d.polygon(old.prev['smooth_ring'](vertices) if smooth else vertices, fill=tuple(map(int, color)))

        color = np.asarray(old.COLORS[breed][0])
        rib, pelvis = [np.asarray(v) for v in model.rib], model.pel
        center, upper, lower, fringe = model.tail
        polygon(upper+fringe[::-1], color*.80)
        for side in ('right', 'left'):
            for chain, radii in ((old.prev['FRONT'], [2,3,2,1.1,1,.3]), (old.prev['BACK'], [3.5,3.1,1.5,1.1,.3])):
                points = np.asarray(model.limb(side, chain))
                widths = np.asarray(radii)*{'golden':1.25,'whippet':.82,'dachshund':.98}[breed]
                tangent = np.gradient(points[:, :2], axis=0)
                normal = np.stack((-tangent[:, 1], tangent[:, 0]), axis=1)
                normal /= np.maximum(.1, np.linalg.norm(normal, axis=1, keepdims=True))
                delta = normal*widths[:, None]
                first, second = points.copy(), points.copy()
                first[:, :2] += delta
                second[:, :2] -= delta
                first[:, 1] = np.maximum(0, first[:, 1])
                second[:, 1] = np.maximum(0, second[:, 1])
                tint = color*(.76 if side == 'right' else .95)
                polygon(list(first)+list(second[::-1]), tint)
                pad, toe = points[-2:]
                polygon([pad+[1.1,-pad[1],0],pad+[.7,.48,0],toe+[-.75,1,0],toe+[-.92,0,0]],tint)
        polygon([*rib[:4],p['body.lumbar_pivot'],model.guide('pelvic_dorsum'),pelvis[2],p['body.tail_root'],
                 *pelvis[3:5],p['body.left_hip'],model.guide('belly_guide'),*rib[6:]],color)

        # The nape meets the withers tangentially, while the throat widens into
        # the front of the chest. The curves derive their endpoints from the
        # relocated head and the fixed thorax instead of drawing a long shaft.
        occiput, throat = p['face.occiput'].copy(), p['face.L_cheek'].copy()
        occiput[2] = throat[2] = 0
        shoulder = rib[2]
        chest = rib[9]
        span = max(1, occiput[1]-shoulder[1])
        back = bezier(occiput, occiput+[.12*span,-.50*span,0],
                      shoulder+[-.25*span,1.1,0], shoulder)
        front = bezier(chest, chest+[-2.3,2.4,0], throat+[.7,-.45*max(1,throat[1]-chest[1]),0], throat)
        polygon([*back, rib[3], rib[4], p['body.left_shoulder'], chest, *front], color, False)
        vertices, colors = polys(head_features(rig,breed,local_profile(rig,profiles[breed])),82,0)
        paint(image, vertices, colors, np.asarray(xy(p['body.head'])), scale)
        d.line((left, ground+1, left+438, ground+1), fill=LINE)
        label(image,left,394,'관찰한 원사진',16,MUTED)
        photo = Image.open(HERE.parents[1] / profiles[breed]['photo']).convert('RGB')
        factor = min(438/photo.width, 264/photo.height)
        photo = photo.resize((round(photo.width*factor),round(photo.height*factor)),Image.Resampling.LANCZOS)
        image.paste(photo,(left+(438-photo.width)//2,428+(264-photo.height)//2))
    label(image,36,713,'목의 길이와 고개 위치는 B 데포르메의 작화값이며, 원사진은 품종별 목·어깨 연결을 확인하는 자료입니다.',15,MUTED)
    return image


if __name__ == '__main__':
    current = load('B.json')['breeds']
    profiles = load('profiles.json')
    board(current, profiles).save(HERE / 'faces.png')
    nose_top(current, profiles).save(HERE / 'nose-top.png')
    standing(current, profiles).save(HERE / 'standing.png')

