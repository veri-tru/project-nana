# Independent technical review — Jack Russell B2 concept

Reviewer: `/root/jack_pixel_technical`  
Date: 2026-11-06  
Decision: **PASS for the saved high-resolution concept candidate**, with one MINOR limitation below. This is not user selection, native64 certification, or a claim that image generation preserved a mesh exactly.

## Direct inspection and coverage

Opened the actual `comparison.png` and inspected all 15 cells, including the entire silhouette, nose/muzzle support, lower jaw/neck continuity, ear-root overlap, eye shapes, coat boundaries, and each row's corresponding views. Opened the actual canonical B2 sheet, selected Golden sheet, Jack exterior sheet, Jack skeleton sheet, and FCI cover photos. Compared the Jack exterior and skeleton **row B** as the shape lineage; A/C geometry was not adopted.

| Row | SIDE | 3-4 | FRONT | BACK | TOP |
| --- | --- | --- | --- | --- | --- |
| A | inspected | inspected | inspected | inspected | inspected |
| B | inspected | inspected | inspected | inspected | inspected |
| C | inspected | inspected | inspected | inspected | inspected |

All 15 cells are present and uncropped. Each shows the same authored white head and tan small folded ears; no tan crown patch or additional spot is introduced between views. Rounded dark eye clusters and attached dark noses are readable. The muzzle stays substantial and elongated, the brow modest, and the closed jaw joins a short supported neck. No visible nose detachment, beak taper, suspended ear, open seam, or severe head/neck volume discontinuity was found. The frontal/back ear silhouettes remain short rather than hanging retriever ears. The large connected beige shadow areas and warm outline fit the current B2 concept treatment; B is lighter and C deeper than A.

The 3-4 view is shallow and close to SIDE, while TOP is a stylized overhead depiction. These are image-generated views comparable to the current B2/Golden concept layout, **not measured camera projections or proof of one shared 3D surface**. The source 3D board has actual five-view renders; this generated output does not inherit that technical property. Hidden contacts, jaw animation, collision behavior, and true orthographic correspondence are not certified by this review. No new jaw-motion or anatomy-engine completion is claimed in the deliverable.

## Source, isolation, and verification

- Recomputed SHA-256 for the one artifact and all 13 evidence inputs: all match `evidence.json`.
- Independently read the original file named by `source.json`: it exists, its hash is `1973bd6f58c8766286d09fe9e4f4eef7f36206ddb6e1e7b44828fa3bd39ce1c3`, and its bytes are identical to `comparison.png`. The saved image is RGB, **1536 x 1024**. No image processing step is evidenced between that original and the delivered copy.
- `generation.json` records built-in image_gen, the complete prompt, the three actual reference paths in their declared order, and a nontransparent background. The available provenance records and parent tool invocation report agree. A model-internal seed/version or deterministic re-execution guarantee is not available; byte-copy reproducibility is established, generative rerun identity is not.
- The canonical manifest is `USER_SELECTED_STYLE_REFERENCE` and its sheet hash matches. Its scope is visual treatment, not old Golden anatomy.
- Golden `selection.json` selects **row A of the current board**, with that board's matching hash and adult-B geometry. This does not select Jack geometry A or transfer Golden anatomy.
- Jack source `review-status.json` remains PENDING for user choice, READY for delivery, with independent technical/visual PASS and its recorded MINOR crease. This generated study does not change that selection status.
- Recomputed all **25 indirect source-input hashes** pinned by the Jack source review status, including A/B/C model files, parameters, build sources, shared renderer inputs, anatomy/reference files, and fonts: **zero mismatches**. The directly pinned Jack model B, parameters B, source boards and source status also match. This supports source isolation; expensive unchanged engine tests were not rerun and are not represented as newly executed.
- `README.md` distinguishes authored coat from a real dog's identity and names the high-resolution scope. It explicitly avoids native64, five-color, integer-grid, exact-mesh-projection, and pixel-exact shape-invariance claims. Those remain unverified runtime targets rather than completion claims.

## Finding

**JPT-01 — MINOR — comparison.png / A-B-C / corresponding SIDE, 3-4, FRONT, BACK, TOP silhouettes and feature clusters.**

Direct observation: A/B/C retain the same overall design and principal feature placement, but individual stepped contour segments, ear edges, and small feature clusters are not exact translated duplicates. For example, the far ear in 3-4 and crown/cheek stair steps differ slightly across rows. The stated generation intent is shadow-only variants; the actual image is therefore a visually consistent shadow comparison, not a strictly controlled pixel-difference experiment. The README already discloses small image-model contour variation. The differences do not introduce another muzzle-length option, change coat identity, or visibly break structure, so they are MINOR at this concept scope. Do not describe these rows as mathematically identical silhouettes. To close this finding in a future strict comparison, reuse the same verified silhouette/feature mask and vary only shadow values/coverage, then inspect all views again.

No unresolved BLOCKER or MAJOR finding. The image and these limitations require the separate independent visual review and final delivery gate before delivery. User approval remains PENDING.

<!-- review-verdict: {"status": "PASS", "reviewer": "/root/jack_pixel_technical", "artifacts": {"comparison.png": "1973bd6f58c8766286d09fe9e4f4eef7f36206ddb6e1e7b44828fa3bd39ce1c3"}, "inputs": {"generation.json": "47ed2c2f72b7fc7064809d8051904b8f0d2fcf4c2d7fb70993d1c7da126d32d4", "source.json": "ef4e8f966deeef38a82cd5cd7b97c7b0d11f63ab5cdb3683da111c61d76b00d9", "../../references/styles/breed-head-b2/v1/reference-sheet.png": "e15a82616528b4f05c51acc369ae4cbc25f6ffc781f1b1e11b1aea3f7fb1a3d6", "../../references/styles/breed-head-b2/v1/manifest.json": "b4b663e1bdc45968d34e50a7e5035f6b826e9400e165f29942e4e11d25938c86", "../golden-b2-canonical-20261106/comparison.png": "7f3a47af0bcb09237bf2881a1bd5221e8a19eb1c4fa2669e584db5e41575d31f", "../golden-b2-canonical-20261106/selection.json": "410778e309cca85c610cf153588cfd4fa352d2cbf77abcf30b328263e81c5cc4", "../jack-russell-head-v1/exterior-comparison.png": "fdb3b2848b4307bdd58133c61a2e8c9eb738a1abef681f9126ece6b553ca7f78", "../jack-russell-head-v1/skeleton-comparison.png": "64a3f7614649db565aae1fef250b71110d4f51368ecb01320af6dd64b177b475", "../jack-russell-head-v1/model-B.pkl": "41f66238527a282df6d395924e4033c39bd35ae7788d3967370a45857b600dd7", "../jack-russell-head-v1/parameters-B.json": "a4914dfbc09881ef12ade90417594ec979f4ba85fb9411acb5c05347748bc102", "../jack-russell-head-v1/review-status.json": "ae727650ed59db9320aa48a03a1e92410f8556987eb384e4efa0de742310568f", "../../private-data/jack-russell-reference-v1/fci-cover.png": "7ab90054ac93ec2f7505ca7c15aab1e5bb3b93260270caab792a56a009c5b171", "../../private-data/jack-russell-reference-v1/fci-345.pdf": "189825f27731344a5c728538786c9184a3b6db7124521b91b9f2eda9f1d8dd01"}, "coverage_complete": true, "unresolved": {"JPT-01": "MINOR"}} -->
