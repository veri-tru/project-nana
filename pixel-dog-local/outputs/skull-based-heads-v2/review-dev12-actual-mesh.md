# Frozen dev12 B — actual saved-mesh failure

Reviewer: /root/maltipoo_photo_technical. **FAIL — T12-01 BLOCKER: final polished skin intersects and exposes reviewed bone.** No full reproduction was run.

This checks `iterations/12` geometry after unconstrained polishing. Initial analytic fields are irrelevant to this final containment result.

| Breed | Outside bone samples | Upper/jaw crossing pairs | Maximum actual penetration |
|---|---:|---:|---:|
| golden | 640 | 40/507 | 0.305711 |
| whippet | 1625 | 0/1240 | 0.316571 |
| dachshund | 1127 | 0/922 | 0.305797 |
| maltipoo | 179 | 6/261 | 0.164214 |

Across451,162 tested bone vertices/triangle centroids,3571 samples are outside. Direct triangle/triangle diagnostics independently confirm2976 skin–bone intersecting pairs, so this is not merely a ray-parity ambiguity. Every reported outside-point nearest distance is certified by the omitted-triangle bound. Distances are model units.

The main affected region is the ventrolateral mandibular surface. Smaller upper-bone exposures also occur at Golden’s left lateral upper surface and one Maltipoo upper point. Full affected bounds, worst bone positions, and nearest skin positions are in `review-dev12-penetration-depth.json`. A smooth offset exceeding the measured peak0.316571 is a plausible repair size, but a tapered displacement must be checked anew; the measured depth is not a guarantee for a proposed offset.

Other bounded checks: all12 skin/eye surfaces remain closed single components with no boundary/nonmanifold/zero-area faces; all arrays are finite. No non-adjacent skin self-intersection or coplanar overlap was found among250,298 overlapping-AABB candidates (shared-vertex pairs excluded). All1621 black nasal coordinates remain byte-exact vs v1B, and all8 eye arrays remain exact and embedded. Those passes do not override T12-01.

Evidence: `review-dev12-saved-mesh.json`, `review-dev12-crossings.json`, `review-dev12-bone-triangle-crossings.json`, `review-dev12-penetration-depth.json`. Floating tolerances and bounded coverage are recorded in the helpers; no formal exact-arithmetic proof is claimed.

## Frozen hashes

- `iterations/12/build.py`: `23e63c78c8f315438150a00b6bcc015dfcb19e38a3129f1a75635fc8fcc545d1`
- `iterations/12/geometry.pkl`: `60a3578d5682fbec885f429f89d8f28a06c1267ae1e2a972222568c628970b2f`
- `iterations/12/heads-B.png`: `42e96c8df0c6957da60b788ab187ab656ced2b15e385bc648e8e45b889e77f06`
