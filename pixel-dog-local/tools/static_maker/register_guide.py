"""Build 25 guide photo registrations in a new private folder from the supplied PDF and tables."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from io import BytesIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
import fitz
from PIL import Image
import maker
from photo_pose import check_visible_features, compile_pose
import standing64

ROOT = Path(__file__).resolve().parent
RECOVERED = {"054","016"}
def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding="utf-8")


def register(pdf_path,tables,out):
    registrations = json.loads((ROOT/"guide_registration/landmarks.json").read_text(encoding="utf-8"))
    with ZipFile(tables) as archive:
        credits = json.loads(archive.read("comparison_credits.json"))["photos"]
        traits = {v["id"]:v for v in json.loads(archive.read("grouping_322.json"))}
    expected = {row["photo_id"] for row in credits} - RECOVERED
    if set(registrations)!=expected or len(credits)!=27:
        raise ValueError("guide registrations do not match the supplied photo inventory")
    out = Path(out)
    if out.exists():
        raise FileExistsError(out)
    out.parent.mkdir(parents=True,exist_ok=True)
    with TemporaryDirectory(dir=out.parent) as work:
        pending=Path(work)/"guide"
        pending.mkdir()
        entries={}
        store=maker.Store(pending/"profiles.sqlite")
        try:
            with fitz.open(pdf_path) as pdf:
                for index,credit in enumerate(credits):
                    key=credit["photo_id"]
                    if key in RECOVERED:
                        continue
                    page=pdf[1+index//9]
                    caption=page.search_for(key+"  "+credit["breed_ko"])
                    if len(caption)!=1:
                        raise ValueError(f"ambiguous photo caption {key}")
                    # A photo sits directly above its printed ID. PDF resource
                    # order has no relation to its position in the grid.
                    match=[]
                    for item in page.get_images():
                        for box in page.get_image_rects(item[0]):
                            if abs(box.y1-caption[0].y0)<18 and box.x0-62<=caption[0].x0<=box.x1:
                                match.append(item[0])
                    if len(match)!=1:
                        raise ValueError(f"ambiguous image for {key}: {match}")
                    guide=traits[key]
                    if credit["group_code"]!=guide["base"]:
                        raise ValueError(f"group mismatch {key}")
                    folder=pending/key
                    folder.mkdir()
                    source=pdf.extract_image(match[0])["image"]
                    (folder/"source-image").write_bytes(source)
                    photo=Image.open(BytesIO(source)).convert("RGB")
                    reg=registrations[key]
                    palette=dict(zip(standing64.ROLES,reg["palette"]))
                    obs=json.loads((ROOT/"example.json").read_text(encoding="utf-8"))
                    obs["dog_id"]="guide-"+key
                    obs["behavior"]={}
                    length = guide["coat_length"][0]
                    obs["render"].update(coat_length="short" if length=="very_short" else length,collar_visible=False)
                    obs["appearance"]["colors"]={k:palette[v] for k,v in zip(maker.COLORS,
                        ["grey","dark","grey","dark","light","grey","dark","dark","dark","light","white","outline"])}
                    obs["appearance"]["unresolved"]=["hidden surfaces and contacts","unobserved pose proportions","precise joint positions"]
                    if "limitations" in reg:
                        obs["appearance"]["unresolved"].append(reg["limitations"])
                    obs["evidence"]=[
                        dict(kind="photo_observation",fields=["projected contours","visible features","pose"],source=credit["source_page"],
                             note=f"Guide page {page.number+1}; embedded image {match[0]}; pose {reg['pose']}; manually registered visible pixels."),
                        dict(kind="design_default",fields=["geometry","colors","render","occluded joins"],source="guide_registration/landmarks.json",
                             note="Legacy observation-schema defaults are not measurements. Palette, head enlargement and hidden joins are authoring choices."),
                        dict(kind="design_default",fields=["breed guide"],source=f"grouping_322.json#{key}",note=guide["base_reason"])]
                    rev=store.save(obs,0,"Guide photo and breed-table registration")
                    write(folder/"evidence.json",dict(photo=credit,breed_table=guide,pose=reg["pose"],page=page.number+1,
                          xref=match[0],embedded_sha256=maker.digest(source),limitations=reg.get("limitations","사진에 가려진 부위와 관절 위치는 미확인."),
                          modifications="Manual projected contour registration, palette reduction, head styling and ear-fold variations."))
                    base=compile_pose(photo,obs,rev,reg)
                    def variant(item):
                        label,color=item
                        profile=deepcopy(base)
                        profile["details"][0]["color"]=color
                        check_visible_features(profile)
                        spec=folder/(label+".json")
                        write(spec,profile)
                        reader=maker.Store(pending/"profiles.sqlite",read_only=True)
                        try:
                            standing64.export(reader,obs["dog_id"],spec,folder/label)
                        finally:
                            reader.close()
                    with ThreadPoolExecutor(max_workers=3) as pool:
                        list(pool.map(variant,[("A","light"),("B","grey"),("C","dark")]))
                    report=json.loads((folder/"B/review.json").read_text())
                    entries[obs["dog_id"]]=dict(profile=key+"/B.json",rgba_sha256=report["rgba_sha256"],
                        authoring_sha256=report["authoring_sha256"],pose=reg["pose"],status="candidate")
        finally:
            store.close()
        write(pending/"entries.json",entries)
        pending.rename(out)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf",required=True)
    parser.add_argument("--tables",required=True)
    parser.add_argument("--out",required=True)
    args=parser.parse_args()
    register(args.pdf,args.tables,args.out)
