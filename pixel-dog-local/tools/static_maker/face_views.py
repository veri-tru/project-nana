"""Orthographic views of a registered head and one shared, layered muzzle model.

Coordinates are in source-grid units: x to the right, y down, z towards the
reference camera. Depth values describe an illustration, not measured anatomy.
"""
from dataclasses import dataclass
import math
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from registered_face import eye_ink


@dataclass(frozen=True)
class View:
    yaw: float
    pitch: float = 0
    roll: float = 0

    def axes(self):
        a,b=map(math.radians,(self.yaw,self.pitch))
        c,s=math.cos(a),math.sin(a)
        t,u=math.cos(b),math.sin(b)
        xaxis,yaxis=(c,0,s),(-u*s,t,u*c)
        cr,sr=math.cos(math.radians(self.roll)),math.sin(math.radians(self.roll))
        return (tuple(cr*x-sr*y for x,y in zip(xaxis,yaxis)),
                tuple(sr*x+cr*y for x,y in zip(xaxis,yaxis)),(-t*s,-u,t*c))


def dot(a,b):
    return sum(x*y for x,y in zip(a,b))


def projected_head(front, pivot, radius_ratio, view, *, side_coat=None, outline=None):
    """Reproject each opaque head row as an elliptical cross-section.

    The frontal surface carries the registered pixels. The unseen rear half
    extends the side-coat colour, rather than duplicating the eyes or blaze.
    """
    px,py=pivot
    axes=view.axes()
    depths=Image.new('F',front.size,float('-inf'))
    rings=[]
    for y in range(front.height):
        xs=[x for x in range(front.width) if front.getpixel((x,y))[3]]
        if not xs:continue
        mid=(xs[0]+xs[-1])/2
        rx=(xs[-1]-xs[0]+1)/2
        if not any((view.yaw,view.pitch,view.roll)):
            for x in xs:
                depths.putpixel((x,y),rx*radius_ratio*math.sqrt(max(0,1-((x-mid)/rx)**2)))
            continue
        ring=[]
        for i in range(64):
            a=math.tau*i/64
            x=mid+rx*math.sin(a)
            z=rx*radius_ratio*math.cos(a)
            xyz=(x-px,y-py,z)
            ring.append((px+dot(axes[0],xyz),py+dot(axes[1],xyz),dot(axes[2],xyz)))
        rings.append((y,mid,rx,ring,xs))
    if not any((view.yaw,view.pitch,view.roll)):
        return front.copy(),depths
    faces=[]
    for row,nextrow in zip(rings,rings[1:]):
        y,mid,rx,ring,xs=row
        for i in range(64):
            j=(i+1)%64
            quad=[ring[i],ring[j],nextrow[3][j],nextrow[3][i]]
            a=math.tau*(i+.5)/64
            pos=mid+rx*math.sin(a)
            if math.cos(a)<0:
                pos=mid+math.copysign(max(rx-2,0),math.sin(a))
            sx=min(xs[-1],max(xs[0],round(pos)))
            ink=front.getpixel((sx,y))
            # A 1px frontal contour must not become a slab of fur on the back.
            if side_coat is not None and (math.cos(a)<0 or
                    (ink==outline and min(sx-xs[0],xs[-1]-sx)<=1)):
                ink=side_coat
            faces.append((sum(pt[2] for pt in quad),[(round(x),round(v)) for x,v,_ in quad],
                          ink))
    out=Image.new('RGBA',front.size)
    pen=ImageDraw.Draw(out)
    depth_pen=ImageDraw.Draw(depths)
    for depth_sum,quad,ink in sorted(faces,key=lambda face:face[0]):
        pen.polygon(quad,fill=ink)
        depth_pen.polygon(quad,fill=depth_sum/4)
    return out,depths


@dataclass(frozen=True)
class MuzzleProfile:
    root: tuple
    width: float
    height: float
    nose_width: float
    nose_height: float


@dataclass(frozen=True)
class SideFeatures:
    """Projected eye centres in reference pixels and an ear seam (azimuth°, row)."""
    eyes: tuple
    ear_curve: tuple
    gaze: int = 0


def side_landmarks(front, pivot, radius_ratio, view, details, colors):
    # Sample the same cross-sections as projected_head. A curve can continue
    # onto the unobserved side, whose precise anatomy is a design estimate.
    axes=view.axes()
    def section(y):
        row=[x for x in range(front.width) if front.getpixel((x,round(y)))[3]]
        if not row:raise ValueError('side landmark outside registered head')
        return (row[0]+row[-1])/2,(row[-1]-row[0]+1)/2
    def project(x,y,z):
        xyz=(x-pivot[0],y-pivot[1],z)
        return tuple(round(pivot[i]+dot(axis,xyz)) for i,axis in enumerate(axes[:2]))
    template=front.copy()
    for cx,cy in details.eyes:
        ImageDraw.Draw(template).ellipse((cx-2,cy-2,cx+2,cy+2),fill=colors['mid'])
    head,surface=projected_head(template,pivot,radius_ratio,view,side_coat=colors['coat'],outline=colors['outline'])
    original_alpha=head.getchannel('A')
    pen=ImageDraw.Draw(head)
    edge=[]
    sign=-1 if view.yaw>0 else 1
    for azimuth,y in details.ear_curve:
        mid,rx=section(y)
        a=math.radians(sign*azimuth)
        edge.append(project(mid+rx*math.sin(a),y,rx*radius_ratio*math.cos(a)))
    pen.line(edge,fill=colors['outline'],width=1)
    for cx,cy in details.eyes:
        mid,rx=section(cy)
        s=(cx-mid)/rx
        if abs(s)>=1:raise ValueError('eye outside registered head')
        c=math.sqrt(1-s*s)
        # Visibility of an eye on the elliptic surface, in camera coordinates.
        n=(s,0,c/radius_ratio)
        facing=dot(n,axes[2])/math.sqrt(dot(n,n))
        if facing<.14:continue
        x,y=project(cx,cy,rx*radius_ratio*c)
        w=4 if facing>.75 else 3
        stencil=('.##.','####','####','.##.') if w==4 else ('.#.','###','###','.#.')
        interior=original_alpha.filter(ImageFilter.MinFilter(3))
        # Snap an edge-on socket at most one cell towards the centre of the
        # face before the exterior contour is drawn. Never stamp outside it.
        for shift in (0,sign):
            left=x+shift-w//2
            socket=Image.new('L',head.size)
            ImageDraw.Draw(socket).ellipse((left-1,y-2,left+w,y+3),fill=255)
            socket=ImageChops.multiply(socket,interior)
            neutral,_=eye_ink(head.size,socket,left,y-1,stencil,0)
            if neutral.histogram()[255]>=5:break
        if neutral.histogram()[255]<4:continue
        pupil,white=eye_ink(head.size,socket,left,y-1,stencil,details.gaze)
        head.paste(colors['mid'],mask=socket)
        head.paste(colors['light'],mask=white)
        head.paste(colors['dark'],mask=pupil)
        glint=(left+1+details.gaze,y)
        if w==4 and pupil.getpixel(glint):pen.point(glint,fill=colors['mid'])
    head.putalpha(original_alpha)
    return head,surface


def compose_profile_head(body, head, jaw_columns, outline):
    """Composite a view-specific head and mark its visible underside over the bib."""
    hull=head.getchannel('A')
    face=head.copy()
    for x in jaw_columns:
        column=hull.crop((x,0,x+1,head.height)).getbbox()
        if column and column[3]<head.height and body.getpixel((x,column[3]))[3]:
            face.putpixel((x,column[3]-1),outline)
    frame=Image.alpha_composite(body,face)
    alpha=frame.getchannel('A')
    frame.paste(outline,mask=ImageChops.subtract(alpha,alpha.filter(ImageFilter.MinFilter(3))))
    return frame


def muzzle_view(size,pivot,profile,depth,view,colors,head_depth=None,*,side_fur_slope=0):
    """Resolve visibility by closest ray/surface hit, including the short lip.

    Both viewpoints use the same solids. Extension adds length along the nose
    axis but does not increase cheek width or scale the nose.
    """
    if not all(math.isfinite(q) and q>0 for q in
               (profile.width,profile.height,profile.nose_width,profile.nose_height,depth)):
        raise ValueError('positive finite dimensions and muzzle depth required')
    ax,ay,az=profile.root
    if not math.isfinite(side_fur_slope) or not 0<=side_fur_slope<=2:
        raise ValueError('side fur slope must be between 0 and 2')
    w,h=profile.width,profile.height
    # The axis descends from between the eyes and slightly towards screen left
    # in the frontal reference. Express the distal end in object coordinates.
    tip=(ax-.20*depth,ay+.28*h+.32*depth,az+depth)
    parts=[
        ('chin',(ax,ay+.60*h+.19*depth,az+.60*depth),(.32*w,.32*h,.39*depth)),
        ('left',(ax-.20*w,ay+.26*h,az+.10*h),(.30*w,.42*h,.36*h)),
        ('right',(ax+.20*w,ay+.26*h,az+.10*h),(.30*w,.42*h,.36*h)),
        ('left',(ax-.15*w,ay+.27*h+.15*depth,az+.62*depth),(.25*w,.36*h,.37*depth)),
        ('right',(ax+.15*w,ay+.27*h+.15*depth,az+.62*depth),(.25*w,.36*h,.37*depth)),
        ('bridge',((ax+tip[0])/2,ay+.01*h,az+.45*depth),(.21*w,.48*h,.60*depth)),
        ('lip',(tip[0],tip[1]+profile.nose_height*.95,tip[2]-.14*depth),
         (.14*w,.055*h,.11*depth)),
        ('nose',tip,(profile.nose_width/2,profile.nose_height/2,.21*w))
    ]
    xaxis,yaxis,ray=view.axes()
    px,py=pivot
    out=Image.new('RGBA',size)
    masks={name:Image.new('L',size) for name,_,_ in parts}
    # Distinguish far-pad loss behind the near pad from loss behind the nose.
    footprints={name:Image.new('L',size) for name in ('left','right')}
    for y in range(size[1]):
        for x in range(size[0]):
            origin=tuple((x-px)*xaxis[i]+(y-py)*yaxis[i] for i in range(3))
            closest=None
            for name,(cx,cy,cz),radii in parts:
                delta=tuple(origin[i]-v for i,v in enumerate((cx-px,cy-py,cz)))
                # Above the nose, the photo-registered coat can sweep towards
                # the viewer independently of anatomical nose depth. Inverse
                # shear the ray to intersect the two joined halves exactly.
                sweep=side_fur_slope*abs(math.sin(math.radians(view.yaw))) if name in ('left','right','bridge') else 0
                hits=[]
                for k in ((0,sweep) if sweep else (0,)):
                    dr=(ray[0],ray[1],ray[2]+k*ray[1])
                    dc=(delta[0],delta[1],delta[2]+k*(origin[1]+py-tip[1]))
                    aa=sum((v/r)**2 for v,r in zip(dr,radii))
                    bb=sum(v*d/r**2 for v,d,r in zip(dr,dc,radii))
                    cc=sum((v/r)**2 for v,r in zip(dc,radii))-1
                    disc=bb*bb-aa*cc
                    if disc<0:continue
                    for sign_root in (1,-1):
                        distance=(-bb+sign_root*math.sqrt(disc))/aa
                        yy=origin[1]+py+distance*ray[1]
                        if not sweep or (yy<=tip[1])==bool(k):
                            hits.append((distance,k,dc,dr));break
                if not hits:continue
                distance,k,dc,dr=max(hits,key=lambda hit:hit[0])
                if name in footprints:footprints[name].putpixel((x,y),255)
                if closest is not None and distance<=closest[0]:continue
                normal=[(d+distance*v)/r**2 for d,v,r in zip(dc,dr,radii)]
                normal[1]+=k*normal[2]
                length=math.sqrt(dot(normal,normal))
                light=dot(normal,(-.38,-.62,.68))/length
                ink=colors['light'] if light>.22 else colors['mid']
                if name=='nose':ink=colors['coat'] if light>.85 else colors['dark']
                if name=='lip':ink=colors['dark']
                closest=(distance,name,ink)
            if closest and (head_depth is None or closest[0]>head_depth.getpixel((x,y))):
                _,name,ink=closest
                out.putpixel((x,y),ink);masks[name].putpixel((x,y),255)
    return out,masks,footprints


def render_view(body, registered_head, pivot, radius_ratio, profile, depth, view, colors, *, side_coat=None, side_features=None, side_fur_slope=0):
    """Composite a native RGBA body, photo-registered head and projected muzzle.

    Colors are RGBA inks. Return the frame and the final surface ownership masks
    so callers can check occlusion and feature separation at the delivery grid.
    """
    if body.mode!='RGBA' or registered_head.mode!='RGBA' or body.size!=registered_head.size:
        raise ValueError('expected matching native RGBA body and head')
    if radius_ratio<=0 or not math.isfinite(radius_ratio):
        raise ValueError('invalid head radius ratio')
    if side_features is not None and view.yaw:
        head,surface=side_landmarks(registered_head,pivot,radius_ratio,view,side_features,colors)
    else:
        head,surface=projected_head(registered_head,pivot,radius_ratio,view,side_coat=side_coat,outline=colors['outline'])
    muzzle,owners,footprints=muzzle_view(body.size,pivot,profile,depth,view,colors,surface,
                                         side_fur_slope=side_fur_slope)
    frame=Image.alpha_composite(body,Image.alpha_composite(head,muzzle))
    alpha=frame.getchannel('A')
    edge=ImageChops.subtract(alpha,alpha.filter(ImageFilter.MinFilter(3)))
    frame.paste(colors['outline'],mask=edge)
    owners={k:ImageChops.subtract(m,edge) for k,m in owners.items()}
    return frame,owners,footprints
