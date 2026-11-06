# Pass11 B saved-mesh preflight

Reviewer: /root/maltipoo_photo_technical. Scope: saved B geometry only. No full reconstruction, A/C comparison, or visual verdict. This is not a final TECHNICAL=PASS or delivery authorization.

Result: the requested saved-mesh preflight checks are clear; no blocking defect found in this tested scope.

## Bone containment

All 451,162 upper/jaw vertices and triangle centroids are inside the actual saved skin using an independent +X ray-parity check. Projected triangle bounds enumerate every possible ray hit; a sub-0.00003 coordinate perturbation avoids shared-edge double counts. This samples bone surfaces; it is not an exhaustive continuous face-containment proof.

| Breed | Upper minimum clearance | Jaw minimum clearance |
|---|---:|---:|
| golden | 0.484867 | 0.716097 |
| whippet | 0.857432 | 0.566777 |
| dachshund | 1.004432 | 0.574480 |
| maltipoo | 1.118018 | 0.976368 |

Clearances are actual closest-triangle distances in model units. Every tabulated minimum is certified: the lower bound for all omitted triangles exceeds the reported minimum. Individual deep-point closest distances are not all certified and are not used as exact clearance claims.

## Surface and attachment checks

- All four skin meshes and eight eye meshes each have one connected component, Euler characteristic 2, zero boundary edges, zero nonmanifold edges, and zero zero-area faces.
- All eight eyes have actual embedded and exposed vertices/centroids, with 148–238 faces crossing the skin. Eyes remain separate closed meshes, intentionally embedded rather than fused.
- Each dark nose material patch is one connected vertex region on the same closed skin mesh, sharing 141–184 edges with adjacent skin. This verifies connection, not photographic shape accuracy.
- Each ear root has local head/ear field overlap (536–940 samples on a 0.6-unit grid) and nearby saved skin; the final skin is a single closed component. No detached ear component was found.
- Dachshund has one very small nonzero triangle near (−47.75,18.75,8.15), double area 6.343e−11. It creates no boundary, duplicate vertex index, or zero-area face. Treat as a numerical export caveat if downstream processing uses minimum-area thresholds; no silhouette or containment failure is established by this measurement.

## Evidence and pending coverage

- `review-pass11-saved-mesh.json`: topology, actual distances, eye crossing, nasal patch, ear roots, certified minimum bounds.
- `review-pass11-ray-containment.json`: independent actual mesh inside/outside classification.
- Source, cache, and image stayed unchanged during the checks.
- Pending: full independent reproduction, all three variants and isolation, transitive provenance/control-response checks, and final same-hash visual approval. No final delivery verdict is issued.

## Captured hashes

- `build.py`: `84ff23798e2d487de2dddaa2302f15eebd292affb4dec0c9ab3690b2df410b2d`
- `geometry.pkl`: `a790311f8becc7dbced2e657b7b1b80ba878069517bae9270352bc95aa6e66c0`
- `heads-B.png`: `1858a944170e4bfa0ea6ab5662ac0287ea431b7a46e90f0dca15789490396440`

- Reviewed skeletal input `../head-skeleton-volume-v2/geometry.pkl`: `eaec7d20d5ea8abbb8a14e728d6120f4f119e2d3ee238d4af5b3836f06e4d154`
