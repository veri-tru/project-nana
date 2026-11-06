# Independent technical review — skull-based-heads-v2, candidate13

Reviewer: `/root/maltipoo_photo_technical`. Implementer: `/root`. 2026-11-06.

**TECHNICAL = PASS.** No unresolved technical BLOCKER or MAJOR remains for the three exact candidate images. This does not replace independent visual approval, the delivery gate, or the user’s choice.

## Coverage and reproduction

I opened all three final boards: A/B/C, each 2400 × 1500, four breeds × side/oblique/front/rear/top, 60 cells total. Each view projects the same corresponding 3D model. The deliverable is neutral head/short-neck geometry; it is not a mouth animation, pixel asset, full body, or trained model.

One independent full reconstruction reproduced all 12 models exactly: every vertex, face, normal, color, profile, and metadata value matches the saved cache, including array dtype. `parameters.json` is exact, and all three PNG byte strings match the candidates. No candidate source or export was overwritten. Source, input skeleton/profile/status, v1 seed source/reference cache, current cache/parameters, and reference manifest were hash-guarded before and after. Evidence: `review-reproduction.json`; independently rendered copies are in `review-reproduction/`.

## Final surfaces, not initial fields

Containment and collision checks use the saved post-relaxation triangles. All 1,353,486 bone vertices/triangle-centroid samples across the 12 models are inside the skin. Direct skin–bone triangle tests find zero crossings, including all 5,903 overlapping-AABB candidate pairs. This closes dev12’s actual bone-exposure failure with fresh evidence, not its initial analytic field or its visual PASS.

| Variant | Breed | Minimum upper clearance | Minimum jaw clearance |
|---|---|---:|---:|
| A | golden | 0.636560 | 0.382143 |
| A | whippet | 0.705733 | 0.362670 |
| A | dachshund | 0.781773 | 0.376709 |
| A | maltipoo | 0.709420 | 0.524781 |
| B | golden | 0.584782 | 0.343419 |
| B | whippet | 0.663911 | 0.332473 |
| B | dachshund | 0.725138 | 0.343375 |
| B | maltipoo | 0.639468 | 0.485302 |
| C | golden | 0.546439 | 0.309843 |
| C | whippet | 0.633191 | 0.310367 |
| C | dachshund | 0.683682 | 0.317266 |
| C | maltipoo | 0.585904 | 0.454482 |

These are certified minimum closest-triangle distances over the tested bone samples, in model units. All omitted-triangle lower bounds exceed the reported minima. The smallest value is 0.309843; the configured 0.70 obstacle margin and 0.65 offset are not claimed as achieved clearances.

All 36 skin/eye meshes have one component, Euler characteristic 2, zero boundary/nonmanifold/zero-area faces, no faces below the stated 1e−10 double-area diagnostic threshold, and finite arrays. Non-adjacent skin-triangle checks find no crossing or positive-area coplanar overlap among 749,304 overlapping-AABB pairs. Shared-vertex pairs are excluded from that self-contact diagnostic. Ray perturbations and triangle tests use explicit floating tolerances; no formal exact-arithmetic or arbitrary-deformation proof is claimed.

## Nose, eyes, and ear attachment

- All 1,621 black nasal vertex coordinates per variant are byte-identical to the user-selected v1 B reference after coordinate sorting. Source nasal template/scale is reused, and the black region plus incident-face boundary is pinned. Final normals are recomputed, so identical nasal shading or PNG pixels are not claimed.
- Every eye mesh has exactly the same v/f/n/c arrays as v1 B. All 24 eyes remain partly embedded in the final skin, with 144–241 crossing faces each; their equal tangential radii and closed shape are retained.
- Every ear root has 143–164 actual shared final-mesh edges across the nearby head/ear partition, together with a single closed skin component and no detected crossing. Initial head/ear fields label this partition only; they are not substituted for final-surface containment. Maltipoo metadata correctly describes its oriented ellipsoid leaf/root union.

Evidence: `review-final-geometry.json`.

## Actual variation scope

A/B/C change only constrained-relaxation iterations: 320/400/480. The 160 polishing steps, normal offset settings, skeleton, seed, nasal template, eye geometry, neck, ear-generating parameters, and palettes remain common. Metadata differences are limited to variant/iteration labels and resulting maximum displacement. Skin face indices and initial colors are identical across variants. All profiles exactly match the reviewed shortened skeletal profiles.

During the independent rebuild, a read-only wrapper observed every seed-to-final mutation: all variants of each breed have identical seed-vertex hashes; all pinned black/incident-face vertices and all zero-weight vertices retain their positions exactly. The unchanged input bone arrays drive both the initial cross-section envelope and the nearest-bone-vertex normal obstacle. The final saved mesh, not a copied label or seed field, is used for the checks above.

The spatial relaxation mask also reaches anterior pinna surfaces. Relative to B, maximum A/C shifts in the ear-labelled region are Golden 0.113/0.100, Dachshund 0.274/0.248, Maltipoo 0.096/0.084, and Whippet 0/0 model units. Dachshund changes extend down the anterior pinna, not merely its root. Thus common ear parameters do not mean byte-identical final ears. This dependent variation is explicitly recorded in README and `review-final-junction-variation.json`; it does not exempt breed-ear appearance from visual review.

## Provenance and limits

The exact 26-entry input set is in `inputs.json` and the machine-readable marker below. It includes current/v1 generation code, both reference geometry caches, the skeletal READY status actually read by `load_inputs`, preserved profiles, raster source and Numba cache, both fonts, candidate data exports, reference manifests, and design images. Runtime read auditing captures transitive local code/cache/font inputs. All hashed inputs and candidate image hashes were checked against the final files. The guarded skeletal status hash was captured both before and after this run.

The v1 full-face rejection remains in force. Only its black nose was explicitly selected for restoration; v1 is a construction seed and comparison source, not inherited visual approval. Photographs/style boards are design references, not measured bone geometry or pixels copied into these boards. README distinguishes initial field metadata from the final relaxed surface and authored model units from real measurements. Dev10/12 results are preserved and not promoted to this candidate.

Reproduction environment: Python 3.12.10, NumPy 1.26.4, SciPy 1.17.1, scikit-image 0.26.0, Pillow 12.2.0, Numba 0.68.0, with pinned fonts/cache. Cross-platform identity, biological accuracy, and training-ground-truth status are not claimed.

## Exact candidate hashes

- `heads-A.png`: `d974fb3a8b41d12a26ec46c14abfad1cf21f5b7af4af6245c2e600bd05ec42ba`
- `heads-B.png`: `467704b1e8b204840dfc37c0b44a099c6e0ead38e5e7dd6ec545fdeefd8e589f`
- `heads-C.png`: `70a5010b26aba44fa552a39028ae693210e5d5bd5219db00e9b0024b1b527d05`

- `build.py`: `37e6843526018bec5c1f501f4feb8253b7a097f1905fd4c9b9ae63b5ded3a384`
- `geometry.pkl`: `3321e3644b2647bb29238898995646d29b0e1fce64851e672d8267f3b7bc2cf9`

The complete input path/hash mapping below exactly matches `inputs.json`.

<!-- review-verdict: {"status":"PASS","reviewer":"/root/maltipoo_photo_technical","artifacts":{"heads-A.png":"d974fb3a8b41d12a26ec46c14abfad1cf21f5b7af4af6245c2e600bd05ec42ba","heads-B.png":"467704b1e8b204840dfc37c0b44a099c6e0ead38e5e7dd6ec545fdeefd8e589f","heads-C.png":"70a5010b26aba44fa552a39028ae693210e5d5bd5219db00e9b0024b1b527d05"},"inputs":{"../../../.codex-attachments/768d9f11-0441-440b-a272-2d05ac586b78/6802266b-b4f1-4a70-9d32-d6584792f9da/55757.jpg":"9c439bdd4b2811a2a9f0eb578dda06909ec080a544e33071bd950b26504c3fb2","../../../.codex-remote-attachments/01a1a744-36e5-7233-ac4f-68fc9cfbfd7a/3c2fda8b-ca8a-4fff-b7e4-601bfe9eaa80/1-55765.jpg":"4ed0aa846afd7badf120f34fc2cc7bdd7e1ed6158a7c70c72ade8c7cf593afc7","../deformation-b-face-v2/golden-reference.png":"2be4a6076f6730adbbab58d68536181bf15b528898084adae17b5f49f1b032ef","../deformation-b-round-eyes-v1/round-eyes-before-after.png":"fc7f9a5626f54bc1e9e9165bc1f6187addaace903e7a8fdb7588c6adbd8fbd9c","../head-skeleton-v1/profiles.json":"aab232a82947fe4a81c6785e3c4e54ad458dca82c82a99e1aa9431ce8e29e323","../head-skeleton-volume-v2/__pycache__/raster.raster-6.py312.1.nbc":"df33acdfd671eb8eb6e6e3a3cfa5eec9a7a9e3e900720868449e60ed3d13a33a","../head-skeleton-volume-v2/__pycache__/raster.raster-6.py312.nbi":"963438c86a99e955db7538d04dc04a537669ab2ee828a4a99f3a406b92dd44a9","../head-skeleton-volume-v2/build.py":"734b85527c58a0cf9bf598867dfabbd9bddf2dd91f50b8fef9ec9fbc6733419e","../head-skeleton-volume-v2/geometry.pkl":"eaec7d20d5ea8abbb8a14e728d6120f4f119e2d3ee238d4af5b3836f06e4d154","../head-skeleton-volume-v2/profiles.json":"aab232a82947fe4a81c6785e3c4e54ad458dca82c82a99e1aa9431ce8e29e323","../head-skeleton-volume-v2/raster.py":"f2747b235362f49c94d8a7121784d5d597464723649bd1a4b951396dbb289f15","../head-skeleton-volume-v2/references.json":"ae6dd24467d04a9666b1def48ff3f7cdcbdeb9708011a08940629c6b26a93c3d","../head-skeleton-volume-v2/review-status.json":"5c9d76e0d6c23f260daf3fa4f327d9cbc2b8b4c8204567a19bcf7754a0ff7e1e","../skull-based-heads-v1/build.py":"84ff23798e2d487de2dddaa2302f15eebd292affb4dec0c9ab3690b2df410b2d","../skull-based-heads-v1/geometry.pkl":"f332953619225f439f62ba955f7d01ca9c73ac24c374f1ae06f7069e6b637b89","../skull-based-heads-v1/heads-B.png":"1858a944170e4bfa0ea6ab5662ac0287ea431b7a46e90f0dca15789490396440","build.py":"37e6843526018bec5c1f501f4feb8253b7a097f1905fd4c9b9ae63b5ded3a384","geometry.pkl":"3321e3644b2647bb29238898995646d29b0e1fce64851e672d8267f3b7bc2cf9","parameters.json":"5d534c3ab7008f55d7a2f1523b5ee921ed75f724109d12a6f0fb5e8873139230","references.json":"96874f0d9b3598bc36ad7223653af7ee001f0ec20044baaf33cf829a5e6c130c","../../private-data/breed-standing-pair-v1/dachshund-source.png":"15b7e9545051ffc8970059748f9fd8d51e7ab6d9d683b95aa22638429f026cfc","../../private-data/skull-anatomy-v2/dorsal.jpg":"f7c059883e2ca7a9ba17f48385f62485e3c2c40b4189dbfff13052b417167a10","../../private-data/skull-anatomy-v2/lateral.jpg":"df1c09fa01836ce5fc28b5c51ca7ccf1333f9a3ce129d448af866709288e9cfd","../../private-data/skull-anatomy-v2/rostral.jpg":"8d8d140502b12b2fb37cbb19b2620ee9ef03bd504a961a333417d39204192ccb","../../../../../../../Windows/Fonts/malgun.ttf":"7a183cf1c6c56b9609fcc16eda8b5229fbc11758a21e669ec00343239b02192f","../../../../../../../Windows/Fonts/malgunbd.ttf":"e8cbc0b2afcc14fb45dfb6086d5102c0b23a96e7b6e708f3122acde1b86c9082"},"coverage_complete":true,"unresolved":{}} -->
