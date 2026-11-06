# Independent technical review — head-skeleton-volume-v2, pass06

2026-11-06. Reviewer: `/root/maltipoo_photo_technical`. Implementer: `/root`.

**TECHNICAL = PASS.** No unresolved technical BLOCKER or MAJOR remains for the five exact candidate images below. This is a technical candidate verdict, not guardian approval, an anatomical measurement certificate, or promotion to training ground truth. Delivery still requires the matching independent visual verdict and delivery gate.

## Exact coverage

| Image | Dimensions | Direct inspection coverage |
|---|---|---|
| structure.png | 1840 × 1550 | All four breeds, side / oblique / front / top |
| jaw-motion.png | 1840 × 1130 | All four breeds at 0° / 10° / 20° |
| structure-detail.png | 1600 × 1150 | Golden side, oblique with cartilage, top, and front at 14° opening |
| jaw-detail.png | 1600 × 1440 | All four isolated mandibles, side / rear oblique / top |
| joint-detail.png | 1840 × 1120 | All four left TMJ regions at 0° / 10° / 20°, same center/scale |

I directly opened all five stored image contents. After pass06, I reopened both changed boards and checked every affected cell. The other three diagnostic files are byte-identical to the already-opened pass05 files, as confirmed against `review-pass05/evidence.json`. The cutaway board intentionally removes original triangles and leaves uncapped cut boundaries; these are not holes in the complete meshes. No finished skin, pixel simplification, dental occlusion, six facial expressions, or actual model training is included.

## Independent reproduction and data integrity

`review_reproduce.py` rebuilt all four models from current source and profiles, including the three breeds reused by the implementer's partial build. All five independently rendered PNG byte strings exactly equal the candidates. Every saved model array, normal, color, ambient-occlusion value, region label, parameter, and profile exactly equals the fresh rebuild. All four `*-regions.npz` exports match the rebuilt vertex/face/normal/region arrays, and `regions.json` exactly matches the current region dictionary. A separate check confirms `parameters.json` equals the saved model parameters. All 13 authored region IDs occur in every breed.

The source, profile, renderer, and reference manifest remained unchanged during the full run. Runtime open-file auditing captures the local renderer source, the Numba cache files actually read, and both fonts. Reference-image hashes and the previous shortened-profile hash were independently checked and included as design provenance. Evidence: `review-reproduction.json`, `review-final-auxiliary.json`, and the five images under `review-reproduction/`.

## Geometry, attachment, and articulation

- **Complete surfaces:** all 12 upper/jaw/cartilage meshes have one connected component, zero boundary edges, zero nonmanifold edges, zero zero-area triangles, and finite coordinates/normals. Jaw and cartilage Euler characteristics are 2. Upper Euler characteristics are -6 for Golden/Whippet/Dachshund and -10 for Maltipoo; shared construction is not a claim of identical mesh genus or anatomical opening counts. Normals have unit length to floating-point precision. Winding agreement with averaged vertex normals is 99.948% or higher for upper meshes and 100% for jaw/cartilage; local shading normals at sharp sampled joins are not exact face normals.
- **Anterior arch attachment:** global connectivity alone failed to catch the pass05 Maltipoo defect, so pass06 was checked locally. The explicit fixed base field excludes arches. In a 41³ grid of spacing 0.2 around each first arch point, Maltipoo has 3460 samples per side inside both volumes by more than 0.1, an approximate overlap of 27.68 model³. Its root-center base field is -0.232, compared with +4.022 and zero overlap in pass05. The other three breeds retain their previous positive overlap counts. The actual saved Maltipoo mesh also has 88 right and 93 left local shared triangle edges joining arch-tagged vertices to basal-region vertices. These checks corroborate actual local attachment, not merely screen adjacency. Evidence: `review-arch-root-overlap.json` and `review-actual-root-edges.json`.
- **Extra-handle interpretation:** the independent structural advisor `/root/skull_structure_advisor` separately extracted base-only fields at the production step and Gaussian smoothing. It reported Maltipoo base Euler unchanged at -6 between pass05 and pass06, while the complete upper surface changes from -6 to -10 when the two previously free anterior arch roots reconnect. No new base loop caused by the retained-bone patch was identified. The advisor's anatomical interpretation is attributed to that reviewer; this review independently measured the final complete-mesh topology and attachment. Full genus counts remain construction diagnostics, not anatomical targets or training labels. The reviewer-owned interpretation is preserved in `advisor-topology-review.md`.
- **Rigid jaw and fixed axis:** all jaw vertices inverse-rotate to their rest positions within 2.85e-14 at 0° / 5° / 10° / 15° / 20°. Both TMJ centers remain exactly on the same fixed transverse axis. The renderer transforms only the jaw; the upper structure is unchanged. No intermediate reinterpolation deforms the ramus or body.
- **Actual mesh clearance:** every jaw vertex and actual triangle center was tested at those five angles against the fixed upper field. Near-surface candidates were then checked against actual upper triangles, including the TMJ band rather than silently discarding it. Candidate selection allows the measured upper-field/mesh residual plus 0.2. Closest-triangle searches were certified using the centroid-distance/radius bound. No tested sample penetrates the upper mesh; the smallest sampled non-TMJ separation is 0.0401 model units (Maltipoo neutral) and the smallest TMJ-band separation is 0.6239. This is a sampled static-state test, not exhaustive continuous triangle-intersection proof for arbitrary angles. Evidence: `review-preflight.json` and `review-mesh-contact.json`.
- **Open spaces and cartilage:** nasal-lumen, oral-midline, and bilateral temporal probes are outside both upper and jaw fields for every breed. Their actual multi-view renders show the corresponding entrances/spaces. These probes do not certify a complete physiological airway. Each cartilage attachment volume has samples inside the upper support (17–38 samples below -0.05), rather than an entirely detached floating volume. This is a generic attachment scaffold, not a finished nasal-leather shape.
- **Smoothing tolerance:** production uses a 0.65 sampling step and 0.5-voxel Gaussian smoothing. Maximum absolute upper-mesh residual against the analytic field is about 0.49–0.59 model units, while the 95th percentile is much smaller. The earlier posterior-cap discontinuity with Whippet residual 4.264 is resolved. Clearance conclusions above use actual triangle surfaces, not a blanket exemption for analytic-field residuals. Ambient occlusion changes shading only; cavity/attachment checks use geometry and fields directly.

## Preserved inputs and real controls

Current `profiles.json` is byte-identical to the prior user-requested shortening input in `head-skeleton-v1`: dorsal anchors, widths, and hinge locations remain unchanged, including Maltipoo's retained muzzle length. Newly authored wall thicknesses, arch offsets, medial ramus curvature, short-face anterior reach, and recesses are not represented as unchanged surface dimensions or measured anatomy.

Five +0.75 control perturbations were independently extracted on a fixed grid using Golden's shared construction path. Crown height, forehead height, derived maxillary width, and nasal-base X each change the actual upper mesh; soft nose-tip X changes the cartilage mesh. Maximum field responses at the original surface are 0.750, 0.767, 0.615, 0.750, and 0.748 respectively. All fresh meshes differ from the baseline; the test does not count a shifted extraction grid as a control effect. The maxillary dependency is derived from profile parameters, not an independently implemented named maxilla joint. These tests validate the stated parameter path, not arbitrary parameter combinations or every breed-specific perturbation.

## Source authority, limits, and earlier failures

I directly opened the three hashed IMAIOS lateral/dorsal/rostral reference images. They support inspection of broad relationships; no CT segmentation, registration, matched-breed measurement, or biological dimension extraction was performed. The four profiles and support dimensions are authored. Region IDs are construction labels classified by source rules, not validated anatomical segmentation ground truth. README/anatomy-evidence wording is review context rather than a rendering dependency. No reference-image pixels are copied into the candidate boards.

Pass03 cap/collision failures, pass04 remaining ramus collisions, and pass05's detached anterior Maltipoo arch are preserved under `review-pass03/`, `review-pass04/`, and `review-pass05/`. The interrupted pass05 full reproduction is explicitly recorded as incomplete and is not counted toward this verdict. Pass06 closes those findings through fresh saved-surface and reproduction checks. A separate matching visual review remains responsible for gross anatomical appearance and surface-quality findings.

The recorded environment is Python 3.12.10 with NumPy 1.26.4, SciPy 1.17.1, scikit-image 0.26.0, Pillow 12.2.0, and Numba 0.68.0. Exact reproduction is demonstrated in this environment with the recorded cache/fonts; cross-platform or cache-free identity is not claimed.

## Final hashes

- `structure.png`: `6079e3c79447d6e56f70fde26701fff23a9218503f3992d6486aec5feeb5b6de`
- `jaw-motion.png`: `a7eeae38412d17ed7c44b5ac5e393f4fd7765b7058973709bab5cafa1f79079f`
- `structure-detail.png`: `f4b82cb52db856372ed7b1f69cae9733516e6fbfd22bc086ac2c76af6487fe59`
- `jaw-detail.png`: `b655e686eba6966a4fbc4fe9c12455e4c59475e2f809c214242e30cff3317841`
- `joint-detail.png`: `68cb5cfe56b939c30849e247506a194322e7fb4c215d87abd53bb7d9697effac`

Saved geometry: `eaec7d20d5ea8abbb8a14e728d6120f4f119e2d3ee238d4af5b3836f06e4d154`.

## Transitive generation and design-provenance inputs

- `../head-skeleton-v1/profiles.json`: `aab232a82947fe4a81c6785e3c4e54ad458dca82c82a99e1aa9431ce8e29e323`
- `__pycache__/raster.raster-6.py312.1.nbc`: `df33acdfd671eb8eb6e6e3a3cfa5eec9a7a9e3e900720868449e60ed3d13a33a`
- `__pycache__/raster.raster-6.py312.nbi`: `963438c86a99e955db7538d04dc04a537669ab2ee828a4a99f3a406b92dd44a9`
- `build.py`: `734b85527c58a0cf9bf598867dfabbd9bddf2dd91f50b8fef9ec9fbc6733419e`
- `profiles.json`: `aab232a82947fe4a81c6785e3c4e54ad458dca82c82a99e1aa9431ce8e29e323`
- `raster.py`: `f2747b235362f49c94d8a7121784d5d597464723649bd1a4b951396dbb289f15`
- `references.json`: `ae6dd24467d04a9666b1def48ff3f7cdcbdeb9708011a08940629c6b26a93c3d`
- `../../private-data/skull-anatomy-v2/dorsal.jpg`: `f7c059883e2ca7a9ba17f48385f62485e3c2c40b4189dbfff13052b417167a10`
- `../../private-data/skull-anatomy-v2/lateral.jpg`: `df1c09fa01836ce5fc28b5c51ca7ccf1333f9a3ce129d448af866709288e9cfd`
- `../../private-data/skull-anatomy-v2/rostral.jpg`: `8d8d140502b12b2fb37cbb19b2620ee9ef03bd504a961a333417d39204192ccb`
- `../../../../../../../Windows/Fonts/malgun.ttf`: `7a183cf1c6c56b9609fcc16eda8b5229fbc11758a21e669ec00343239b02192f`
- `../../../../../../../Windows/Fonts/malgunbd.ttf`: `e8cbc0b2afcc14fb45dfb6086d5102c0b23a96e7b6e708f3122acde1b86c9082`

The manifest and private reference images are manual design provenance, not images parsed by the generator. Package versions and the actual imported renderer/cache/fonts describe the execution path.

<!-- review-verdict: {"status":"PASS","reviewer":"/root/maltipoo_photo_technical","artifacts":{"structure.png":"6079e3c79447d6e56f70fde26701fff23a9218503f3992d6486aec5feeb5b6de","jaw-motion.png":"a7eeae38412d17ed7c44b5ac5e393f4fd7765b7058973709bab5cafa1f79079f","structure-detail.png":"f4b82cb52db856372ed7b1f69cae9733516e6fbfd22bc086ac2c76af6487fe59","jaw-detail.png":"b655e686eba6966a4fbc4fe9c12455e4c59475e2f809c214242e30cff3317841","joint-detail.png":"68cb5cfe56b939c30849e247506a194322e7fb4c215d87abd53bb7d9697effac"},"inputs":{"../head-skeleton-v1/profiles.json":"aab232a82947fe4a81c6785e3c4e54ad458dca82c82a99e1aa9431ce8e29e323","__pycache__/raster.raster-6.py312.1.nbc":"df33acdfd671eb8eb6e6e3a3cfa5eec9a7a9e3e900720868449e60ed3d13a33a","__pycache__/raster.raster-6.py312.nbi":"963438c86a99e955db7538d04dc04a537669ab2ee828a4a99f3a406b92dd44a9","build.py":"734b85527c58a0cf9bf598867dfabbd9bddf2dd91f50b8fef9ec9fbc6733419e","profiles.json":"aab232a82947fe4a81c6785e3c4e54ad458dca82c82a99e1aa9431ce8e29e323","raster.py":"f2747b235362f49c94d8a7121784d5d597464723649bd1a4b951396dbb289f15","references.json":"ae6dd24467d04a9666b1def48ff3f7cdcbdeb9708011a08940629c6b26a93c3d","../../private-data/skull-anatomy-v2/dorsal.jpg":"f7c059883e2ca7a9ba17f48385f62485e3c2c40b4189dbfff13052b417167a10","../../private-data/skull-anatomy-v2/lateral.jpg":"df1c09fa01836ce5fc28b5c51ca7ccf1333f9a3ce129d448af866709288e9cfd","../../private-data/skull-anatomy-v2/rostral.jpg":"8d8d140502b12b2fb37cbb19b2620ee9ef03bd504a961a333417d39204192ccb","../../../../../../../Windows/Fonts/malgun.ttf":"7a183cf1c6c56b9609fcc16eda8b5229fbc11758a21e669ec00343239b02192f","../../../../../../../Windows/Fonts/malgunbd.ttf":"e8cbc0b2afcc14fb45dfb6086d5102c0b23a96e7b6e708f3122acde1b86c9082"},"coverage_complete":true,"unresolved":{}} -->
