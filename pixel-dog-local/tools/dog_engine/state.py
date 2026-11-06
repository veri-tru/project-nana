"""Read current policy and artifact-bound selections without loading renderers."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def selection(folder):
    record = read(f"outputs/{folder}/selection.json")
    artifact = ROOT / "outputs" / folder / record["artifact"]
    if hashlib.sha256(artifact.read_bytes()).hexdigest() != record["sha256"]:
        raise ValueError(f"Selected artifact changed: {artifact}")
    return {key: record[key] for key in
            ("selected_variant", "geometry_reference", "style_id", "scope")}


def current():
    project = read("config/project.json")
    catalog = read("tools/head_engine/catalog.json")
    rejected = read("outputs/golden-pixel-refresh-20261106/review-status.json")
    ears = read("outputs/jack-russell-ear-study-20261106/review-status.json")
    return {
        "canonical_head_style": project["art_style"]["selected_head_style_id"],
        "geometry_defaults": {key: value["default_preset"] for key, value in catalog["breeds"].items()},
        "geometry_selection": "WORKING_DEFAULT_USER_REVIEW_PENDING",
        "concept_selections": {
            "golden": selection("golden-b2-canonical-20261106"),
            "jack_russell": selection("jack-russell-b2-20261106"),
        },
        "native64_head": {"source_user_decision": rejected["user_decision"],
                          "delivery": rejected["delivery"], "active_route": "diagnostic_only"},
        "individual_ears": {"implemented": False, "concept_selection": ears["user_decision"]},
        "full_body": {"renderer": "tools/static_maker/standing64.py", "format": "2D_authored_profile",
                      "native_canvas_px": [64, 64], "connected_to_head_mesh": False},
        "animation": "NOT_IMPLEMENTED", "mobile_app": "NOT_IMPLEMENTED",
    }


def doctor():
    import importlib.metadata
    import sys
    from . import head
    problems = []
    for row in (Path(__file__).parent / "requirements.txt").read_text().splitlines():
        if not row or row.startswith("#"):
            continue
        package, expected = row.split("==")
        try:
            actual = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            actual = "MISSING"
        if actual != expected:
            problems.append(f"{package}: expected {expected}, got {actual}")
    if sys.version_info[:2] != (3, 12):
        problems.append("Checkpoint regression environment requires Python 3.12")
    catalog = head.catalog()
    for preset, spec in catalog["presets"].items():
        request = {"schema_version": 1, "breed": spec["breed"], "size_class": "medium",
                   "display": {"mode": "normalized", "scene_scale": 3.2},
                   "individual": {"id": "doctor", "overrides": {"geometry_preset": preset},
                                  "evidence": {"geometry_preset": {"kind": "authored_default",
                                               "source": "catalog", "note": "Read-only integrity check"}}}}
        try:
            head.verify_source(head.resolve_profile(request))
        except (OSError, ValueError, KeyError) as exc:
            problems.append(f"{preset}: {exc}")
    try:
        status = current()
        if status["canonical_head_style"] != "breed-head-soft-B2-v1":
            problems.append("Current head style conflicts with the approved B2 manifest")
    except (OSError, ValueError, KeyError) as exc:
        problems.append(f"Current state: {exc}")
    return {"environment_and_sources": "PASS" if not problems else "FAIL", "problems": problems,
            "scope": "Local dependencies and source integrity; not visual approval or portable-clone certification"}
