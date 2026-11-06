"""Resolve size-class -> breed -> individual settings and render reviewed heads.

Only catalogued, hash-pinned local models are deserialized. No source generator
is run and no anatomical dimensions are inferred from a display size class.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import pickle
import sys

import numpy as np
from PIL import Image

from . import renderer

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CATALOG = ROOT / "tools/head_engine/catalog.json"
RUNTIME_INPUTS = HERE / "runtime-inputs.json"
VIEWS = [("측면", 90, 0), ("사선", 48, 7), ("정면", 0, 0),
         ("후면", 180, 0), ("윗면", 90, 90)]
TARGET_EXTENT = 320.0
CELL_SIZE = (440.0, 340.0)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    def duplicate_safe(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(Path(path).read_text("utf-8"), object_pairs_hook=duplicate_safe)


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                    allow_nan=False) + "\n", "utf-8")


def object_keys(value, allowed, required, name):
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    unknown = set(value) - set(allowed)
    missing = set(required) - set(value)
    if unknown or missing:
        raise ValueError(f"{name}: unknown={sorted(unknown)}, missing={sorted(missing)}")


def text_value(value, name):
    if not isinstance(value, str) or not value.strip() or len(value) > 500:
        raise ValueError(f"{name} must be a nonempty string of at most 500 characters")
    return value


def number(value, name, low, high):
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"{name} must be finite and between {low} and {high}")
    return float(value)


def catalog():
    return read_json(CATALOG)


def resolve_profile(request):
    """The request has no arbitrary source paths or unrestricted mesh overrides."""
    object_keys(request, ["schema_version", "size_class", "breed", "individual", "display"],
                ["schema_version", "size_class", "breed", "display"], "profile")
    if type(request["schema_version"]) is not int or request["schema_version"] != 1:
        raise ValueError("Unsupported profile schema_version")
    c = catalog()
    size_class = text_value(request["size_class"], "size_class")
    breed = text_value(request["breed"], "breed")
    if size_class not in c["size_classes"] or breed not in c["breeds"]:
        raise ValueError("Unknown size_class or breed")
    # Size affects only relative display scale; breed supplies geometry.
    values = dict(c["size_classes"][size_class])
    provenance = {"relative_scale": {"layer": "size_class", "kind": "authored_default",
                                      "source": f"catalog.size_classes.{size_class}"}}
    values["geometry_preset"] = c["breeds"][breed]["default_preset"]
    provenance["geometry_preset"] = {"layer": "breed", "kind": "reviewed_working_preset",
                                       "source": f"catalog.breeds.{breed}"}
    individual = request.get("individual", {"id": "unspecified", "overrides": {}, "evidence": {}})
    object_keys(individual, ["id", "overrides", "evidence"], ["id", "overrides", "evidence"], "individual")
    text_value(individual["id"], "individual.id")
    overrides, evidence = individual["overrides"], individual["evidence"]
    object_keys(overrides, ["relative_scale", "geometry_preset"], [], "individual.overrides")
    object_keys(evidence, overrides, overrides, "individual.evidence")
    for key, value in overrides.items():
        ev = evidence[key]
        object_keys(ev, ["kind", "source", "note"], ["kind", "source", "note"], f"evidence.{key}")
        if ev["kind"] not in ("authored_default", "owner_report", "observed_input"):
            raise ValueError("Evidence kind must be authored_default, owner_report or observed_input")
        text_value(ev["source"], "evidence.source")
        text_value(ev["note"], "evidence.note")
        values[key] = value
        provenance[key] = {"layer": "individual", **ev}
    values["relative_scale"] = number(values["relative_scale"], "relative_scale", 0.1, 3.0)
    preset_id = text_value(values["geometry_preset"], "geometry_preset")
    if preset_id not in c["presets"] or c["presets"][preset_id]["breed"] != breed:
        raise ValueError("geometry_preset must be a catalogued preset of the selected breed")
    display = request["display"]
    object_keys(display, ["mode", "scene_scale"], ["mode", "scene_scale"], "display")
    if display["mode"] not in ("normalized", "relative"):
        raise ValueError("display.mode must be normalized or relative; actual-size is unsupported")
    scene_scale = number(display["scene_scale"], "scene_scale", 0.1, 10.0)
    return {
        "schema_version": 1, "catalog_sha256": sha(CATALOG),
        "request": request, "breed": breed, "size_class": size_class,
        "individual_id": individual["id"], "values": values,
        "provenance": provenance, "source": c["presets"][preset_id],
        "display": {"mode": display["mode"], "scene_scale": scene_scale,
                    "normalized_max_extent_px": TARGET_EXTENT,
                    "relative_scale_applied": display["mode"] == "relative",
                    "units": "authored_model_units_not_cm"},
        "selection": "WORKING_DEFAULT_USER_REVIEW_PENDING",
        "limitations": ["Size classes do not select skull geometry or infer weight.",
                        "Relative scale is authored display scale, not measured physical size.",
                        "Individual evidence is recorded, not independently authenticated.",
                        "No new skeleton, pose, animation or native pixel asset is generated."]}


def validate_resolved(resolved):
    if not isinstance(resolved, dict) or "request" not in resolved:
        raise ValueError("Resolved profile lacks its original request")
    if resolved != resolve_profile(resolved["request"]):
        raise ValueError("Resolved profile was edited or catalog changed; resolve it again")


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def verify_source(resolved):
    validate_resolved(resolved)
    c = catalog()
    for relative, expected in read_json(RUNTIME_INPUTS).items():
        if sha(ROOT / relative) != expected:
            raise ValueError(f"Active renderer dependency changed: {relative}")
    for relative, expected in c["renderer_inputs"].items():
        if sha(ROOT / relative) != expected:
            raise ValueError(f"Renderer dependency changed: {relative}")
    source = resolved["source"]
    for field, hash_field in [("path", "sha256"), ("review_status", "review_status_sha256")]:
        if sha(ROOT / source[field]) != source[hash_field]:
            raise ValueError(f"Reviewed source changed: {source[field]}")
    status_path = ROOT / source["review_status"]
    status = read_json(status_path)
    check = module(ROOT / "tools/review/check_delivery.py", "head_engine_delivery_check")
    problems = check.check(status_path)
    if problems:
        raise ValueError("Source review is blocked: " + "; ".join(problems))
    relative_model = os.path.relpath(ROOT / source["path"], status_path.parent).replace("\\", "/")
    if status["inputs"].get(relative_model) != source["sha256"]:
        raise ValueError("Selected model is not covered by its source review")
    return status


def load_model(resolved):
    verify_source(resolved)
    source = resolved["source"]
    # The path/hash are selected from the pinned catalog, never from user input.
    result = pickle.loads((ROOT / source["path"]).read_bytes())
    for key in source["selector"]:
        result = result[key]
    if result["breed"] != resolved["breed"]:
        raise ValueError("Model breed does not match the resolved profile")
    return result


def projection_plan(resolved, projected_bounds):
    """One scale per five-view head, so view-to-view proportions are retained."""
    bounds = np.asarray(projected_bounds, dtype=float)
    if bounds.shape != (5, 2) or not np.isfinite(bounds).all() or (bounds <= 0).any():
        raise ValueError("Five finite positive projected bounds are required")
    display = resolved["display"]
    if display["mode"] == "normalized":
        scale = display["normalized_max_extent_px"] / float(bounds.max())
    else:
        scale = display["scene_scale"] * resolved["values"]["relative_scale"]
    pixel_bounds = bounds * scale
    if (pixel_bounds > np.array(CELL_SIZE)).any():
        raise ValueError("Relative view exceeds the cell; reduce scene_scale. No automatic rescaling was applied.")
    return {"pixels_per_model_unit": scale, "projected_bounds_model_units": bounds.tolist(),
            "projected_bounds_px": pixel_bounds.tolist(), "mode": display["mode"],
            "normalized_max_extent_px": display["normalized_max_extent_px"]}


def render_resolved(resolved):
    model = load_model(resolved)
    projections = [renderer.projected(model, az, el) for _, az, el in VIEWS]
    bounds = [np.ptp(q[:, :, :2], axis=(0, 1)) for q, _ in projections]
    plan = projection_plan(resolved, bounds)
    scale = plan["pixels_per_model_unit"]
    image = Image.new("RGB", (2400, 650), (248, 247, 242))
    breed_name = catalog()["breeds"][resolved["breed"]]["display_name"]
    renderer.label(image, 28, 22, f"{breed_name} · 머리 엔진 작업 참조", 34, True)
    mode_label = "비율 비교 / 공통 최대 bbox" if plan["mode"] == "normalized" else "상대 크기 표시 / 공통 제작 단위"
    renderer.label(image, 28, 76, f"{resolved['values']['geometry_preset']} · {mode_label} · 사용자 선택 대기", 21)
    for j, ((name, _, _), (q, colors)) in enumerate(zip(VIEWS, projections)):
        renderer.label(image, 28 + j * 480, 140, name, 23, True)
        low, high = q[:, :, :2].min((0, 1)), q[:, :, :2].max((0, 1))
        center = np.array([j * 480 + 240, 365]) - (low + high) / 2 * np.array([scale, -scale])
        renderer.paint(image, q, colors, center, scale)
    renderer.label(image, 28, 592, "같은 저장 모델의 실제 5시점 · 실측 크기 아님 · 픽셀 재작화 전", 21)
    return image, plan


def ensure_new_target(path):
    path = Path(path).resolve()
    outputs = (ROOT / "outputs").resolve()
    if not path.is_relative_to(outputs):
        raise ValueError("Render output must be inside this project's outputs directory")
    # A new artifact cannot be written into a folder holding an existing review.
    for ancestor in [path, *path.parents]:
        if ancestor == outputs:
            break
        if (ancestor / "review-status.json").exists():
            raise ValueError("Use a new output folder; an existing review-status.json is protected")
    for name in ["engine-reference.png", "engine-render.json", "engine-inputs.json"]:
        if (path / name).exists():
            raise ValueError(f"Refusing to overwrite existing artifact: {path / name}")
    return path


def render_file(resolved_path, output_dir):
    target = ensure_new_target(output_dir)
    resolved_path = Path(resolved_path).resolve()
    resolved = read_json(resolved_path)
    image, plan = render_resolved(resolved)
    # Resolve/verify all inputs before writing any image.
    status_path = ROOT / resolved["source"]["review_status"]
    status = read_json(status_path)
    inputs = {HERE / "head.py": sha(HERE / "head.py"), CATALOG: sha(CATALOG),
              RUNTIME_INPUTS: sha(RUNTIME_INPUTS),
              resolved_path: sha(resolved_path), status_path: sha(status_path),
              ROOT / resolved["source"]["path"]: resolved["source"]["sha256"]}
    for relative, digest in read_json(RUNTIME_INPUTS).items():
        inputs[ROOT / relative] = digest
    for relative, digest in catalog()["renderer_inputs"].items():
        inputs[ROOT / relative] = digest
    for relative, digest in status["inputs"].items():
        inputs[(status_path.parent / relative).resolve()] = digest
    for role in ["technical", "visual"]:
        review = status["reviews"][role]
        inputs[(status_path.parent / review["report"]).resolve()] = review["report_sha256"]
    for path, digest in inputs.items():
        if sha(path) != digest:
            raise ValueError(f"Source changed during rendering: {path}")
    target.mkdir(parents=True, exist_ok=True)
    image.save(target / "engine-reference.png")
    write_json(target / "engine-render.json", {"source_model_sha256": resolved["source"]["sha256"],
                                             "geometry_preset": resolved["values"]["geometry_preset"],
                                             "views": VIEWS, "projection": plan,
                                             "source_user_decision": status["user_decision"],
                                             "output_user_decision": "PENDING"})
    write_json(target / "engine-inputs.json", {
        "artifacts": {"engine-reference.png": sha(target / "engine-reference.png")},
        "inputs": {os.path.relpath(path, target).replace("\\", "/"): digest
                   for path, digest in sorted(inputs.items(), key=lambda pair: str(pair[0]))},
        "render_record": {"engine-render.json": sha(target / "engine-render.json")}})
    return target / "engine-reference.png"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    resolve = commands.add_parser("resolve")
    resolve.add_argument("--profile", type=Path, required=True)
    resolve.add_argument("--output", type=Path, required=True)
    render = commands.add_parser("render")
    render.add_argument("--resolved", type=Path, required=True)
    render.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "resolve":
            result = resolve_profile(read_json(args.profile))
            verify_source(result)
            target = args.output.resolve()
            if target.exists():
                raise ValueError("Refusing to overwrite an existing resolved profile")
            if not target.is_relative_to((ROOT / "outputs").resolve()):
                raise ValueError("Resolved output must be inside this project's outputs directory")
            ensure_new_target(target.parent)
            target.parent.mkdir(parents=True, exist_ok=True)
            write_json(target, result)
            print(target)
        else:
            print(render_file(args.resolved, args.output_dir))
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(2, f"head_engine: {exc}\n")


if __name__ == "__main__":
    main()
