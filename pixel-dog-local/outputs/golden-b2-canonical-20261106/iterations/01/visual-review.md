# Independent visual review — B2 canonical golden study

Verdict: **VISUAL=FAIL**. The B2 color/contour treatment is recognizable, but the adult-B geometry requirement is not met. This is not a user taste decision or a native64 compliance objection.

Reviewer: `/root/b2_canonical_visual`. I did not create or modify the images. I opened the final comparison first, before the style sheet, geometry reference, photo, and generation instructions. No producer success assessment or technical verdict was supplied before my initial observation. All artifacts and input hashes in `evidence.json` were independently recomputed and matched. The model pickle was hash-checked only, not inspected as visual evidence.

## Unresolved finding

**V1 — BLOCKER — `comparison.png`, A/B/C, primarily SIDE and 3-4, supported by FRONT and TOP: adult muzzle/skull proportions revert toward the old B2 golden.**

Direct observation: every side head has a high, nearly circular cranial dome and a short forward muzzle segment. The stop sits relatively close to the nose, leaving the dome and hanging ear dominant. In the adult-B engine reference, the muzzle occupies more of the total length and the skull is lower relative to that length; its muzzle is a substantial elongated volume. The generated three-quarter heads likewise shorten the projected muzzle and enlarge the forehead. The front drawings have a rounder, taller central face than the broader, lower engine front. The top drawings show the same reduced forward projection relative to the rounded rear skull. This is visible silhouette/proportion drift, rather than a request for exact mesh pixels.

The original B2 sheet's golden silhouette has that same short muzzle/high dome combination. It was explicitly designated STYLE ONLY; its obsolete proportions must not replace adult-B. The left source photo also supports an adult golden with a substantial muzzle and restrained forehead transition, not the generated puppy-like dome. Photo-specific open-mouth posture is not required and is not used as a defect.

Severity basis: preserving the revised adult golden face while restoring the earlier B2 rendering style is a core user requirement. Style recovery alone does not complete that correction. The common geometry regression affects all three options, so none is a deliverable candidate.

Recheck condition: regenerate all three rows with the adult-B side muzzle length/depth and restrained cranial dome, then preserve the corresponding broad front face and longer top projection. Keep the current B2 contour, solid round eyes, and connected soft shadow clusters. Reopen all fifteen cells against the geometry reference and style sheet; do not use the old B2 golden's silhouette as a geometry reference.

## Coverage — all 15 cells directly inspected

All cells were viewed in the actual saved 1536×1024 comparison. No cells were omitted. Findings below distinguish shared geometry failure from local defects; lack of a local defect is not a whole-cell PASS.

| Row | View | Observation |
| --- | --- | --- |
| A | SIDE | Short muzzle/high dome relative to adult-B; ear and nose remain attached; V1. |
| A | 3-4 | Forehead dominates shortened projected muzzle; eyes/nose readable; V1. |
| A | FRONT | Face is taller/rounder than broad adult-B; paired ears connected; V1 support. |
| A | BACK | Connected crown, bilateral hanging ears and neck; no obvious detached volume; silhouette consistent with this row's rounded head. |
| A | TOP | Forward muzzle shorter relative to rear skull than adult-B; nose connected; paired side eyes coherent; V1 support. |
| B | SIDE | Same shortened adult proportions; softer ear/jaw shadow does not correct shape; V1. |
| B | 3-4 | Same high forehead/short muzzle; eye centers remain effectively aligned with A; V1. |
| B | FRONT | Same round face geometry; reduced shadow makes cheek/neck junction gentler but does not broaden face; V1 support. |
| B | BACK | Crown/ear/neck continuity retained; smaller, paler shadow areas. |
| B | TOP | Same short forward projection and round rear skull; reduced shadows; V1 support. |
| C | SIDE | Same geometry regression; larger darker lower-jaw and ear shadows; V1. |
| C | 3-4 | Same dome and shortened muzzle; deeper ear/neck shadows; V1. |
| C | FRONT | Same rounded central face; deeper side/under-jaw shadow; V1 support. |
| C | BACK | Continuous silhouette and paired ears; deeper lower-side shadows, no obvious structural break. |
| C | TOP | Same reduced forward projection; darker/larger lower/right shadow; V1 support. |

## B2 style and A/B/C change isolation

The warm brown softened contour, stepped connected gold shadow clusters, cream board, and solid rounded dark eyes belong to the same visual family as the four-breed B2 reference. There is no return to a harsh black outline or tiny plus-shaped eyes. Individual heads are displayed larger than those on the four-breed source board, but their contour-step appearance is recognizably related. This style success cannot override V1.

A/B/C are visually near-identical in overall silhouette, placement, and eye/nose shape. Small step/ear-tip differences exist at a few pixels, but I do not find material identity, eye placement, or geometry changes between rows. B is visibly paler/softer in its ear and lower-face shading, and C deeper; this fits the intended small shadow variation at concept-study level. The material geometry problem is shared across all three rows relative to adult-B, not caused by their intended shade variation.

## Scope and limits

This review covers the actual high-resolution static concept sheet and all fifteen shown views. It does not certify native64 grid alignment, palette counts, mesh identity, anatomical measurements, hidden attachments, device rendering, or animation. The absence of such claims does not narrow the user's face/proportion and cross-breed style requirements. The 3D reference is used visually, not as proof that generated views share one exact model. The photo's right-hand diagram was excluded as instructed. User approval remains separate from this independent rejection.

<!-- review-verdict: {"status":"FAIL","reviewer":"/root/b2_canonical_visual","artifacts":{"comparison.png":"201306cc1ba82859cdf0f927634295451c4cd16c166ccfd4e4c5d5ac38512752"},"inputs":{"../../references/styles/breed-head-b2/v1/reference-sheet.png":"e15a82616528b4f05c51acc369ae4cbc25f6ffc781f1b1e11b1aea3f7fb1a3d6","../../references/styles/breed-head-b2/v1/manifest.json":"b4b663e1bdc45968d34e50a7e5035f6b826e9400e165f29942e4e11d25938c86","../skeleton-pixel-concepts-20261106/B2-soft.png":"e15a82616528b4f05c51acc369ae4cbc25f6ffc781f1b1e11b1aea3f7fb1a3d6","../golden-pixel-refresh-20261106/engine-reference.png":"45c75c02ff081898fb7532bc200c4acd3fbd609d289ae2fc0cfa31b792f88741","../golden-adult-head-v1/model-B.pkl":"9ccdb84a4d3f03604b3f49195a1b919224e92641c04640781fde535c10dbf122","../deformation-b-face-v2/golden-reference.png":"2be4a6076f6730adbbab58d68536181bf15b528898084adae17b5f49f1b032ef","generation.json":"110fc67b76bbbddc7467e88a6041ae42d2b816bfe616825d6377f6d7deab5c4d"},"coverage_complete":true,"unresolved":[{"id":"V1","severity":"BLOCKER"}]} -->
