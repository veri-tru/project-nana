# Dev10 B actual saved-mesh audit

Reviewer: /root/maltipoo_photo_technical. Bounded development check; no full reproduction or final delivery verdict. Dev10 remains subject to the independent visual findings.

The requested geometry checks found no blocking containment, topology, or crossing defect. All tests use the relaxed saved mesh, not the initial analytic field.

- All 451,162 upper/jaw vertices and triangle centroids are inside the final skin by projected-triangle ray parity.
- Direct skin/bone triangle intersection diagnostics found zero intersections, including the 280 overlapping-AABB candidate pairs. This addresses cuts between the sampled bone vertices/centroids.
- Every skin and eye mesh is one closed component, Euler2, with zero boundary edges, nonmanifold edges, zero-area faces, or near-zero faces at the stated1e−10 diagnostic double-area threshold. All arrays are finite.
- Non-adjacent skin-triangle tests found no intersections or positive-area coplanar overlaps among249,722 overlapping-AABB pairs. Pairs sharing a vertex are excluded; floating-tolerance diagnostics are not a formal exact-arithmetic proof of every possible self-contact.
- All1,621 black nasal vertex coordinates, sorted lexicographically, are byte-identical to v1B. This is a coordinate claim; regenerated normals and rendered shading are not claimed identical.
- All8 eye meshes have exactly the same v/f/n/c arrays as v1B and remain partly embedded in the final skin, with146–236 crossing faces each.

The current source advanced to dev11 after these checks. The finished tests had stable hashes at execution, and the archived dev10 source/cache/image now match them exactly. The final direct skin/bone triangle check read the frozen `iterations/10/geometry.pkl`. No result is inherited by dev11.

Evidence: `review-dev10-saved-mesh.json`, `review-dev10-crossings.json`, and `review-dev10-bone-triangle-crossings.json`.

## Frozen dev10 hashes

- `iterations/10/build.py`: `2f0fa0573af072a9fb8bd7702fbb7aae6bfaad5a489083bd49ec8f756dc9747f`
- `iterations/10/geometry.pkl`: `643a4b1b7444ca71ff64cc4c7dac5e9babb51c4d056a5cd74bc6bed70b7c8931`
- `iterations/10/heads-B.png`: `7cfa4ab5dce70cf80479a1756f99fd434df2544783f8f4db1f02e838a7a675f1`
