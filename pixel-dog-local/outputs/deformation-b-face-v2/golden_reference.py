"""Place visible features of the public-domain source beside the neutral rig profile."""
import json
import runpy
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
PHOTO = HERE.parents[1] / "private-data/guide-roster/002/source.jpg"
BG, INK, TEAL = "#F8F6F0", "#293E38", "#256C60"
board = Image.new("RGB", (1140, 624), BG)
draw = ImageDraw.Draw(board)


def text(x, y, value, size=16, bold=False, color=INK):
    font = ImageFont.truetype("C:/Windows/Fonts/malgun" + ("bd" if bold else "") + ".ttf", size)
    draw.text((x, y), value, font=font, fill=color, anchor="lt")


def path(points, color, width=2):
    draw.line(points, fill=color, width=width, joint="curve")


text(36, 22, "NANA    /    BREED REFERENCE     002", 13, True, TEAL)
text(34, 51, "골든 리트리버의 옆얼굴", 35, True)
text(36, 108, "원사진에서 확인할 수 있는 네 곳을 B 압축형의 측면 기준점과 나란히 놓았다.", 17)
text(36, 160, "01    원사진 확대", 19, True)
text(610, 160, "02    수정 B의 얼굴 기준점", 19, True)
crop = (440, 10, 650, 158)
photo = Image.open(PHOTO).crop(crop).resize((452, 318), Image.Resampling.LANCZOS)
board.paste(photo, (36, 198))
model = json.loads((HERE / "B.json").read_text(encoding="utf-8"))
world = runpy.run_path(str(HERE.parent / "integrated-rig-b-v1/build.py"))["world_pose"](model["breeds"]["golden"])
origin = world["face.nose"]


def xy(name):
    x, y, _ = world["face." + name]
    return (1026 - (x - origin[0]) * 10.7, 301 - (y - origin[1]) * 10.7)


def chain(names):
    return [xy(k) for k in names.split()]


# Polygons use the same projected landmarks as the JSON. Color separates regions.
for names, fill in [
    ("occiput crown L_brow stop nose nose_bottom upper_lip chin L_jaw_side L_cheek neck_mount", "#ECD9AD"),
    ("stop nose nose_bottom upper_lip L_mouth_corner L_muzzle_side", "#DCB989"),
    ("L_mouth_corner upper_lip chin L_jaw_side", "#C99F71"),
]:
    pts = chain(names)
    draw.polygon(pts, fill=fill)
    path(pts + pts[:1], "#82755E", 2)
path(chain("L_ear_root L_ear_fold L_ear_tip"), TEAL, 4)
path(chain("L_eye stop nose"), "#A58A59", 2)
for name in ("crown", "occiput", "L_eye", "L_ear_fold", "L_ear_tip", "chin"):
    x, y = xy(name)
    draw.ellipse((x-3, y-3, x+3, y+3), fill=INK)

features = [
    ("L_ear_root", (513, 41), "귀뿌리"),
    ("stop", (578, 54), "이마와 콧등의 경계"),
    ("nose", (626, 62), "코"),
    ("L_mouth_corner", (559, 104), "입꼬리"),
]
for i, (name, pos, label) in enumerate(features, 1):
    photo_point = 36 + (pos[0]-crop[0])*452/210, 198 + (pos[1]-crop[1])*318/148
    for px, py in (photo_point, xy(name)):
        draw.ellipse((px-8, py-8, px+8, py+8), fill=TEAL, outline="white", width=1)
        f = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 10)
        draw.text((px, py), str(i), font=f, anchor="mm", fill="white")
    text(610 + (i-1)%2*203, 432+(i-1)//2*32, f"0{i}   {label}", 16)
draw.line((36, 536, 1104, 536), fill="#C5CDC4")
text(36, 551, "사진은 입을 벌린 순간이다. 오른쪽은 닫힌 입의 작화 좌표이며, 번호는 대응하는 부위를 가리킨다.", 15)
text(36, 592, "사진  Janneke Vreugdenhil · Anka Friedrich, Wikimedia Commons, Public domain  /  사진 일부 확대", 12, color="#586B62")
board.save(HERE / "golden-reference.png")
