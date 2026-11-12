"""Small authored coat envelopes for one hash-pinned maltipoo structure.

Lengths are prototype envelope offsets, not measured hair lengths. No generic
breed morph, new anatomical structure, or appearance approval is implied.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

SOURCE_SHA256 = "77d56d9ce2454a12d4ac2f9329c1a880414e5cc14da59730816c993213b27133"
ARRAY_SHA256 = "041e83a371ec09a90c65ebf606a9414b54fd6a8f54f4e4770068d9ccde0a92d8"
PARTS = ("head", "eye_-1", "eye_1", "ear_left", "ear_right")
CHANNELS = ("v", "f", "n", "c")
REGIONS = ("crown", "cheeks", "ears", "chest")
OFFSETS = {"short": 0.0, "medium": 2.0, "long": 4.0}
# The rostral cheek has less room between the protected eyes, jaw and free ear.
REGION_GAINS = {"crown": 1.0, "cheeks": .4, "ears": 1.0, "chest": 1.0}


def _array_digest(parts):
    digest = hashlib.sha256()
    for name in sorted(f"{part}_{channel}" for part in PARTS for channel in CHANNELS):
        part, channel = name.rsplit("_", 1)
        value = parts[part][channel]
        digest.update(name.encode())
        digest.update(str(value.dtype).encode())
        digest.update(str(value.shape).encode())
        digest.update(value.tobytes())
    return digest.hexdigest()


def _validate_base(model):
    if not isinstance(model, dict) or model.get("breed") != "maltipoo":
        raise ValueError("Only the pinned maltipoo coat baseline is supported")
    parts = model.get("parts")
    if not isinstance(parts, dict) or set(parts) != set(PARTS):
        raise ValueError("Unsupported coat model parts")
    for key, part in parts.items():
        if not isinstance(part, dict) or set(part) != set(CHANNELS):
            raise ValueError(f"Unsupported channels for {key}")
        for channel in CHANNELS:
            value = part[channel]
            if (not isinstance(value, np.ndarray) or value.dtype.kind not in "fiu"
                    or value.ndim != 2 or value.shape[1] != 3 or not np.isfinite(value).all()):
                raise ValueError(f"Invalid coat array: {key}.{channel}")
    if _array_digest(parts) != ARRAY_SHA256:
        raise ValueError("Coat baseline differs from the pinned source; chained morphs are unsupported")


def load_npz(path):
    """Read only the exact pinned source, never pickle or a caller-selected mesh."""
    import io
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError("Coat source NPZ hash mismatch")
    with np.load(io.BytesIO(raw), allow_pickle=False) as archive:
        expected = {f"{part}_{channel}" for part in PARTS for channel in CHANNELS}
        if set(archive.files) != expected:
            raise ValueError("Unsupported source NPZ channels")
        parts = {part: {channel: archive[f"{part}_{channel}"].copy()
                        for channel in CHANNELS} for part in PARTS}
    model = {"parts": parts, "breed": "maltipoo"}
    _validate_base(model)
    return model


def _smooth(value):
    t = np.clip(value, 0.0, 1.0)
    return t**3 * (t * (t * 6 - 15) + 10)


def _window(value, low, rise, fall, high):
    return _smooth((value - low) / (rise - low)) * _smooth((high - value) / (high - fall))


def _weights(model):
    """Masks are authored for this source's x-caudal, y-up coordinate system."""
    head = model["parts"]["head"]
    vertices, faces = head["v"], head["f"]
    x, y, z = vertices.T
    nose = np.all(head["c"] == [43, 40, 34], axis=1)
    # Protect the black nose and two incident face rings, not only pigment.
    nose_adjacent = nose.copy()
    for _ in range(2):
        nose_adjacent[np.unique(faces[nose_adjacent[faces].any(axis=1)])] = True
    eyes = np.concatenate([model["parts"][k]["v"] for k in ("eye_-1", "eye_1")])
    eye_distance = cKDTree(eyes).query(vertices)[0]
    ear_vertices = np.concatenate([model["parts"][k]["v"] for k in ("ear_left", "ear_right")])
    ear_distance = cKDTree(ear_vertices).query(vertices)[0]
    protection = _smooth((eye_distance - 4) / 4) * _smooth((ear_distance - 3) / 4)
    protection[nose_adjacent] = 0
    # Central crown: no ear-root expansion and no forehead/eye displacement.
    crown = (_window(x, -34, -25, -4, 8) * _smooth((y - 28) / 10)
             * (1 - _smooth((np.abs(z) - 10) / 10)) * protection)
    # Rostral cheek only: stay in front of the free ear and above jaw/throat.
    cheeks = (_window(x, -50, -40, -38, -27) * _window(y, 0, 6, 14, 23)
              * _smooth((np.abs(z) - 8) / 7) * protection)
    # Anterior upper chest, below the jaw-throat transition. Back and shoulder
    # silhouette remain unchanged; this is not a full-body coat operation.
    chest = (_window(y, -65, -53, -37, -25) * (1 - _smooth((x - 2) / 15))
             * (1 - _smooth((np.abs(z) - 14) / 12)) * protection)
    ears = {key: _smooth((15 - model["parts"][key]["v"][:, 1]) / 15)
            for key in ("ear_left", "ear_right")}
    return {"crown": crown, "cheeks": cheeks, "chest": chest, "ears": ears}, {
        "nose_and_adjacent": nose_adjacent,
        "eye_neighborhood": eye_distance <= 4,
        "ear_neighborhood": ear_distance <= 3,
        "jaw_throat": (y <= 0) & (y >= -25),
    }


def _normals_and_quality(before, after, faces, original_normals):
    old_face = np.cross(before[faces[:, 1]] - before[faces[:, 0]],
                        before[faces[:, 2]] - before[faces[:, 0]])
    new_face = np.cross(after[faces[:, 1]] - after[faces[:, 0]],
                        after[faces[:, 2]] - after[faces[:, 0]])
    old_size, new_size = np.linalg.norm(old_face, axis=1), np.linalg.norm(new_face, axis=1)
    if (old_size <= 0).any() or (new_size <= 0).any():
        raise ValueError("Degenerate triangle in coat model")
    cosine = np.sum(old_face * new_face, axis=1) / (old_size * new_size)
    ratio = new_size / old_size
    if float(cosine.min()) < .8 or float(ratio.min()) < .5 or float(ratio.max()) > 2:
        raise ValueError(f"Coat deformation exceeds local orientation/area bounds: "
                         f"cosine={cosine.min()}, ratio={ratio.min()}..{ratio.max()}")
    normals = np.zeros_like(after, dtype=np.float64)
    for index in range(3):
        np.add.at(normals, faces[:, index], new_face)
    normals /= np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1e-12)
    if np.mean(np.sum(normals * original_normals, axis=1)) < 0:
        normals *= -1
    # Preserve unaffected lighting normals exactly; recompute the complete
    # one-ring only where a face actually moved.
    changed = np.any(before != after, axis=1)
    affected = np.unique(faces[changed[faces].any(axis=1)])
    output = original_normals.copy()
    output[affected] = normals[affected]
    return output, {"min_face_orientation_cosine": float(cosine.min()),
                    "min_face_area_ratio": float(ratio.min()),
                    "max_face_area_ratio": float(ratio.max())}


def _ear_clearance(parts):
    tree = cKDTree(parts["head"]["v"])
    return {key: float(tree.query(parts[key]["v"][parts[key]["v"][:, 1] < 20])[0].min())
            for key in ("ear_left", "ear_right")}


def apply_lengths(model, lengths):
    """Return a new model and audit report; the source arrays stay byte-identical.

    Omitted regions keep the baseline (short). Short means no added envelope,
    not a measured short haircut. Input must always be the unmodified baseline.
    """
    _validate_base(model)
    if not isinstance(lengths, dict) or set(lengths) - set(REGIONS):
        raise ValueError("Unsupported coat length regions")
    if any(not isinstance(value, str) or value not in OFFSETS for value in lengths.values()):
        raise ValueError("Coat length must be short, medium or long")
    selection = {key: lengths.get(key, "short") for key in REGIONS}
    result = copy.deepcopy(model)
    weights, protected = _weights(model)
    vertices = model["parts"]["head"]["v"]
    x, _, z = vertices.T
    directions = {
        "crown": np.column_stack([.15 * np.clip((x + 18) / 15, -1, 1), np.ones(len(x)), .15 * z / 20]),
        "cheeks": np.column_stack([np.full(len(x), -.15), np.zeros(len(x)), np.sign(z)]),
        "chest": np.column_stack([-np.ones(len(x)), np.zeros(len(x)), .15 * z / 20]),
    }
    shift = np.zeros_like(vertices, dtype=np.float64)
    for key, direction in directions.items():
        direction /= np.linalg.norm(direction, axis=1)[:, None]
        shift += direction * (OFFSETS[selection[key]] * REGION_GAINS[key] * weights[key])[:, None]
    result["parts"]["head"]["v"] = (vertices + shift).astype(vertices.dtype)
    for key in ("ear_left", "ear_right"):
        result["parts"][key]["v"][:, 1] -= OFFSETS[selection["ears"]] * weights["ears"][key]
    changes = {}
    for key in ("head", "ear_left", "ear_right"):
        old, new = model["parts"][key], result["parts"][key]
        delta = np.linalg.norm(new["v"] - old["v"], axis=1)
        quality = {}
        if np.any(delta):
            new["n"], quality = _normals_and_quality(old["v"], new["v"], old["f"], old["n"])
        changes[key] = {"changed_vertices": int(np.count_nonzero(delta)),
                        "max_displacement_model_units": float(delta.max()), **quality}
    old_clearance, new_clearance = _ear_clearance(model["parts"]), _ear_clearance(result["parts"])
    if any(new_clearance[key] < old_clearance[key] - .01 for key in old_clearance):
        raise ValueError("Coat deformation reduced sampled free-ear clearance")
    for name, mask in protected.items():
        if not np.array_equal(vertices[mask], result["parts"]["head"]["v"][mask]):
            raise ValueError(f"Coat deformation moved protected {name}")
    return result, {
        "schema_version": 1, "source_model_sha256": SOURCE_SHA256,
        "source_array_sha256": ARRAY_SHA256, "lengths": selection,
        "envelope_offsets_model_units": {key: OFFSETS[value] for key, value in selection.items()},
        "region_gains": REGION_GAINS.copy(),
        "changes": changes, "protection": {key: int(mask.sum()) for key, mask in protected.items()},
        "free_ear_vertex_clearance_before": old_clearance,
        "free_ear_vertex_clearance_after": new_clearance,
        "status": "TECHNICAL_GEOMETRY_ONLY_NOT_VISUAL_APPROVAL",
        "limitations": ["One pinned authored maltipoo head/neck/upper-thorax source only.",
                        "Offsets are envelope model units, not physical hair length or density.",
                        "Clearance is sampled vertex distance, not a global surface collision proof.",
                        "No full-body, coat texture, independent fullness or grooming-style morph.",
                        "New geometry and native64 appearance need independent visual/technical review."],
    }
