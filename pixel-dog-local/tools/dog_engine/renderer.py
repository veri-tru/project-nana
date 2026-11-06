"""Projection extracted from skull-based-heads-v2/13 without shape changes.

This runtime imports no archived generator. The source and regression contract
are recorded in docs/engine-organization.md.
"""
import numpy as np
from PIL import ImageDraw, ImageFont
from .raster import paint

FONT = "C:/Windows/Fonts/malgun.ttf"
BOLD = "C:/Windows/Fonts/malgunbd.ttf"
INK = (38, 54, 48)

def projected(model,az=50,el=6,show_ears=True):
    t,e=np.radians([az,el]);right=np.array([np.sin(t),0,np.cos(t)])
    front=np.array([-np.cos(t)*np.cos(e),np.sin(e),np.sin(t)*np.cos(e)])
    up=np.cross(front,right);view=np.column_stack([right,up,front]);qq=[];cc=[]
    for key,part in model['parts'].items():
        v,n=part['v']@view,part['n']@view
        light=np.array([-.32,.72,.61]);shade=.73+.24*np.maximum(0,n@light)+.035*np.maximum(0,n[:,1])
        c=np.clip(part['c']*shade[:,None],0,255)
        ix=part['f'][:,[0,1,2,2]];qq.append(v[ix]);cc.append(c[ix])
    return np.concatenate(qq),np.concatenate(cc)


def label(im, x, y, text, size=21, bold=False):
    ImageDraw.Draw(im).text((x, y), text,
        font=ImageFont.truetype(BOLD if bold else FONT, size), fill=INK)
