# Independent technical review — head-neck-volume-v2, pass 09

2026-11-05. Reviewer: `/root/volume_technical_review`. Implementer: `/root`.

**TECHNICAL = PASS.** No unresolved technical BLOCKER or MAJOR remains for the four hashed candidate boards below. This is a technical candidate-review verdict, not VISUAL approval, guardian approval, a likeness determination, or delivery authorization by itself. A separate matching VISUAL PASS is still required by `docs/visual-review-policy.md`.

The generator was read-only throughout review. Reviewer files contain tests, diagnostics and reproduction results. Earlier failed measurements are preserved in `review-geometry-initial.json`, `review-geometry-pass04.json` and `review-scope-pass04.json`; pass 08 evidence remains separately identified. The interrupted pass 08 reproduction is not counted as a completed check.

## Exact review coverage

All four final PNG files were directly opened after pass 09 was saved. Every breed column and every row was inspected for technical attachment/contact and output coverage. These are actual projections of the same saved 3D geometry, not painted substitute viewpoints.

| File | Size | Four-breed coverage |
|---|---|---|
| views.png | 1600 × 1020 | Neutral side, front, oblique |
| attachments.png | 1600 × 1320 | Neutral rear, top, ears-hidden side and oblique |
| expressions.png | 1600 × 2220 | Neutral, half eyelid, closed eyelid, half mouth opening, full opening, tongue, nose lick; oblique |
| mouth-side.png | 1600 × 1620 | Neutral, half/full opening, tongue, lick; ears hidden, side |

Golden, Whippet, Dachshund and Maltipoo are all included. Reviewer detail crops and archived iterations are diagnostic evidence, not additional candidate-delivery artifacts. No animation, 64×64 pixel asset, device result, or photo-measured anatomy is claimed.

## Reproduction and input authority

`python outputs/head-neck-volume-v2/review_audit.py --reproduce` independently rebuilt all geometry and boards. All four PNG byte strings exactly match the saved candidates. Every saved state geometry array and each saved rig match the independent rebuild exactly. Generator SHA-256 remained unchanged throughout the run.

The runtime audit captures transitive local imports, loaded JSON inputs, the font actually used, and the two Numba raster cache files actually read. Cached Python bytecode resolves to its source file. Recursive module inspection supplements the open-file audit. The 20-entry input set below and in the verdict marker is authoritative; it includes more than the top-level generator. Package versions were read from the running environment: Python 3.12.10, NumPy 1.26.4, SciPy 1.17.1, scikit-image 0.26.0, Pillow 12.2.0 and Numba 0.68.0. `requirements.txt` documents this environment; it was not read by the generator. Cross-platform or cache-free reproducibility was not claimed.

Evidence: `review-reproduction.json`, `review-final-checks.json`, and the read-only reproduction images under `review-reproduction/`. Inspection scripts are `review_audit.py`, `review_final_checks.py`, `review_geometry.py`, and `review_scope.py`.

## Structural and scope findings

- **Unified head/neck surface:** all four head meshes and all four independent jaw meshes have one connected component, zero boundary edges, zero nonmanifold edges and Euler characteristic 2. Every triangle has positive area; all vertices/normals are finite. Normals have unit length to float precision and agree with triangle winding. Six head triangles have very small positive area below 1e-10, but none has zero area or invalid normals. This is documented numerical conditioning, not a disconnected or torn surface.
- **Controls actually drive the volume:** each of occipital joint, C1, C2 and lower neck was independently perturbed by +0.75 in Y with direct-child compensation. Every head/face world node stayed fixed within 8.9e-16. The actual saved surface samples changed implicit field values by maxima 0.136–0.750; thousands of surface samples responded to each control. This tests the volume evaluator at actual mesh vertices; it is not a claim that a new animated cervical skeleton was implemented.
- **TMJ and mandible:** left/right hinge centers share the rotation-axis XY exactly and sit inside both the head volume and ramus capsules. Head-field values at hinges range from -0.657 to -2.455; jaw-field values range from -0.588 to -1.078. The whole jaw is rigidly transformed in all seven states; inverse rotation error is at most 7.11e-15. Upper-head geometry is identical across all states.
- **Mouth aperture:** rostral jaw surfaces forward of the mouth-corner transition are clear in half/full opening for all breeds. Minimum open-state clearance is 0.560 or greater; half-opening clearance is 0.383 or greater. Closed-state minimum residual is -0.01490 for Maltipoo and about 6.5e-5 or smaller for the other breeds. The posterior ramus is intentionally embedded under the cheek and is not required to be collision-free from that surrounding volume. Actual ears-hidden side/oblique boards show the exposed oral opening without a wall joining the moving jaw to the fixed roof.
- **Tongue support and contact:** both vertices and quad centers were tested against the posed jaw and fixed head. Worst tongue/jaw residual is -0.00167 and worst tongue/head residual is -0.00567. There are zero samples deeper than 0.1 in either volume. Interior underside samples contact the floor closely; Maltipoo has some local lift up to 0.180 while retaining supporting contact elsewhere. Tongues retain finite thickness (maximum vertical thickness 0.640) and closed angular seams below 4.1e-16. All four lick tips meet the head surface within 8.8e-7 field residual. No previous gross jaw penetration or nose penetration remains.
- **Shared nose family:** the source dark nasal material was sampled directly rather than inferred from unchanged constants. Maltipoo nasal material ends at depth 2.343; rebuild starts at 2.55 and front-pad widening at 2.80. Zero source dark nasal samples fall in its rebuild. The remeshed nose is not vertex-identical: all breeds have absolute field residual p95 0.099–0.1085, maximum 0.1281, consistent with the common 0.20 grid and 1.2-cell Gaussian smoothing. The earlier Maltipoo residual of 1.061 and direct overlap of about 34% of dark source samples are resolved.
- **Preservation:** all face/head world node coordinates and eye radii match the prior baseline. Golden, Whippet and Dachshund ear surfaces and materials are exactly unchanged. Maltipoo ears are explicitly rebuilt, not represented as preserved source geometry. Every ear stays fixed across expressions. Actual-root samples from the first five ear sections have zero angular seam error, finite coordinates and inward nearest-surface-normal projections on the current head; this is a local attachment diagnostic, not exact signed-distance proof. See `review-ear-attachments.json`.

## Disposition and limits

The development tongue penetration, Maltipoo nasal-family mutation and exposed closed-jaw overlap are resolved at the tested resolution. No unresolved technical findings remain. Geometry is authored stylization; control coordinates and jaw dimensions are not measured anatomical facts. The implicit field combines EDT, smoothing and analytic unions/cuts, so its values are proximity diagnostics rather than globally exact physical distances. Tests cover the saved static states and the specified control perturbations, not arbitrary poses or continuous animation. These limitations do not turn a visual failure into technical success or replace the separate visual review.

## Artifact hashes

- `views.png`: `ad625378de94d723e30bf6aaefbed49193c6cd672531947a3da2e383e9340369`
- `attachments.png`: `5fa54baa1cb12d11eb6f2c2404dc1f52f05531d81e3c011762dbaa9cdd33fd5e`
- `expressions.png`: `b99527e00b59ae5b1b1995696fdb261940e013907195e6dd17740978bb10f584`
- `mouth-side.png`: `e39c718ce287ae0c9dd93726deaa0e6d5b95bc5a34194cdacc0d439437442605`

Saved geometry: `ab2dc6545a7fbf28e45529ea2db1e97fa4697ef6b739302e9bad778f473c4ca4`. Generator: `cdab4db38cb579e46a4b01ae7a3803f59d960af281b49fc464ffea5ff8cf150b`.

## Transitive generation input hashes

- `../cranio-cervical-v1/expressions.py`: `b24a4f6fb1ade495aa9809387410f654e497f97a4b5d96125bb326a3591c6c6a`
- `../cranio-cervical-v1/head_surface.py`: `641698f6b62ebe2bc14f6eeeaae6089b1f2c0f20659d2fb86d4f64f3803bd221`
- `../cranio-cervical-v1/preview.py`: `ccebfccc71a6ebbc86d6a8e64c3cbe12da7da17ff4c054c5ad3294a5c70b436a`
- `../deformation-b-expressions-simple-v1/preview.py`: `bf8644368beaaea677bd82cb5760520951064373c59bdfdc58b1637ce0cabbe6`
- `../deformation-b-face-v2/__pycache__/preview.raster-207.py312.1.nbc`: `a0c63699688705eccd3044b02db4443cc7ca1080fcc6d654c6f107a7a0a3f795`
- `../deformation-b-face-v2/__pycache__/preview.raster-207.py312.nbi`: `104c3fcd47e7cd24949df8dfa852ccbfe5d4fe9069bf510beb714ec2b2ae93f7`
- `../deformation-b-face-v2/preview.py`: `937e27122d0231a6745bc2329aff07db01d5665b48d1efd24ed027022b7e4b19`
- `../deformation-b-face-v3/B.json`: `f20990163e6763af041308b12bc703b6b12d0430da2d966714da52be15cf2e9c`
- `../deformation-b-face-v3/preview.py`: `9da720d13f6472359bd2882bbc390a1f70c7b9e4e28206db3d9eb88f489db11e`
- `../deformation-b-face-v3/profiles.json`: `1a574306a6bf8eb010ed98a8f3711dfcc22decb55d6fdf6d2a754a3e4e3f995a`
- `../deformation-b-heads-v1/preview.py`: `0041692ee9f25fc1e4dd179f5952efe8dc12ec95330f843a0448b1eca0d025c2`
- `../deformation-b-round-eyes-v1/preview.py`: `29ccbb7a79694540ceabe72311d5b86062177c6396477fe64cb2eb388cb62e24`
- `../deformation-rig-b-v1/B.json`: `fabc3715d0f6af6ac38d1fbd8a9dcc56975d3757cb73b1bf35379d372b9a306e`
- `../deformation-rig-b-v1/preview.py`: `9d7d9beefa043b1c08caac1a86b05a688b88664265f301c5dbedcf2a056ff1f3`
- `preview.py`: `cdab4db38cb579e46a4b01ae7a3803f59d960af281b49fc464ffea5ff8cf150b`
- `../heads-necks-four-v1/head_surface.py`: `641698f6b62ebe2bc14f6eeeaae6089b1f2c0f20659d2fb86d4f64f3803bd221`
- `../heads-necks-four-v1/preview.py`: `5a64539f866de6653101f30066059fab97663a08f6b39d2a2d6a344a4b6e23af`
- `../integrated-rig-b-v1/build.py`: `e72f1c02c4517dd4a07d4d24e8b2c7d564448c285dfe58433c5ce903fd43efbd`
- `../integrated-rig-b-v1/preview.py`: `dd32361f84e4eb281ad1472bb48a8f3fd203d26d5e247febee2d2b7481fd4d4a`
- `../../../../../../../Windows/Fonts/malgunbd.ttf`: `e8cbc0b2afcc14fb45dfb6086d5102c0b23a96e7b6e708f3122acde1b86c9082`

<!-- review-verdict: {"status":"PASS","reviewer":"/root/volume_technical_review","artifacts":{"views.png":"ad625378de94d723e30bf6aaefbed49193c6cd672531947a3da2e383e9340369","attachments.png":"5fa54baa1cb12d11eb6f2c2404dc1f52f05531d81e3c011762dbaa9cdd33fd5e","expressions.png":"b99527e00b59ae5b1b1995696fdb261940e013907195e6dd17740978bb10f584","mouth-side.png":"e39c718ce287ae0c9dd93726deaa0e6d5b95bc5a34194cdacc0d439437442605"},"inputs":{"../cranio-cervical-v1/expressions.py":"b24a4f6fb1ade495aa9809387410f654e497f97a4b5d96125bb326a3591c6c6a","../cranio-cervical-v1/head_surface.py":"641698f6b62ebe2bc14f6eeeaae6089b1f2c0f20659d2fb86d4f64f3803bd221","../cranio-cervical-v1/preview.py":"ccebfccc71a6ebbc86d6a8e64c3cbe12da7da17ff4c054c5ad3294a5c70b436a","../deformation-b-expressions-simple-v1/preview.py":"bf8644368beaaea677bd82cb5760520951064373c59bdfdc58b1637ce0cabbe6","../deformation-b-face-v2/__pycache__/preview.raster-207.py312.1.nbc":"a0c63699688705eccd3044b02db4443cc7ca1080fcc6d654c6f107a7a0a3f795","../deformation-b-face-v2/__pycache__/preview.raster-207.py312.nbi":"104c3fcd47e7cd24949df8dfa852ccbfe5d4fe9069bf510beb714ec2b2ae93f7","../deformation-b-face-v2/preview.py":"937e27122d0231a6745bc2329aff07db01d5665b48d1efd24ed027022b7e4b19","../deformation-b-face-v3/B.json":"f20990163e6763af041308b12bc703b6b12d0430da2d966714da52be15cf2e9c","../deformation-b-face-v3/preview.py":"9da720d13f6472359bd2882bbc390a1f70c7b9e4e28206db3d9eb88f489db11e","../deformation-b-face-v3/profiles.json":"1a574306a6bf8eb010ed98a8f3711dfcc22decb55d6fdf6d2a754a3e4e3f995a","../deformation-b-heads-v1/preview.py":"0041692ee9f25fc1e4dd179f5952efe8dc12ec95330f843a0448b1eca0d025c2","../deformation-b-round-eyes-v1/preview.py":"29ccbb7a79694540ceabe72311d5b86062177c6396477fe64cb2eb388cb62e24","../deformation-rig-b-v1/B.json":"fabc3715d0f6af6ac38d1fbd8a9dcc56975d3757cb73b1bf35379d372b9a306e","../deformation-rig-b-v1/preview.py":"9d7d9beefa043b1c08caac1a86b05a688b88664265f301c5dbedcf2a056ff1f3","preview.py":"cdab4db38cb579e46a4b01ae7a3803f59d960af281b49fc464ffea5ff8cf150b","../heads-necks-four-v1/head_surface.py":"641698f6b62ebe2bc14f6eeeaae6089b1f2c0f20659d2fb86d4f64f3803bd221","../heads-necks-four-v1/preview.py":"5a64539f866de6653101f30066059fab97663a08f6b39d2a2d6a344a4b6e23af","../integrated-rig-b-v1/build.py":"e72f1c02c4517dd4a07d4d24e8b2c7d564448c285dfe58433c5ce903fd43efbd","../integrated-rig-b-v1/preview.py":"dd32361f84e4eb281ad1472bb48a8f3fd203d26d5e247febee2d2b7481fd4d4a","../../../../../../../Windows/Fonts/malgunbd.ttf":"e8cbc0b2afcc14fb45dfb6086d5102c0b23a96e7b6e708f3122acde1b86c9082"},"coverage_complete":true,"unresolved":{}} -->
