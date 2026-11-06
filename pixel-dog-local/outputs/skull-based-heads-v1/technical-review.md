# Independent technical review — skull-based-heads-v1, pass11 A/B/C

Reviewer: `/root/maltipoo_photo_technical`. Implementer: `/root`. 2026-11-06.

**TECHNICAL = PASS.** No unresolved technical BLOCKER or MAJOR was found for these three exact saved images. This verdict does not replace the separate visual verdict or the user’s selection.

## Coverage and exact reproduction

I directly opened `heads-A.png`, `heads-B.png`, and `heads-C.png`: each is 2400 × 1500, containing four breeds × five views (side, oblique, front, rear, top), 60 cells total. All views are projections of the corresponding single saved 3D model at the same nominal scale; cell recentering follows each projected bounding box. This is neutral head-and-short-neck geometry, not mouth animation, a full body, pixel conversion, or ML training.

`review_reproduce.py` independently rebuilt all 12 models once, without overwriting candidate files. Every saved vertex, face, normal, color, metadata field, and profile exactly matches the fresh reconstruction, including dtype for arrays. All three rendered PNG byte strings exactly match the saved candidates. `parameters.json` exactly matches the rebuilt metadata. The regenerated copies are under `review-reproduction/`. Main source, skeletal geometry, profiles, candidate cache, parameters, and reference manifest remained unchanged during the run. Evidence: `review-reproduction.json`.

The initial audit aggregate included a missing old-cache comparison in its success predicate; all current model/PNG comparisons had already passed. That bookkeeping predicate was corrected without another rebuild. The missing prior cache is separately and explicitly handled below.

## Actual geometry and containment

For A and C, I independently checked every upper/jaw bone vertex and every bone triangle centroid against the saved skin using +X ray parity, enumerating all possible ray hits through projected triangle bounds. A sub-0.00003 coordinate perturbation avoids shared-edge double counts. No sample is outside the raw exterior field or saved skin. B’s same-source preflight supplies the corresponding tests. Total coverage is 1,353,486 bone samples across the three variants (451,162 per variant).

| Variant | Breed | Minimum upper clearance | Minimum jaw clearance |
|---|---|---:|---:|
| A | golden | 0.293032 | 0.555255 |
| A | whippet | 0.711766 | 0.444928 |
| A | dachshund | 0.847387 | 0.451912 |
| A | maltipoo | 1.038039 | 0.864728 |
| B | golden | 0.484867 | 0.716097 |
| B | whippet | 0.857432 | 0.566777 |
| B | dachshund | 1.004432 | 0.574480 |
| B | maltipoo | 1.118018 | 0.976368 |
| C | golden | 0.675751 | 0.803614 |
| C | whippet | 1.003156 | 0.691134 |
| C | dachshund | 1.161089 | 0.629127 |
| C | maltipoo | 1.190675 | 1.090231 |

Distances are model units, not measured biological dimensions. Every tabulated minimum is certified against the lower bound of omitted triangles. Individual deep-point distances in the earlier B nearest-triangle report are not all certified and are not presented as exact values. These are sampled surface-containment tests, not exhaustive continuous face-intersection or arbitrary-deformation proofs.

- All 12 skin meshes and 24 eye meshes have one component, Euler characteristic 2, zero boundary edges, zero nonmanifold edges, and zero zero-area faces. All saved arrays are finite. A few nonzero microscopic triangles fall below the diagnostic double-area threshold of 1e−10 (A Dachshund/Maltipoo and B Dachshund); they do not create holes or zero-area faces.
- Every eye has actual surface samples inside and outside the skin, with crossing triangles along the embedding boundary. Eyes are separate closed ellipsoids, intentionally embedded rather than welded to skin. Their common tangential radii are equal by construction; apparent shape changes with the view.
- Every nasal material patch is one connected region on the same closed skin, with shared edges to neighboring skin. The normalized nasal field is the same template across all 12 models to 2.57e−15; breed scaling is uniform. The exposed patch boundary also depends on the surrounding muzzle, so identical exposed silhouettes are not claimed.
- Both ear roots of every variant have positive local head/ear volume overlap. The A/C root grids contain 458–1055 overlapping samples each at spacing 0.6, and the complete saved skin has one closed component. B overlap and attachment were checked in its preflight. These are actual field/mesh connection checks, not inference from screen adjacency.

Evidence: `review-final-geometry.json`, `review-pass11-saved-mesh.json`, `review-pass11-ray-containment.json`, and `review-final-auxiliary.json`.

## B evidence reuse

The source hash and B PNG are identical to pass11 preflight. Archived pass11 parameters exactly match current B metadata, all recorded topology counts match, and the current B model exactly matches a new independent build. Therefore the previous B bone/attachment tests are reused rather than repeating their full nearest-triangle scan. The old B-only `geometry.pkl` was not archived: no direct old-array byte comparison is claimed. The old cache hash remains in the original evidence, while current cache and per-array fingerprints are recorded in the new reports.

## Real skeletal dependency and variation isolation

The source reads the reviewed upper and jaw vertex arrays to construct local convex cross-section envelopes. This is a functional dependency, not just a copied profile label. In an isolated test, moving 3717 actual Golden upper-bone vertices upward by 2 units while keeping the entire profile unchanged changed 25,160 baseline skin samples by more than 0.01 in the field, with maximum response 2.380067. A fresh extraction on the unchanged production grid changed the actual skin mesh (51,088 vertices). The perturbation was performed on a deep copy; reviewed skeletal files were not changed.

For each breed, comparing A/C metadata with B changes only `sections`, `variant`, and the dependent `eyes` anchors. Profiles, nasal template placement/scale, ear paths and thickness, neck loft, and palette definitions are fixed. Surface fitting, the front support envelope, posterior envelope, eye location/orientation, and material exposure follow the fullness allowance as declared. This does not claim bit-identical surface colors at different vertices or unchanged projected bounding boxes.

The skeletal profile hash still exactly equals the user-requested shortened profiles from `head-skeleton-v1`; source skull, jaw, hinge and nasal guide values were not edited. The candidate uses neutral bone positions and authored soft-tissue allowances. Cartilage is excluded from the bone-containment target; the profile’s nasal guide informs nose placement.

## Provenance and limits

The 23-entry `inputs.json` below pins the direct source, actual skeleton/cache inputs, imported skeletal builder and rasterizer, Numba cache files, both fonts, profiles, reference manifests, and design reference images. Candidate geometry and parameters are included as validated board-data exports. Runtime open-file auditing identifies transitive local code/cache/font reads; the photos and style plate are design provenance rather than images parsed by the generator. Package versions are recorded in `review-reproduction.json`. Exact reproduction is established in that recorded environment, not on every platform.

The imported skeletal `review-status.json` is an actual input because `load_inputs()` requires READY. The live start guard passed, the end value is READY, and its last-write timestamp precedes this review. Its full byte hash was captured at the end after correcting an overly broad exclusion of review-prefixed filenames; no unrecorded start byte hash is claimed. This status gates eligibility and does not supply geometry parameters. The current full hash is pinned below.

README correctly distinguishes authored model units from measured anatomy, photograph/style references from generation inputs, and future work from completed work. No CT registration, breed-matched bone measurement, physiological accuracy, expression rig, exhaustive self-intersection proof, or training-ground-truth status is claimed. The earlier rejected bun-like/conical candidates remain historical failures; this technical result does not overwrite their rejection or independently decide likeness.

## Exact candidate hashes

- `heads-A.png`: `c2889fd909531aa8bc7cd6e298da68a0a1bcbfe038ea7226ea30a71b81947cc5`
- `heads-B.png`: `1858a944170e4bfa0ea6ab5662ac0287ea431b7a46e90f0dca15789490396440`
- `heads-C.png`: `d274f7c115dd7321267f1970fcb678a0a1f55c33b9542c0783dedc77bfdde9f0`

## Exact input hash set

- `../../../.codex-attachments/768d9f11-0441-440b-a272-2d05ac586b78/6802266b-b4f1-4a70-9d32-d6584792f9da/55757.jpg`: `9c439bdd4b2811a2a9f0eb578dda06909ec080a544e33071bd950b26504c3fb2`
- `../../../.codex-remote-attachments/01a1a744-36e5-7233-ac4f-68fc9cfbfd7a/3c2fda8b-ca8a-4fff-b7e4-601bfe9eaa80/1-55765.jpg`: `4ed0aa846afd7badf120f34fc2cc7bdd7e1ed6158a7c70c72ade8c7cf593afc7`
- `../deformation-b-face-v2/golden-reference.png`: `2be4a6076f6730adbbab58d68536181bf15b528898084adae17b5f49f1b032ef`
- `../deformation-b-round-eyes-v1/round-eyes-before-after.png`: `fc7f9a5626f54bc1e9e9165bc1f6187addaace903e7a8fdb7588c6adbd8fbd9c`
- `../head-skeleton-v1/profiles.json`: `aab232a82947fe4a81c6785e3c4e54ad458dca82c82a99e1aa9431ce8e29e323`
- `../head-skeleton-volume-v2/__pycache__/raster.raster-6.py312.1.nbc`: `df33acdfd671eb8eb6e6e3a3cfa5eec9a7a9e3e900720868449e60ed3d13a33a`
- `../head-skeleton-volume-v2/__pycache__/raster.raster-6.py312.nbi`: `963438c86a99e955db7538d04dc04a537669ab2ee828a4a99f3a406b92dd44a9`
- `../head-skeleton-volume-v2/build.py`: `734b85527c58a0cf9bf598867dfabbd9bddf2dd91f50b8fef9ec9fbc6733419e`
- `../head-skeleton-volume-v2/geometry.pkl`: `eaec7d20d5ea8abbb8a14e728d6120f4f119e2d3ee238d4af5b3836f06e4d154`
- `../head-skeleton-volume-v2/profiles.json`: `aab232a82947fe4a81c6785e3c4e54ad458dca82c82a99e1aa9431ce8e29e323`
- `../head-skeleton-volume-v2/raster.py`: `f2747b235362f49c94d8a7121784d5d597464723649bd1a4b951396dbb289f15`
- `../head-skeleton-volume-v2/references.json`: `ae6dd24467d04a9666b1def48ff3f7cdcbdeb9708011a08940629c6b26a93c3d`
- `build.py`: `84ff23798e2d487de2dddaa2302f15eebd292affb4dec0c9ab3690b2df410b2d`
- `geometry.pkl`: `f332953619225f439f62ba955f7d01ca9c73ac24c374f1ae06f7069e6b637b89`
- `parameters.json`: `8391d478b00d22d84da5b85a68d041d3416627f3eff1d5f2a63ce712ad5890ca`
- `references.json`: `00dac371c404cccf967e8c931f356746bfe740754257016df5bc2888ade14cdd`
- `../../private-data/breed-standing-pair-v1/dachshund-source.png`: `15b7e9545051ffc8970059748f9fd8d51e7ab6d9d683b95aa22638429f026cfc`
- `../../private-data/skull-anatomy-v2/dorsal.jpg`: `f7c059883e2ca7a9ba17f48385f62485e3c2c40b4189dbfff13052b417167a10`
- `../../private-data/skull-anatomy-v2/lateral.jpg`: `df1c09fa01836ce5fc28b5c51ca7ccf1333f9a3ce129d448af866709288e9cfd`
- `../../private-data/skull-anatomy-v2/rostral.jpg`: `8d8d140502b12b2fb37cbb19b2620ee9ef03bd504a961a333417d39204192ccb`
- `../../../../../../../Windows/Fonts/malgun.ttf`: `7a183cf1c6c56b9609fcc16eda8b5229fbc11758a21e669ec00343239b02192f`
- `../../../../../../../Windows/Fonts/malgunbd.ttf`: `e8cbc0b2afcc14fb45dfb6086d5102c0b23a96e7b6e708f3122acde1b86c9082`
- `../head-skeleton-volume-v2/review-status.json`: `5c9d76e0d6c23f260daf3fa4f327d9cbc2b8b4c8204567a19bcf7754a0ff7e1e`

<!-- review-verdict: {"status":"PASS","reviewer":"/root/maltipoo_photo_technical","artifacts":{"heads-A.png":"c2889fd909531aa8bc7cd6e298da68a0a1bcbfe038ea7226ea30a71b81947cc5","heads-B.png":"1858a944170e4bfa0ea6ab5662ac0287ea431b7a46e90f0dca15789490396440","heads-C.png":"d274f7c115dd7321267f1970fcb678a0a1f55c33b9542c0783dedc77bfdde9f0"},"inputs":{"../../../.codex-attachments/768d9f11-0441-440b-a272-2d05ac586b78/6802266b-b4f1-4a70-9d32-d6584792f9da/55757.jpg":"9c439bdd4b2811a2a9f0eb578dda06909ec080a544e33071bd950b26504c3fb2","../../../.codex-remote-attachments/01a1a744-36e5-7233-ac4f-68fc9cfbfd7a/3c2fda8b-ca8a-4fff-b7e4-601bfe9eaa80/1-55765.jpg":"4ed0aa846afd7badf120f34fc2cc7bdd7e1ed6158a7c70c72ade8c7cf593afc7","../deformation-b-face-v2/golden-reference.png":"2be4a6076f6730adbbab58d68536181bf15b528898084adae17b5f49f1b032ef","../deformation-b-round-eyes-v1/round-eyes-before-after.png":"fc7f9a5626f54bc1e9e9165bc1f6187addaace903e7a8fdb7588c6adbd8fbd9c","../head-skeleton-v1/profiles.json":"aab232a82947fe4a81c6785e3c4e54ad458dca82c82a99e1aa9431ce8e29e323","../head-skeleton-volume-v2/__pycache__/raster.raster-6.py312.1.nbc":"df33acdfd671eb8eb6e6e3a3cfa5eec9a7a9e3e900720868449e60ed3d13a33a","../head-skeleton-volume-v2/__pycache__/raster.raster-6.py312.nbi":"963438c86a99e955db7538d04dc04a537669ab2ee828a4a99f3a406b92dd44a9","../head-skeleton-volume-v2/build.py":"734b85527c58a0cf9bf598867dfabbd9bddf2dd91f50b8fef9ec9fbc6733419e","../head-skeleton-volume-v2/geometry.pkl":"eaec7d20d5ea8abbb8a14e728d6120f4f119e2d3ee238d4af5b3836f06e4d154","../head-skeleton-volume-v2/profiles.json":"aab232a82947fe4a81c6785e3c4e54ad458dca82c82a99e1aa9431ce8e29e323","../head-skeleton-volume-v2/raster.py":"f2747b235362f49c94d8a7121784d5d597464723649bd1a4b951396dbb289f15","../head-skeleton-volume-v2/references.json":"ae6dd24467d04a9666b1def48ff3f7cdcbdeb9708011a08940629c6b26a93c3d","build.py":"84ff23798e2d487de2dddaa2302f15eebd292affb4dec0c9ab3690b2df410b2d","geometry.pkl":"f332953619225f439f62ba955f7d01ca9c73ac24c374f1ae06f7069e6b637b89","parameters.json":"8391d478b00d22d84da5b85a68d041d3416627f3eff1d5f2a63ce712ad5890ca","references.json":"00dac371c404cccf967e8c931f356746bfe740754257016df5bc2888ade14cdd","../../private-data/breed-standing-pair-v1/dachshund-source.png":"15b7e9545051ffc8970059748f9fd8d51e7ab6d9d683b95aa22638429f026cfc","../../private-data/skull-anatomy-v2/dorsal.jpg":"f7c059883e2ca7a9ba17f48385f62485e3c2c40b4189dbfff13052b417167a10","../../private-data/skull-anatomy-v2/lateral.jpg":"df1c09fa01836ce5fc28b5c51ca7ccf1333f9a3ce129d448af866709288e9cfd","../../private-data/skull-anatomy-v2/rostral.jpg":"8d8d140502b12b2fb37cbb19b2620ee9ef03bd504a961a333417d39204192ccb","../../../../../../../Windows/Fonts/malgun.ttf":"7a183cf1c6c56b9609fcc16eda8b5229fbc11758a21e669ec00343239b02192f","../../../../../../../Windows/Fonts/malgunbd.ttf":"e8cbc0b2afcc14fb45dfb6086d5102c0b23a96e7b6e708f3122acde1b86c9082","../head-skeleton-volume-v2/review-status.json":"5c9d76e0d6c23f260daf3fa4f327d9cbc2b8b4c8204567a19bcf7754a0ff7e1e"},"coverage_complete":true,"unresolved":{}} -->
