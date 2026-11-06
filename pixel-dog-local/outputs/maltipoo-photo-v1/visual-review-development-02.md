# Independent visual re-review - development 02

Verdict: **FAIL**. Reviewer: `/root/maltipoo_photo_visual`.

All five saved boards were directly opened. The four common boards were reviewed across all 76 cells as in development 01; `maltipoo-detail.png` adds basic/open/tongue-out states in side/front/oblique, 9 cells. Total: 85 directly inspected cells. Both user photos had already been opened directly with photo 1 for basic shape and photo 2 for mouth/tongue only. This re-review received the implementer's concern about a separate neutral lower-lip plate before viewing, so it is not described as a fully blinded second assessment. No technical verdict was supplied. The first pass remains preserved separately.

## V01 - MAJOR - unresolved separated lip/chin silhouette

Files: `views.png`, `attachments.png`, `expressions.png`, `mouth-side.png`, `maltipoo-detail.png`; Maltipoo basic and eye states; front, oblique and side.

Direct observation: neutral lower jaw remains a separate horizontal oval/plate beneath the face. The upper muzzle is a broad upright rounded disk encompassing much of the lower face, with a narrow projecting strip below the nose. The lower piece attaches at the transition where that facial disk abruptly narrows to the neck. In side view there are still two protruding lobes instead of a cohesive short fur muzzle. Removing the dark neutral mouth color has made the detached-looking plate more obvious; it has not corrected the volume relationship.

Photo 1 basis: the actual trimmed coat gives low rounded muzzle masses at the sides of the nose, blending into cheek and chin. The requirement is these large simplified shapes, not realistic hair texture. The current strong concentric facial disk and separate lip oval do not convey that structure.

Recheck condition: neutral front/oblique/side must read as one short rounded muzzle envelope with a small closed mouth and supported chin. The lower jaw may remain independently articulated internally, but it must not resemble an object attached to the neck or a separate plate in the visible silhouette.

## V02 - resolved for this snapshot

The nose-lick tongue in `expressions.png` is now a continuous pink path from the mouth to the nose in the oblique view. The side diagnostic is also continuous. This resolves the development-01 occlusion/split appearance for the currently saved hashes only.

## V03 - MAJOR - open mouth reads as low horizontal slot

Files: especially `maltipoo-detail.png` open front and oblique; also open/tongue states of `expressions.png`.

Direct observation: the area between the underside of the upper muzzle and the rotated lower jaw remains substantially cream colored in front and oblique, while the dark oral region is restricted to a thin horizontal oval immediately on the lower jaw. The result reads as a low mouth slot below a solid lower face, rather than an open cavity immediately below the muzzle. The detail board newly makes this relationship clear. The tongue is supported on the lower region, but does not cure the location/depth problem.

Photo 2 basis: the visible mouth has clear dark vertical depth directly beneath the nose/muzzle, surrounded at the sides and below by fur; the tongue emerges from its floor. The user's previous concern about a face filling an open mouth also applies to the current visible state.

Recheck condition: front/oblique mid and full opening should show an actual legible oral cavity between upper muzzle and lower jaw, with jaw/chin support at the correct location. A painted black patch is not sufficient evidence of corrected hidden geometry. Check the neck/face surface behind the cavity and use the same real model in side and front diagnostics.

## Visual/code distinction

After recording the image findings, `preview.py` was read. The large facial ellipsoids, the separate jaw beard ellipsoid and avoidance carving, and the head/neck union behind the mouth are candidate contributors to the observed shape. This is an implementation hypothesis, not measured geometry proof. The visual findings above are independently supported by the displayed boards.

Ear volume, rear/head-neck continuity, and the three other dogs show no newly identified major visual change. Byte identity and topology are deferred to the separate technical reviewer. Static coverage does not establish animation continuity or owner likeness approval.

<!-- review-verdict: {"status": "FAIL", "reviewer": "/root/maltipoo_photo_visual", "artifacts": {"review-snapshot-02/attachments.png": "ec29153ade030928d97a1ba1b8ea3ac7bda17a217606b461e3f9db855b235687", "review-snapshot-02/expressions.png": "1613f2a9c15442f0e73e80a63a0cc4cd9e3cc4a10c0ecc257c14c62d37cf3aef", "review-snapshot-02/maltipoo-detail.png": "69c096fc3c4eaba74d8293fa1c73225c394dfa397d4af8805545a78cec993710", "review-snapshot-02/mouth-side.png": "0d3091a4d2280abccb6f27f4b103281cffaba3496aa356dcc95ad2a18538cc07", "review-snapshot-02/views.png": "f23dd80db19e7bb3984d6f662b00c26671e3188d8d6f94f48c957b4f09bf5327"}, "coverage_complete": true, "unresolved": {"V01": "MAJOR", "V03": "MAJOR"}} -->
