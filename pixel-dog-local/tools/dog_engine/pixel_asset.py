"""Reproduce an authored 64x64 index grid; never infer anatomy from a photo."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw

VERSION = "authored-index64-v1"


def load_asset(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("format") != VERSION:
        raise ValueError("Unsupported pixel asset format")
    rows = data.get("rows")
    if (not isinstance(rows, list) or len(rows) != 64 or
            any(not isinstance(row, str) or len(row) != 64 or
                set(row) - set("012345") for row in rows)):
        raise ValueError("Expected 64 rows of 64 palette indices 0..5")
    if set("".join(rows)) == {"0"}:
        raise ValueError("Empty pixel asset")
    palettes = data.get("palettes")
    if not isinstance(palettes, dict) or not palettes:
        raise ValueError("Missing palettes")
    for key, colors in palettes.items():
        if (not key or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in key)
                or not isinstance(colors, list) or len(colors) != 5):
            raise ValueError("Palettes require a safe name and five opaque RGB colors")
        try:
            rgb = [ImageColor.getrgb(c) for c in colors]
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid palette color") from exc
        if any(len(c) != 3 for c in rgb) or len(set(rgb)) != 5:
            raise ValueError("Expected five distinct RGB colors")
    return data


def render(data, variant):
    colors = [ImageColor.getrgb(c) for c in data["palettes"][variant]]
    result = Image.new("P", (64, 64))
    result.putpalette([0, 0, 0] + [n for color in colors for n in color] + [0] * 750)
    result.putdata([int(n) for row in data["rows"] for n in row])
    result.info["transparency"] = 0
    return result


def export(asset, output):
    asset, output = Path(asset).resolve(), Path(output).resolve()
    data = load_asset(asset)
    if output.exists():
        raise ValueError("Use a new output directory; reviewed outputs are immutable")
    output.mkdir(parents=True)
    variants = list(data["palettes"])
    board = Image.new("RGB", (640 * len(variants), 690), "#e8e5e0")
    pen = ImageDraw.Draw(board)
    files = []
    for index, name in enumerate(variants):
        native = render(data, name)
        path = output / (name + ".png")
        native.save(path, bits=8, transparency=0, optimize=False)
        files.append(path)
        rgba = native.convert("RGBA")
        large = rgba.resize((512, 512), Image.Resampling.NEAREST)
        preview = output / (name + "-8x.png")
        large.save(preview)
        files.append(preview)
        x = index * 640
        pen.text((x + 32, 16), name + " | 64 x 64 / 1x", fill="#383b42")
        board.paste(rgba, (x + 288, 42), rgba)
        pen.text((x + 32, 124), "8x nearest | same geometry", fill="#383b42")
        board.paste(large, (x + 64, 154), large)
    board_path = output / "comparison.png"
    board.save(board_path)
    files.append(board_path)
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    record = {"renderer": VERSION, "asset": str(asset), "asset_sha256": digest(asset),
              "renderer_sha256": digest(Path(__file__)), "native_size": [64, 64],
              "png_bit_depth": 8, "png_color_type": 3, "transparent_index": 0,
              "opaque_colors": 5, "palette_only_variants": variants,
              "user_decision": "PENDING", "review_status": "NOT_REVIEWED",
              "artifacts": {p.name: digest(p) for p in files}}
    (output / "render-record.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(export(args.asset, args.output_dir), indent=2))
    return 0
