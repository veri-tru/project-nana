"""Rounded coat envelopes with separate length and visible-fullness controls.

Only the v1 hash-pinned maltipoo structure is supported. Controls describe an
authored visible envelope, not real hair length, density, or biological growth.
The v1 implementation and all of its historical outputs remain unchanged.
"""
from __future__ import annotations

import copy

import numpy as np
from scipy.spatial import cKDTree

from . import coat_head_geometry as baseline

SOURCE_SHA256 = baseline.SOURCE_SHA256
ARRAY_SHA256 = baseline.ARRAY_SHA256
PARTS = baseline.PARTS
CHANNELS = baseline.CHANNELS
LENGTH_REGIONS = ("crown", "cheeks", "ears", "chest")
VOLUME_REGIONS = ("crown", "chest")
LENGTH_LEVELS = ("short", "medium", "long")
VOLUME_LEVELS = ("flat", "moderate", "full")
LENGTH_MAX = {"crown": 3.0, "cheeks": 1.5, "ears": 4.0, "chest": 3.0}
VOLUME_MAX = {"crown": 2.5, "chest": 5.0}
load_npz = baseline.load_npz


def _bump(radius):
    """A rounded C-infinity compact bump; no plateau or clipped flat top."""
    radius = np.asarray(radius, dtype=float)
    result = np.zeros_like(radius)
    inside = np.abs(radius) < 1
    result[inside] = np.exp(1 - 1 / (1 - radius[inside] ** 2))
    return result


def _preferences(values, regions, levels, kind):
    if not isinstance(values, dict) or set(values) - set(regions):
        raise ValueError(f"Unsupported {kind} regions")
    if any(not isinstance(value, str) or value not in levels for value in values.values()):
        raise ValueError(f"Unsupported {kind} level; expected {', '.join(levels)}")
    return {region: values.get(region, levels[0]) for region in regions}


def _fields(model):
    vertices = model["parts"]["head"]["v"].astype(float)
    x, y, z = vertices.T
    _, protected = baseline._weights(model)
    fixed = protected["nose_and_adjacent"] | protected["eye_neighborhood"] | protected["ear_neighborhood"]
    distance = cKDTree(vertices[fixed]).query(vertices)[0]
    protection = baseline._smooth(distance / 8)

    # Rounded distributions vary continuously over x/z or x/y. Unlike the v1
    # windows, they never lift a wide central band by one constant amount.
    crown_radius = np.sqrt(((x + 18) / 27) ** 2 + (z / 27) ** 2)
    crown = (_bump(crown_radius) * baseline._smooth((y - 24) / 12) * protection)
    cheek_radius = np.sqrt(((x + 38) / 16) ** 2 + ((y - 10) / 16) ** 2)
    cheeks = (_bump(cheek_radius) * baseline._smooth(y / 7)
              * baseline._smooth((np.abs(z) - 5) / 8) * protection)
    chest_radius = np.sqrt(((x - 2) / 41) ** 2 + ((y + 48) / 31) ** 2 + (z / 43) ** 2)
    chest = _bump(chest_radius) * baseline._smooth((-25 - y) / 14) * protection

    zero = np.zeros(len(vertices))
    length = {
        "crown": np.column_stack([zero, crown, zero]),
        "cheeks": np.column_stack([zero, -cheeks, zero]),
        "chest": np.column_stack([zero, -chest, zero]),
    }
    # Fullness uses a separate distribution and a noncollinear field. Crown
    # fullness may also rise; it is not a scalar multiple of the length field.
    # Volume has its own broad distribution. Reusing the compact length bump
    # concentrated changes on front-facing surfaces rather than the outline.
    crown_volume = (_bump((x + 18) / 45) * baseline._smooth((y - 20) / 20)
                    * baseline._smooth(distance / 14))
    chest_volume = _bump((x - 28) / 90) * baseline._smooth((-25 - y) / 22)
    crown_spread = np.column_stack([(x + 18) / 30, np.maximum(0, y - 18) / 26, z / 16])
    chest_spread = np.column_stack([.6 * (x - 28) / 55, zero, z / 28])
    volume = {
        "crown": crown_spread * crown_volume[:, None],
        "chest": chest_spread * chest_volume[:, None],
    }
    ears = {key: baseline._smooth((15 - model["parts"][key]["v"][:, 1]) / 15)
            for key in ("ear_left", "ear_right")}
    return length, volume, ears, protected


def _transport_normals(before, after, faces, source_normals):
    """Rotate source shading normals by the actual old/new geometric normal.

    Using a recomputed absolute normal only inside the changed region created
    visible shading seams against the original saved normal field. Transport
    preserves that field while following the deformation's geometric rotation.
    Geometry quality is checked separately using the actual face cross products.
    """
    def geometric(points):
        points = points.astype(float)
        face = np.cross(points[faces[:, 1]] - points[faces[:, 0]],
                        points[faces[:, 2]] - points[faces[:, 0]])
        values = np.zeros(points.shape)
        for corner in range(3):
            np.add.at(values, faces[:, corner], face)
        size = np.linalg.norm(values, axis=1)
        if np.any(size <= 1e-12):
            raise ValueError("Undefined geometric vertex normal during transport")
        values /= size[:, None]
        return values

    changed = np.any(before != after, axis=1)
    if not changed.any():
        return source_normals.copy()
    affected = np.unique(faces[changed[faces].any(axis=1)])
    original_geometry = geometric(before)
    direction = -1 if np.mean(np.sum(original_geometry * source_normals, axis=1)) < 0 else 1
    old, new = direction * original_geometry[affected], direction * geometric(after)[affected]
    cosine = np.clip(np.sum(old * new, axis=1), -1, 1)
    if np.any(cosine < -1 + 1e-8):
        raise ValueError("Antiparallel normal transport is unsupported")
    axis = np.cross(old, new)
    original = source_normals[affected].astype(float)
    first = np.cross(axis, original)
    rotated = original + first + np.cross(axis, first) / (1 + cosine[:, None])
    magnitude = np.linalg.norm(rotated, axis=1)
    if not np.isfinite(rotated).all() or np.any(magnitude <= 1e-12):
        raise ValueError("Invalid transported normal")
    rotated /= magnitude[:, None]
    # Identical normal directions need no re-normalisation/rounding change.
    identical = np.all(old == new, axis=1)
    rotated[identical] = source_normals[affected[identical]]
    result = source_normals.copy()
    result[affected] = rotated
    return result


def apply_preferences(model, lengths, volumes):
    """Return a fresh model and report after bounded deformation checks.

    Omitted length/volume regions mean baseline short/flat. All listed level
    combinations are attempted within fixed bounds; failed quality checks
    raise before returning a model. Ear and cheek fullness are unsupported;
    cheek length remains supported independently.
    """
    baseline._validate_base(model)
    lengths = _preferences(lengths, LENGTH_REGIONS, LENGTH_LEVELS, "length")
    volumes = _preferences(volumes, VOLUME_REGIONS, VOLUME_LEVELS, "visible-fullness")
    length_offsets = {key: LENGTH_MAX[key] * LENGTH_LEVELS.index(value) / 2
                      for key, value in lengths.items()}
    volume_offsets = {key: VOLUME_MAX[key] * VOLUME_LEVELS.index(value) / 2
                      for key, value in volumes.items()}
    length_fields, volume_fields, ear_fields, protected = _fields(model)
    result = copy.deepcopy(model)
    vertices = model["parts"]["head"]["v"]
    length_delta = np.zeros(vertices.shape, dtype=float)
    volume_delta = np.zeros(vertices.shape, dtype=float)
    for key in length_fields:
        length_delta += length_offsets[key] * length_fields[key]
    for key in volume_fields:
        volume_delta += volume_offsets[key] * volume_fields[key]
    result["parts"]["head"]["v"] = (vertices + length_delta + volume_delta).astype(vertices.dtype)
    for key in ("ear_left", "ear_right"):
        result["parts"][key]["v"][:, 1] -= length_offsets["ears"] * ear_fields[key]

    changes = {}
    for key in ("head", "ear_left", "ear_right"):
        before, after = model["parts"][key], result["parts"][key]
        displacement = np.linalg.norm(after["v"] - before["v"], axis=1)
        quality = {}
        if np.any(displacement):
            _, quality = baseline._normals_and_quality(before["v"], after["v"], before["f"], before["n"])
            after["n"] = _transport_normals(before["v"], after["v"], before["f"], before["n"])
        changes[key] = {"changed_vertices": int(np.count_nonzero(displacement)),
                        "max_displacement_model_units": float(displacement.max()), **quality}
    for name, mask in protected.items():
        if not np.array_equal(vertices[mask], result["parts"]["head"]["v"][mask]):
            raise ValueError(f"Coat v2 moved protected {name}")
    before_clearance = baseline._ear_clearance(model["parts"])
    after_clearance = baseline._ear_clearance(result["parts"])
    if any(after_clearance[key] < before_clearance[key] - .01 for key in before_clearance):
        raise ValueError("Coat v2 reduced sampled free-ear clearance")
    return result, {
        "schema_version": 2, "geometry_version": "envelope-v2",
        "source_model_sha256": SOURCE_SHA256, "source_array_sha256": ARRAY_SHA256,
        "lengths": lengths, "volumes": volumes,
        "length_offsets_model_units": length_offsets,
        "visible_fullness_offsets_model_units": volume_offsets,
        "length_direction": {"crown": "up", "cheeks": "down", "ears": "down", "chest": "down"},
        "visible_fullness_direction": {"crown": "up_and_horizontal_radial", "chest": "horizontal_radial"},
        "protection_scope": {
            "jaw_throat": "Complete original y[-25,0] band fixed; no lower cheek release.",
            "nose_eye_ear": "Original protected vertex sets remain fixed.",
        },
        "normal_update": "source shading normals transported by old/new geometric-normal rotation",
        "changes": changes, "protection": {key: int(mask.sum()) for key, mask in protected.items()},
        "free_ear_vertex_clearance_before": before_clearance,
        "free_ear_vertex_clearance_after": after_clearance,
        "status": "TECHNICAL_GEOMETRY_ONLY_NOT_VISUAL_APPROVAL",
        "limitations": ["One pinned authored maltipoo head/neck/upper-thorax source only.",
                        "Length and visible fullness are authored envelopes, not measured hair length or density.",
                        "Fullness does not change coat layers, strand count, texture, or actual anatomical proportions.",
                        "No cheek or ear fullness, full-body coat, independent left/right grooming or universal breed morph.",
                        "Cheek-fullness experiments failed visual review; removing support does not resolve or approve those candidates.",
                        "Local triangle checks and sampled vertex clearance are not a global collision proof.",
                        "COAT-LONG-01 appearance correction and native64 readability require fresh visual review."],
    }
