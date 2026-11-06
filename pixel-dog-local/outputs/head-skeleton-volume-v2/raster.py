"""Local deterministic depth-buffer renderer reused from deformation-b-face-v2."""
import numpy as np
from numba import njit
from PIL import Image

@njit(cache=True)
def raster(px,color,buf,rgb):
    height,width=buf.shape
    for q in range(len(px)):
        for j in (1,2):
            a,b,c=px[q,0],px[q,j],px[q,j+1]
            ax,ay,az=a; bx,by,bz=b; cx,cy,cz=c
            det=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
            if abs(det)<1e-5: continue
            for y in range(max(0,int(np.floor(min(ay,by,cy)))),min(height,int(np.ceil(max(ay,by,cy)))+1)):
                for x in range(max(0,int(np.floor(min(ax,bx,cx)))),min(width,int(np.ceil(max(ax,bx,cx)))+1)):
                    one=((by-cy)*(x+.5-cx)+(cx-bx)*(y+.5-cy))/det
                    two=((cy-ay)*(x+.5-cx)+(ax-cx)*(y+.5-cy))/det
                    thr=1.-one-two
                    if min(one,two,thr)<-.00001: continue
                    z=az*one+bz*two+cz*thr
                    if z>buf[y,x]:
                        buf[y,x]=z
                        for ch in range(3):
                            rgb[y,x,ch]=color[q,0,ch]*one+color[q,j,ch]*two+color[q,j+1,ch]*thr


def paint(im,xyz,colors,center,scale):
    ss=2
    q=xyz.copy(); q[:,:,0]=q[:,:,0]*scale+center[0]; q[:,:,1]=center[1]-q[:,:,1]*scale
    l,t=np.floor(q[:,:,:2].min(axis=(0,1))-2).astype(int)
    r,b=np.ceil(q[:,:,:2].max(axis=(0,1))+2).astype(int)
    q[:,:,:2]=(q[:,:,:2]-np.array([l,t]))*ss
    under=im.crop((l,t,r,b)).resize(((r-l)*ss,(b-t)*ss))
    colors=np.ascontiguousarray(colors,dtype=np.uint8)
    canvas=np.array(under)
    raster(q,colors,np.full(canvas.shape[:2],-np.inf),canvas)
    im.paste(Image.fromarray(canvas).resize((r-l,b-t),Image.Resampling.LANCZOS),(l,t))
