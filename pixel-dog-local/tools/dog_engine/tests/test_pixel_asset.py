"""Native-grid export contract, including PNG encoding and lossless preview."""
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from tools.dog_engine import pixel_asset


class PixelAssetTests(unittest.TestCase):
    def fixture(self, folder):
        rows = ["0" * 64 for _ in range(64)]
        rows[30] = "0" * 29 + "12345" + "0" * 30
        data = {"format": pixel_asset.VERSION, "rows": rows, "palettes": {
            "a": ["#383b42", "#606570", "#949ba7", "#cbd0d6", "#f3f0e8"],
            "b": ["#383b42", "#707581", "#9ba2ad", "#d3d7db", "#f3f0e8"]}}
        path = folder / "asset.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path, data

    def test_indexed_encoding_transparency_and_exact_preview(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            path, _ = self.fixture(folder)
            pixel_asset.export(path, folder / "out")
            raw = (folder / "out/a.png").read_bytes()
            self.assertEqual(raw[24:26], bytes([8, 3]))
            with Image.open(folder / "out/a.png") as a, Image.open(folder / "out/b.png") as b:
                self.assertEqual(a.size, (64, 64))
                self.assertEqual(a.mode, "P")
                self.assertEqual(a.tobytes(), b.tobytes())
                rgba = a.convert("RGBA")
                self.assertEqual(rgba.getpixel((0, 0))[3], 0)
                self.assertEqual(rgba.getpixel((29, 30))[3], 255)
                with Image.open(folder / "out/a-8x.png") as preview:
                    self.assertEqual(preview.tobytes(), rgba.resize((512, 512), Image.Resampling.NEAREST).tobytes())

    def test_replay_and_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            path, _ = self.fixture(folder)
            first = pixel_asset.export(path, folder / "first")
            second = pixel_asset.export(path, folder / "second")
            self.assertEqual(first["artifacts"], second["artifacts"])
            with self.assertRaises(ValueError):
                pixel_asset.export(path, folder / "first")

    def test_invalid_grid_palette_and_path_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            path, original = self.fixture(folder)
            for mutation in ("bad-index", "bad-width", "duplicate-color", "path-name"):
                data = json.loads(json.dumps(original))
                if mutation == "bad-index": data["rows"][0] = "6" * 64
                if mutation == "bad-width": data["rows"][0] = "0" * 63
                if mutation == "duplicate-color": data["palettes"]["a"][1] = data["palettes"]["a"][0]
                if mutation == "path-name": data["palettes"]["../escape"] = data["palettes"]["a"]
                path.write_text(json.dumps(data), encoding="utf-8")
                with self.assertRaises(ValueError, msg=mutation):
                    pixel_asset.export(path, folder / "out")
                self.assertFalse((folder / "out").exists())


if __name__ == "__main__":
    unittest.main()
