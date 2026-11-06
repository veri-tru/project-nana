"""Build a portable comparison of the 27 supplied guide photographs and native outputs."""
import argparse
import base64
import html
import json
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

POSES = dict(stand="서기",walk="걷는 순간",seated="앉음",lying="누움",portrait="얼굴 사진")
OLD = {"054":"whippet","016":"dachshund"}

def inline(image):
    stream=BytesIO()
    image.save(stream,format="PNG")
    return "data:image/png;base64,"+base64.b64encode(stream.getvalue()).decode()

def build(folder):
    new = sorted(folder.glob("*/evidence.json"))
    items = []
    notes = {}
    for file in new:
        ev=json.loads(file.read_text(encoding="utf-8"))
        notes[ev["photo"]["photo_id"]] = ev.get("limitations","")
        items.append((ev["photo"],ev["pose"],file.parent/"source-image",
                      [(k,file.parent/k/"standing.png") for k in "ABC"]))
    pair=folder.parent/"breed-standing-pair-v1"
    credits=json.loads((pair/"credits.json").read_text(encoding="utf-8"))
    for credit in credits["photos"]:
        breed=OLD[credit["photo_id"]]
        items.append((credit,"stand",pair/(breed+"-source.png"),[("확인본",pair/"muzzle-r4"/breed/"middle/standing.png")]))
    items.sort(key=lambda item:(item[0]["group_code"],item[0]["position_in_group"]))
    font=lambda n:ImageFont.truetype("C:/Windows/Fonts/malgun.ttf",n)
    sections=[]
    for index,(credit,pose,source,files) in enumerate(items):
        key=credit["photo_id"]
        name=credit["breed_ko"]
        title=f"{key} {name} · {POSES[pose]}"
        photo=Image.open(source).convert("RGB")
        photo.thumbnail((136,118))
        images=[(k,Image.open(path).convert("RGBA")) for k,path in files]
        middle=images[len(images)//2][1]
        if index%9==0:
            sheet=Image.new("RGB",(990,675),"#faf7f1")
            pen=ImageDraw.Draw(sheet)
            pen.text((15,8),f"가이드 개체 비교    {index//9+1} / 3",font=font(22),fill="#343138")
        x=14+329*(index%3)
        y=47+207*((index%9)//3)
        pen.text((x,y),title,font=font(15),fill="#383139")
        sheet.paste(photo,(x,y+31))
        large=middle.resize((128,128),Image.Resampling.NEAREST)
        sheet.paste(large,(x+153,y+21),large)
        pen.text((x,y+155),credit['author'][:28]+" · "+credit["license"],font=font(10),fill="#564e4c")
        pen.line((x,y+188,x+301,y+188),fill="#dad3cb")
        if index%9==8:
            sheet.save(folder/f"group-{index//9+1}.png")
        cards=[]
        for label,image in images:
            data=inline(image)
            cards.append(f'<div>{label}<br><img class="sprite" width="128" height="128" src="{data}"><br><img class="sprite" width="64" height="64" src="{data}"></div>')
        sections.append(f'<section><h2>{html.escape(title)}</h2><p>{html.escape(notes.get(key,""))}</p><article><img src="{inline(photo)}">' +
                        ''.join(cards)+'</article><p>'+html.escape(credit['attribution'])+
                        '<br>사진을 참고해 윤곽 등록, 픽셀 작화 및 팔레트 축소. <a href="'+
                        html.escape(credit['license_url'],quote=True)+'">원본 라이선스</a></p></section>')
    (folder/'index.html').write_text('''<!doctype html><html lang="ko"><meta charset=utf-8><title>가이드 27개체 비교</title>
<style>body{background:#faf7f1;color:#383239;font:16px system-ui;max-width:980px;margin:2em auto;padding:0 16px}section{border-top:1px solid #ccc;padding:1em 0}article{display:flex;align-items:center;gap:20px;flex-wrap:wrap}article div{text-align:center}.sprite{image-rendering:pixelated}p{font-size:13px;overflow-wrap:anywhere}</style>
<h1>가이드 27개체</h1><p>사진에서 보이는 자세를 기준으로 했습니다. 휘핏과 닥스훈트는 확인한 복구본입니다. 나머지 25개체는 귀 안쪽 선의 농도만 바꾼 A·B·C이며 B는 작업 기준입니다. 각 그림은 2배와 원본 크기입니다.</p>'''+''.join(sections)+'</html>',encoding='utf-8')

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder",type=Path)
    build(parser.parse_args().folder)
