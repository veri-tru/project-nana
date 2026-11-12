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


def individual_pair_selection():
    record = read("config/individual-pair-canonical.json")
    artifact = ROOT / record["artifact"]
    selection_path = ROOT / record["selection_record"]
    for path, expected in ((artifact, record["sha256"]),
                           (selection_path, record["selection_sha256"])):
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Individual pair selection changed: {path}")
    source = json.loads(selection_path.read_text(encoding="utf-8"))
    for key in ("status", "canonical_id", "selected_variant", "selected_rows", "views",
                "sha256", "style_id", "geometry_reference", "scope"):
        if record[key] != source[key]:
            raise ValueError(f"Individual pair selection conflicts: {key}")
    if (selection_path.parent / source["artifact"]).resolve() != artifact.resolve():
        raise ValueError("Individual pair selected artifact path conflicts")
    from tools.review.check_delivery import check
    review_path = artifact.parent / "review-status.json"
    errors = check(review_path)
    if errors:
        raise ValueError("Individual pair review blocked: " + "; ".join(errors))
    review = json.loads(review_path.read_text(encoding="utf-8"))
    if record["status"] != "USER_ACCEPTED" or review.get("user_decision") != "ACCEPTED":
        raise ValueError("Individual pair user acceptance conflicts with review record")
    return record


def coat_support():
    registry = read("tools/dog_engine/coat-head-models.json")
    return {
        "registered_head_models": {
            key: {"geometry_version": spec["geometry_version"],
                  "length_regions": spec["length_regions"],
                  "fullness_3d_regions": spec.get("volume_regions", []),
                  "fullness_native64_regions": spec.get("native_volume_regions", [])}
            for key, spec in registry["models"].items()
        },
        "native64_route": "REVIEW_GATED_NEUTRAL_DIAGNOSTIC",
        "b2_native64_style_approved": False,
        "unsupported": ["cheek_fullness", "ear_fullness", "texture", "named_grooming_shapes"],
        "latest_result_record": "docs/coat-chest-tone-fix.md",
    }


def current():
    project = read("config/project.json")
    catalog = read("tools/head_engine/catalog.json")
    rejected = read("outputs/golden-pixel-refresh-20261106/review-status.json")
    ears = read("outputs/jack-russell-ear-study-20261106/review-status.json")
    pair = individual_pair_selection()
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
        "individual_ears": {"implemented": False, "concept_selection": ears["user_decision"],
                            "structure_experiment": "ear-structure: separate maltipoo head/left/right ear meshes",
                            "catalog_connected": False, "native64_connected": False},
        "anatomy_appearance_gate": {"command": "structure-gate", "required_scope": "head_neck_shoulders",
                                    "short_neck_reference_sufficient": False,
                                    "latest_pair_art": pair["canonical_id"],
                                    "latest_pair_art_status": pair["status"],
                                    "neck_structure": "REFERENCE02_REVIEWED_FOR_APPEARANCE_NOT_CATALOG_DEFAULT"},
        "individual_pair_canonical": pair,
        "coat": coat_support(),
        "full_body": {"renderer": "tools/static_maker/standing64.py", "format": "2D_authored_profile",
                      "native_canvas_px": [64, 64], "connected_to_head_mesh": False},
        "animation": "NOT_IMPLEMENTED", "mobile_app": "NOT_IMPLEMENTED",
    }


def pinned_requirements(path):
    for row in path.read_text(encoding="utf-8").splitlines():
        row = row.strip()
        if not row or row.startswith("#"):
            continue
        if row.startswith("-r "):
            yield from pinned_requirements(path.parent / row[3:].strip())
        else:
            yield row.split("==")


def doctor():
    import importlib.metadata
    import sys
    problems = []
    for package, expected in pinned_requirements(Path(__file__).with_name("verification-lock.txt")):
        try:
            actual = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            actual = "MISSING"
        if actual != expected:
            problems.append(f"{package}: expected {expected}, got {actual}")
    if sys.version_info[:2] != (3, 12):
        problems.append("Checkpoint regression environment requires Python 3.12")
    if problems:
        return {"environment_and_sources": "FAIL", "problems": problems,
                "remedy": r"Use .\engine.ps1 -Setup, then .\engine.ps1 doctor",
                "scope": "Dependency check failed before loading checkpoint renderers"}
    from . import head
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
