"""Rasterize an observed muzzle as a part, independent of dog, pose and canvas size."""
import math
from PIL import Image, ImageChops, ImageDraw


def masks(size, center, span, nose_size, projection, turn, transform, *, lobe_depth=0):
    """All lengths are in authoring coordinates. Projection never expands pad span."""
    cx, cy = center
    w, h = span
    nw, nh = nose_size
    if not (0 <= projection <= 0.3 and -1 <= turn <= 1 and 0 <= lobe_depth <= .3):
        raise ValueError('projection and lobe_depth must be 0..0.3; turn must be -1..1')
    if not (0 < nw < w and 0 < nh < h and all(math.isfinite(v) for v in (*center, *span, *nose_size))):
        raise ValueError('nose must fit inside a finite muzzle span')

    def screen(vertices):
        pts=[transform(p) for p in vertices]
        if any(not (0<=x<size[0] and 0<=y<size[1]) for x,y in pts):
            raise ValueError('muzzle geometry extends outside the target canvas')
        return pts

    def polygon(vertices):
        mask = Image.new('L', size)
        ImageDraw.Draw(mask).polygon(screen(vertices), fill=255)
        return mask

    def oval(x, y, a, b):
        return [(x+a*math.cos(i*math.tau/40), y+b*math.sin(i*math.tau/40)) for i in range(40)]

    # Local +u points towards the far cheek. Reflect the *geometry*, not the lighting.
    direction = -1 if turn < 0 else 1
    yaw = abs(turn)
    advance = projection * yaw
    def at(u, v):
        return cx + direction*w*u, cy + h*v

    # Keep both outer fur edges fixed. Only the near pad's inside edge sweeps
    # across the far pad as the tip travels along the projected bridge axis.
    radius = h*(.38 + .42*lobe_depth)
    y = cy + .02*h + (radius-.38*h)
    def pad(lo, hi, dy):
        x, _ = at((lo+hi)/2, 0)
        return polygon(oval(x, y+dy*h, (hi-lo)*w/2, radius))
    far = pad(-.10, .50, -.07*yaw)
    near = pad(-.50, .10+.62*advance, .07*yaw)
    # The lower leading surface of the near whisker pad can pass *below*
    # the tip and across the far pad. Moving only the top edge would hide
    # this entire change behind the nose.
    if yaw:
        leading=polygon([at(-.20,.12),at(.04+.9*advance,.07),
                         at(.075+1.8*advance,.18),at(.07+1.5*advance,.29),
                         at(-.03+.75*advance,.37),at(-.22,.34)])
        near=ImageChops.lighter(near,ImageChops.multiply(leading,far))
    tip_u = .85*advance
    tip_v = -.16 + projection*.54
    bridge = polygon([at(-.10,-.48),at(.10,-.48),at(tip_u+.15,tip_v-.07),
                      at(tip_u+.12,tip_v+.11),at(tip_u-.12,tip_v+.11),at(tip_u-.15,tip_v-.07)])
    chin = polygon(oval(cx,cy+.20*h,.33*w,.30*h))
    pads = ImageChops.lighter(ImageChops.lighter(near,far),ImageChops.lighter(chin,bridge))

    def underside(pad_mask, dy, reach):
        # The advancing near pad exposes more of its curved underside.
        cutoff = polygon([at(u, v+dy) for u,v in
            [(-.55,-.12),(-.44,.12),(-.26,.28-reach),(0,.31-reach),
             (.26,.28-reach),(.44,.12),(.55,-.12),(.55,.75),(-.55,.75)]])
        return ImageChops.multiply(pad_mask,cutoff)

    nx,ny = at(tip_u,tip_v)
    nose = polygon([(nx+direction*nw*u,ny+nh*v) for u,v in
                    [(-.48,-.14),(-.34,-.43),(0,-.50),(.34,-.43),(.48,-.14),
                     (.43,.12),(.20,.38),(0,.50),(-.20,.38),(-.43,.12)]])
    sheen = polygon([(nx+nw*u,ny+nh*v) for u,v in
                     [(-.34,-.19),(-.2,-.40),(.17,-.40),(.27,-.23)]])
    # The lip follows the tip, with progressively less of its far end visible.
    lip_y = min(ny+nh*.5+h*.11,cy+h*.41)
    mouth=Image.new('L',size)
    for side,length in [(-1,.12),(1,max(.025,.12-.45*advance))]:
        ImageDraw.Draw(mouth).line(screen([(nx,lip_y),
                           (nx+side*direction*w*length,lip_y+.045*h)]),fill=255)
    foreground = ImageChops.lighter(bridge,ImageChops.lighter(nose,mouth))
    over_far = ImageChops.lighter(near,foreground)
    far_visible = ImageChops.subtract(far,over_far)
    near_visible = ImageChops.subtract(near,foreground)
    far_shadow=underside(far_visible,-.07*yaw,.03*yaw)
    if yaw:
        cast_start=screen([(cx,cy)])[0]
        cast_end=screen([at(.11*yaw+.42*advance,0)])[0]
        dx=cast_end[0]-cast_start[0]
        cast=Image.new('L',size)
        cast.paste(near,(dx,0))
        far_shadow=ImageChops.lighter(far_shadow,ImageChops.multiply(far_visible,cast))
    return {'muzzle':pads,'chin':chin,'far_pad':far_visible,
            'far_underside':far_shadow,
            'near_pad':near_visible,'near_underside':underside(near_visible,.07*yaw,.38*advance),
            'bridge':bridge,'mouth':ImageChops.multiply(mouth,pads),
            'nose':ImageChops.multiply(nose,pads),'nose_light':ImageChops.multiply(sheen,nose)}


ROLES = {'muzzle':'muzzle_shadow','chin':'muzzle_shadow','far_pad':'muzzle',
         'far_underside':'muzzle_shadow','near_pad':'muzzle','near_underside':'muzzle_shadow',
         'bridge':'muzzle','mouth':'nose','nose':'nose','nose_light':'coat'}


def oblique_landmark_layer(size, bridge, nose, lip, chin, near_cheek, nose_width, inks):
    """Right-facing screen-space study with independently registered facial landmarks.

    The bridge starts below the fixed eyes. The near-side mouth recedes behind
    the tip and the jaw underside shades into the cheek. No hidden-side depth
    is recovered from a single oblique photograph.
    """
    bx,by=bridge
    nx,ny=nose
    lx,ly=lip
    jx,jy=chin
    cx,cy=near_cheek
    if not (by<ny<ly<jy and nx>cx and nose_width>0):
        raise ValueError('expected a descending, right-facing muzzle')
    layer=Image.new('RGBA',size)
    pen=ImageDraw.Draw(layer)
    radius=nose_width/2
    def shape(role,points):
        pen.polygon([(round(x),round(y)) for x,y in points],fill=inks[role])
    # Start with the underside so its edge separates the chin from the bib.
    shoulder=max(bx+1,nx+radius)
    shape('mid',[(cx,cy),(bx,by),(shoulder+1,ny-3),(nx+radius,ny+1),
                 (lx+1,ly),(jx+1,jy-1),(jx,jy),(jx-4,jy),
                 (cx+2,cy+4),(cx,cy+2)])
    shape('light',[(cx,cy),(bx-2,by),(bx+1,by),
                   (shoulder,ny-4),(shoulder+1,ny-2),(nx+radius,ny),
                   (lx,ly-1),(lx-3,ly),(cx+3,cy+3),(cx,cy+1)])
    # Short closed lip, with a little light chin beyond its visible end.
    shape('light',[(lx-3,ly),(lx+1,ly),(jx,jy-1),(jx-3,jy-1)])
    pen.line([(round(lx-3),round(ly-1)),(round(lx-1),round(ly)),
              (round(lx),round(ly))],fill=inks['dark'])
    shape('dark',[(nx-radius,ny-1),(nx,ny-1),(nx+radius,ny),
                  (nx+radius-1,ny+1),(nx,ny+1),(nx-radius,ny)])
    pen.point((round(nx-1),round(ny-1)),fill=inks['coat'])
    return layer


def closed_side_muzzle(size, bridge, cheek, nose, lip, chin, nose_width, inks, *, chin_overlap=False):
    """Opaque planes for a forward-facing snout in a rightward oblique drawing.

    Only the exposed lip and chin are landmarks. The shaded lower edge
    returns into the cheek without placing or drawing a hidden jaw hinge.
    """
    bx,by=bridge
    cx,cy=cheek
    nx,ny=nose
    lx,ly=lip
    jx,jy=chin
    if not (cx<jx<lx<nx and bx<nx and by<ny<ly<jy and nose_width>=3):
        raise ValueError('a closed profile needs a forward tip and receding lower lip and chin')
    im=Image.new('RGBA',size)
    pen=ImageDraw.Draw(im)
    half=nose_width/2

    def plane(role, start, arcs):
        # Sample quadratic arcs before placing whole pixels on the native grid.
        path=[start]
        for control,end in arcs:
            x0,y0=path[-1]
            steps=max(4,math.ceil(abs(end[0]-x0)+abs(end[1]-y0)))
            for i in range(1,steps+1):
                t=i/steps
                path.append(tuple((1-t)**2*a+2*(1-t)*t*b+t*t*c
                                  for a,b,c in zip((x0,y0),control,end)))
        pen.polygon([(round(x),round(y)) for x,y in path],fill=inks[role])

    # One rounded envelope. Its underside sweeps back into the lower cheek.
    plane('light',(cx-1,cy-2),[
        ((cx+2,by),(bx,by)),((nx+half,by-1),(nx+half,ny)),
        ((nx+half,ny+1),(lx+1,ly)),((lx,jy),(jx,jy)),
        ((cx+2,jy+4),(cx-1,cy)),((cx-2,cy-1),(cx-1,cy-2))])
    # Shadow just below the distal lip. Stop before reaching the rear cheek
    # so its hidden attachment cannot become a long drawn jawline.
    envelope=im.getchannel('A')
    plane('mid',(jx-3,jy),[
        ((jx,jy-1),(lx,ly-1)),((nx+half,ny),(nx+half,ny+1)),
        ((lx,jy+1),(jx,jy+1)),((jx-2,jy+1),(jx-3,jy))])
    im.putalpha(envelope)
    if chin_overlap:
        # Show the exposed chin over the bib; stop the seam well before the ear.
        x,y=round(jx),round(jy)
        pen.line([(x-1,y-1),(x,y-1)],fill=inks['light'])
        pen.line([(x-1,y),(x,y)],fill=inks['outline'])
    pen.line([(round(lx-2),round(ly)),(round(lx),round(ly))],fill=inks['dark'])
    plane('dark',(nx-half,ny-1),[
        ((nx,ny-2),(nx+half,ny-1)),((nx+half,ny+1),(nx,ny+1)),
        ((nx-half,ny+1),(nx-half,ny-1))])
    pen.point((round(nx-1),round(ny-1)),fill=inks['coat'])
    return im
