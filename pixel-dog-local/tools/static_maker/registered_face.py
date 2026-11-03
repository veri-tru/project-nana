"""Place photo-traced face planes in native pixels using two corresponding eyes."""
from PIL import Image, ImageChops, ImageDraw, ImageFilter


def registration(source_eyes, grid_eyes):
    a,b=(complex(*xy) for xy in source_eyes)
    c,d=(complex(*xy) for xy in grid_eyes)
    if a==b or c==d:
        raise ValueError('two distinct eye centres are required in both spaces')
    scale=(d-c)/(b-a)
    def place(x,y):
        point=c+scale*(complex(x,y)-a)
        return round(point.real),round(point.imag)
    return place


def eye_ink(size, socket, pupil_left, pupil_top, rows, gaze):
    """Place the pupil within a fixed socket; expose sclera only away from gaze."""
    if gaze not in (-1,0,1):raise ValueError('gaze must be -1, 0 or 1')
    pupil=Image.new('L',size)
    pen=ImageDraw.Draw(pupil)
    for j,row in enumerate(rows):
        for i,c in enumerate(row):
            if c=='#':pen.point((pupil_left+i+gaze,pupil_top+j),fill=255)
    pupil=ImageChops.multiply(socket,pupil)
    white=Image.new('L',size)
    if gaze:
        # Only the vacated side of the globe has an exposed sliver of white.
        shifted=Image.new('L',size)
        shifted.paste(pupil,(-gaze,0))
        rim=ImageChops.subtract(shifted,pupil)
        white=ImageChops.multiply(socket,rim)
    return pupil,white


def draw_face(body, source_eyes, grid_eyes, contour, layers, outline, fringe, eyes, *, seams=(), gaze=0):
    """Layers are ordered (ink, vertices); shift only the fringe in target pixels."""
    if 'transparency' not in body.info or body.mode!='P':
        raise ValueError('indexed base with transparent background required')
    place=registration(source_eyes,grid_eyes)
    def shape(vertices,dy=0):
        mask=Image.new('L',body.size)
        points=[(x,y+dy) for x,y in (place(*xy) for xy in vertices)]
        if any(x<0 or x>=body.width or y<0 or y>=body.height for x,y in points):
            raise ValueError('face plane outside canvas')
        ImageDraw.Draw(mask).polygon(points,fill=255)
        return mask
    head=shape(contour)
    result=body.copy()
    for ink,vertices in layers:
        result.paste(ink,mask=ImageChops.multiply(head,shape(vertices)))
    for ink,vertices in seams:
        stroke=Image.new('L',body.size)
        ImageDraw.Draw(stroke).line([place(*p) for p in vertices],fill=255,width=1)
        result.paste(ink,mask=ImageChops.multiply(head,stroke))
    cores=[]
    for (cx,cy),eye in zip(grid_eyes,eyes,strict=True):
        sclera,dark,light,glint=eye
        x,y=round(cx)-2,round(cy)-2
        socket=Image.new('L',body.size)
        ImageDraw.Draw(socket).ellipse((x,y,x+4,y+4),fill=255)
        socket=ImageChops.multiply(head,socket)
        result.paste(sclera,mask=socket)
        pupil,white=eye_ink(body.size,socket,x+1,y,('.##.','####','####','.##.'),gaze)
        result.paste(light,mask=white)
        result.paste(dark,mask=pupil)
        if pupil.getpixel((x+2+gaze,y+1)):
            result.putpixel((x+2+gaze,y+1),glint)
        cores.append((pupil,dark))
    ink,vertices,depth=fringe
    if type(depth)!=int or depth<0:raise ValueError('fringe travel must be nonnegative pixels')
    coverage=shape(vertices)
    for dy in range(1,depth+1):
        coverage=ImageChops.lighter(coverage,shape(vertices,dy))
    result.paste(ink,mask=ImageChops.multiply(head,coverage))
    # Exposed silhouette and deliberately authored internal seams share one ink.
    alpha=result.convert('RGBA').getchannel('A')
    edge=ImageChops.subtract(alpha,alpha.filter(ImageFilter.MinFilter(3)))
    result.paste(outline,mask=edge)
    for pupil,dark in cores:
        visible=[(x,y) for y in range(body.height) for x in range(body.width)
                 if pupil.getpixel((x,y)) and result.getpixel((x,y))==dark]
        if (len(visible)<4 or len({x for x,y in visible})<2
                or len({y for x,y in visible})<2):
            raise ValueError('fringe or silhouette collapses the visible pupil')
    return result
