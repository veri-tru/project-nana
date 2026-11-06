"""Register visible head contours to the compact B skeleton.

Photo coordinates are manual observations. Neutral pitch, hidden width and the
closed golden jaw are authored estimates, stored separately in each profile.
"""
import json
import math
import runpy
from copy import deepcopy
from pathlib import Path

OUT = Path(__file__).resolve().parent
FK = runpy.run_path(str(OUT.parent / "integrated-rig-b-v1/build.py"))
DATA = {
    "golden": dict(
        photo="private-data/guide-roster/002/source.jpg", crop=[460, 14, 650, 146],
        direction=1, pitch=0, scale=.215, mount=[518,97], half_width=10.2,
        top=[[491,49],[513,32],[539,27],[558,33],[570,43],[579,55],[604,57],[625,59],[631,65]],
        bottom=[[491,98],[515,113],[545,114],[559,111],[583,110],[608,108],[621,99],[628,84],[631,65]],
        mouth=[[558,104],[576,103],[594,102],[608,99],[620,91],[625,81]],
        nose=[[616,59],[626,58],[632,63],[630,74],[625,81],[617,77],[614,67]],
        ear=[[493,48],[505,40],[518,43],[526,56],[533,73],[541,94],[539,107],[531,114],[515,114],[499,108],[486,96],[477,81],[480,62]],
        ridge=[[505,44],[518,57],[529,77],[535,99]],
        points=dict(crown=[539,27],occiput=[491,49],stop=[579,55],nose=[629,65],nose_bottom=[625,81],
                    upper_lip=[620,91],chin=[608,108],skull=[532,65],brow=[560,44],eye=[562,55],
                    temple=[515,63],cheek=[548,96],mouth_corner=[558,104],muzzle_side=[596,83],
                    jaw_hinge=[531,94],jaw_side=[568,110],nose_wing=[622,69],
                    ear_root=[505,44],ear_fold=[519,74],ear_tip=[530,113]),
        notes="near-side profile observed; open source mouth replaced by authored closed lower jaw; hidden width symmetric"),
    "dachshund": dict(
        photo="private-data/breed-standing-pair-v1/dachshund-source.png",crop=[608,78,936,323],
        direction=1,pitch=8,scale=.116,mount=[719,216],half_width=8.3,
        top=[[663,145],[681,112],[714,94],[749,91],[785,98],[808,112],[821,133],[853,144],[887,155],[909,161],[918,172]],
        bottom=[[670,205],[703,224],[734,230],[751,228],[787,226],[826,224],[864,224],[889,214],[906,197],[918,172]],
        mouth=[[751,220],[787,218],[825,219],[863,219],[887,209],[902,194]],
        nose=[[889,159],[904,159],[917,168],[918,180],[910,193],[901,194],[890,180]],
        ear=[[676,140],[693,137],[710,141],[716,183],[734,231],[746,270],[740,292],[726,305],[713,307],[686,302],[659,291],[641,278],[628,259],[623,239],[634,208],[645,177]],
        ridge=[[685,143],[674,183],[665,224],[676,277]],
        points=dict(crown=[749,91],occiput=[663,145],stop=[821,133],nose=[914,173],nose_bottom=[905,193],
                    upper_lip=[890,207],chin=[861,224],skull=[739,161],brow=[783,121],eye=[785,137],
                    temple=[709,157],cheek=[746,204],mouth_corner=[751,220],muzzle_side=[843,185],
                    jaw_hinge=[724,208],jaw_side=[791,228],nose_wing=[905,175],
                    ear_root=[693,141],ear_fold=[678,220],ear_tip=[713,304]),
        notes="near-side contour observed; pitch raised 8 degrees for neutral; hidden width symmetric"),
    "whippet": dict(
        photo="private-data/breed-standing-pair-v1/whippet-source.png",crop=[80,105,390,307],
        direction=-1,pitch=25,scale=.155,mount=[270,220],half_width=7.5,
        top=[[283,150],[263,134],[242,127],[221,139],[192,169],[172,205],[147,224],[121,244],[106,251],[101,262]],
        bottom=[[283,218],[262,242],[244,247],[219,265],[192,280],[164,289],[140,288],[119,277],[106,266],[101,262]],
        mouth=[[204,264],[183,275],[162,282],[141,281],[121,273]],
        nose=[[119,245],[106,251],[101,262],[108,271],[119,277],[133,264],[130,251]],
        ear=[[274,149],[287,132],[311,119],[329,121],[344,134],[359,156],[371,172],[359,170],[345,159],[328,153],[313,160],[298,165],[281,161]],
        ridge=[[284,146],[306,134],[328,138],[349,155]],
        points=dict(crown=[242,127],occiput=[283,150],stop=[172,205],nose=[106,260],nose_bottom=[119,277],
                    upper_lip=[141,281],chin=[164,289],skull=[239,196],brow=[211,170],eye=[211,183],
                    temple=[262,177],cheek=[244,247],mouth_corner=[204,264],muzzle_side=[161,252],
                    jaw_hinge=[251,239],jaw_side=[213,271],nose_wing=[118,260],
                    ear_root=[279,150],ear_fold=[311,129],ear_tip=[365,168]),
        notes="source is three-quarter; side length and hidden width are estimates; pitch raised 25 degrees"),
}


def main():
    model=json.loads((OUT.parent / "deformation-rig-b-v1/B.json").read_text(encoding="utf8"))
    base=deepcopy(model)
    profiles={}
    for breed,spec in DATA.items():
        rig=model["breeds"][breed]
        old=FK["world_pose"](rig)
        head=old["body.head"]
        w=spec["half_width"]
        a=math.radians(spec["pitch"])
        def point(xy,lateral=0):
            forward=(xy[0]-spec["mount"][0])*spec["direction"]
            up=spec["mount"][1]-xy[1]
            z=(forward*math.cos(a)-up*math.sin(a))*spec["scale"]
            y=(forward*math.sin(a)+up*math.cos(a))*spec["scale"]
            return [head[0]-z,head[1]+y,lateral]
        vertices={k:point(v) for k,v in spec["points"].items()}
        new=deepcopy(old)
        for name in ("skull","crown","occiput","stop","nose","nose_bottom","upper_lip","chin"):
            new["face."+name]=vertices[name]
        for side,sign in (("L_",1),("R_",-1)):
            for name in ("brow","eye","temple","cheek","mouth_corner","muzzle_side","jaw_hinge","jaw_side","nose_wing","ear_root","ear_fold","ear_tip"):
                lateral={"eye":.77,"brow":.78,"temple":1,"cheek":.94,"mouth_corner":.66,
                         "muzzle_side":.67,"jaw_side":.62,"nose_wing":.46,
                         "jaw_hinge":.79,"ear_root":.82,"ear_fold":1.03,"ear_tip":.96}[name]
                new["face."+side+name]=point(spec["points"][name],sign*w*lateral)
            eye=new["face."+side+"eye"]
            for name,dy,dz in (("eye_inner",0,-1.6),("eye_outer",0,1.6),("upper_lid",.9,0),("lower_lid",-.7,0),("pupil",0,0)):
                new["face."+side+name]=[eye[0],eye[1]+dy,eye[2]+sign*dz]
        new["face.jaw_axis"]=[(x+y)/2 for x,y in zip(new["face.L_jaw_hinge"],new["face.R_jaw_hinge"])]
        # Authored attachment registration for the B head. Source photo points
        # remain in source_observations; the ear hinges now use the lateral
        # temple rather than the posterior silhouette of the photo ear.
        source_root = new['face.L_ear_root'][:]
        eye = new['face.L_eye']
        target_root = [new['face.L_temple'][0],
                       eye[1]+{'golden':.04,'whippet':.18,'dachshund':.28}[breed]*w,
                       source_root[2]]
        ear_delta = [target_root[0]-source_root[0],target_root[1]-source_root[1],0]
        for side in ('L_','R_'):
            for part in ('ear_root','ear_fold','ear_tip'):
                key='face.'+side+part
                new[key]=[v+d for v,d in zip(new[key],ear_delta)]
        for name,node in rig["nodes"].items():
            if name.startswith("face."):
                node["offset"]=FK["delta"](new[name],new[node["parent"]])
        FK["verify"](rig)
        profile={k:[point(v) for v in spec[k]] for k in ("top","bottom","mouth","nose","ear","ridge")}
        for name in ('ear','ridge'):
            profile[name]=[[v+d for v,d in zip(p,ear_delta)] for p in profile[name]]
        profile['ear_registration'] = dict(source_root=source_root,target_root=target_root,
                                           translation=ear_delta,classification='authored B head attachment; not measured anatomy')
        profile.update(photo=spec["photo"],crop=spec["crop"],half_width=w,notes=spec["notes"],
                       source_observations=spec,coordinates="integrated world xyz; ear/ridge xy at z=0 before lateral placement")
        # Surfaces can follow head and jaw rotations through the existing FK frames.
        bindings={}
        for name in ("top","bottom","mouth","nose"):
            owner="face.jaw_axis" if name=="bottom" else "face.skull"
            bindings[name]=dict(owner=owner,offsets=[FK["delta"](p,new[owner]) for p in profile[name]])
        profile["bindings"]=bindings
        rig["face_shape"]=profile
        profiles[breed]=profile
        assert all(rig["nodes"][k]==base["breeds"][breed]["nodes"][k]
                   for k in rig["nodes"] if k.startswith("body."))
    model["version"]="deformation-b-face-v3"
    (OUT/"B.json").write_text(json.dumps(model,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    (OUT/"profiles.json").write_text(json.dumps(profiles,ensure_ascii=False,indent=2)+"\n",encoding="utf8")


if __name__=="__main__":
    main()
