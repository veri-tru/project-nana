# Scoped technical review: muzzle shortening

2026-11-06. Independent reviewer: `/root/maltipoo_photo_technical`. Implementer: `/root`.

**Requested length edit: verified. Whole candidate: BLOCKED.** This report does not grant a whole-candidate TECHNICAL PASS. The existing SK01, SK02 and SK03 MAJOR findings remain unresolved. Overall review coverage is therefore incomplete; the machine-readable verdict remains NOT_REVIEWED for the full anatomical candidate.

## Scope and evidence

The user requested shorter muzzles for Golden, Whippet and Dachshund, preserving Maltipoo. I inspected the current two saved PNGs directly, including all four breeds and all three views in `comparison.png`, plus the Golden neutral/opening guide. I also opened the immutable pre-edit comparison. This is a technical review of change isolation and reproduction, not a fresh anatomical approval.

`review_muzzle.py` independently imports the unchanged generator, reconstructs all rigs from the current profiles, and calls `boards(rigs)`. Both generated PNG byte strings exactly equal the saved files. The saved `rigs.json` equals the independent reconstruction. Reproductions are saved under `review-muzzle-reproduction/`; numerical evidence and hashes are in `muzzle-technical-checks.json`. The generator was read-only and its SHA-256 remained unchanged throughout review.

## Confirmed changes and preservation

| Breed | Stop-to-tip X span before | After | Reduction |
|---|---:|---:|---:|
| Golden | 44.00 | 30.32 | 31.09% |
| Whippet | 68.00 | 48.20 | 29.12% |
| Dachshund | 60.00 | 41.80 | 30.33% |
| Maltipoo | 29.00 | 29.00 | 0% |

These are authored coordinate spans along X, not biological measurements or three-dimensional curve lengths.

- In each changed profile, only X coordinates for `nasal_bridge`, `nasal_base` and `nose_tip` changed. Every dorsal Y value, all widths, hinge X, and the crown/forehead/stop coordinates remain exact. `skeleton.py` is byte-identical to the pre-edit snapshot.
- The same eight derived nodes changed in each affected breed: nasal bridge/base/tip, maxilla front, nasal floor, chin, and left/right jaw front. The last seven all translate by the same X delta: Golden +13.68, Whippet +19.80, Dachshund +18.20. No other node changed. Their parent ownership and kind remain identical.
- The entire nasal-base-to-tip vector is unchanged. Its X span is 8 and its Y difference is -2 for these three breeds; its 3D straight-line length is approximately 8.246, so this report does not call it an 8-unit Euclidean segment.
- Maltipoo profile, every node, and every sampled line in `geometry(rig)` are exactly unchanged. Its entire comparison row (all three views, pixels Y 1113–1417 inclusive) is byte-identical to the pre-edit image.
- Parent/group topology is unchanged. At 9 and 18 degrees, every orange jaw curve matches one rigid transformation about the unchanged jaw-axis center, while every non-orange curve remains fixed. Maximum error is below 1e-10. This confirms the implementation's transform, not anatomical adequacy of the sparse lines.
- The two current outputs are 1660 × 1470 (`comparison.png`) and 1360 × 850 (`chain-guide.png`). No other runtime project modules are imported by the standalone generator: its project generation inputs are `skeleton.py` and `profiles.json`, with the two Windows fonts. The reference manifest and its first-photo hash are linked as design provenance; neither the photo nor external web pages are parsed by rendering code.

## Unresolved whole-candidate findings

- **SK01 / MAJOR:** dorsal guide lines and ellipse sections still lack the supporting cranial/maxillary volumes required for the intended skull foundation.
- **SK02 / MAJOR:** mandibular centerlines still lack body depth, adequate ascending ramus/coronoid structure, and explicit articular support. Correct rigid rotation alone does not resolve this.
- **SK03 / MAJOR:** authored breed profiles remain unvalidated against matched skull views. A groomed Maltipoo exterior photo is not skeletal measurement evidence.

The length correction does not repair or downgrade these findings. The full candidate remains BLOCKED; this report verifies only that the explicitly requested length change was carried out consistently and reproducibly. It does not claim completed skin, occlusion, continuous animation, six facial expressions, or app integration. The README correctly defines `parent` as motion ownership and node points as shared head-local neutral coordinates, and defines 0 degrees as authored neutral rather than verified tooth contact. README wording is review context, not a hashed rendering dependency.

## Final artifact hashes

- `comparison.png`: `af5b7f882f552f16c73b9fa3614442e3fa2239065d09ee9daa1e9a26e0e5cf14`
- `chain-guide.png`: `a8f4ed751acab9b47b15e6fc0a1257d79621cfed9bba691b56291c70d3e5c79b`

## Input and provenance hashes

- `skeleton.py`: `6287902a8de664b6a1b8322a7f3623a603ad47b92023b3c78831a70a5f480950`
- `profiles.json`: `aab232a82947fe4a81c6785e3c4e54ad458dca82c82a99e1aa9431ce8e29e323`
- `references.json`: `cab5787245c05674a92c32a415c7575d158c4b5417113107461f16a06b6e5117`
- `../../../../../../../Windows/Fonts/malgun.ttf`: `7a183cf1c6c56b9609fcc16eda8b5229fbc11758a21e669ec00343239b02192f`
- `../../../../../../../Windows/Fonts/malgunbd.ttf`: `e8cbc0b2afcc14fb45dfb6086d5102c0b23a96e7b6e708f3122acde1b86c9082`
- `../../../.codex-remote-attachments/01a1a744-36e5-7233-ac4f-68fc9cfbfd7a/3c2fda8b-ca8a-4fff-b7e4-601bfe9eaa80/1-55765.jpg`: `4ed0aa846afd7badf120f34fc2cc7bdd7e1ed6158a7c70c72ade8c7cf593afc7`

The immutable pre-edit source/profiles/rigs/images/status hashes are recorded separately in `muzzle-technical-checks.json` under `before_evidence`. They are comparison evidence, not current rendering inputs. Runtime libraries: numpy 1.26.4, scipy 1.17.1, Pillow 12.2.0.

<!-- review-verdict: {"status":"NOT_REVIEWED","reviewer":"/root/maltipoo_photo_technical","artifacts":{"comparison.png":"af5b7f882f552f16c73b9fa3614442e3fa2239065d09ee9daa1e9a26e0e5cf14","chain-guide.png":"a8f4ed751acab9b47b15e6fc0a1257d79621cfed9bba691b56291c70d3e5c79b"},"inputs":{"skeleton.py":"6287902a8de664b6a1b8322a7f3623a603ad47b92023b3c78831a70a5f480950","profiles.json":"aab232a82947fe4a81c6785e3c4e54ad458dca82c82a99e1aa9431ce8e29e323","references.json":"cab5787245c05674a92c32a415c7575d158c4b5417113107461f16a06b6e5117","../../../../../../../Windows/Fonts/malgun.ttf":"7a183cf1c6c56b9609fcc16eda8b5229fbc11758a21e669ec00343239b02192f","../../../../../../../Windows/Fonts/malgunbd.ttf":"e8cbc0b2afcc14fb45dfb6086d5102c0b23a96e7b6e708f3122acde1b86c9082","../../../.codex-remote-attachments/01a1a744-36e5-7233-ac4f-68fc9cfbfd7a/3c2fda8b-ca8a-4fff-b7e4-601bfe9eaa80/1-55765.jpg":"4ed0aa846afd7badf120f34fc2cc7bdd7e1ed6158a7c70c72ade8c7cf593afc7"},"coverage_complete":false,"unresolved":{"SK01":"MAJOR","SK02":"MAJOR","SK03":"MAJOR"},"scope":"Only user-requested muzzle shortening: scoped technical checks PASS; full anatomical candidate remains BLOCKED."} -->
