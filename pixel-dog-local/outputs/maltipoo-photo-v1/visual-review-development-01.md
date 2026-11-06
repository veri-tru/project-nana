# Independent visual review - development 01

Reviewer: `/root/maltipoo_photo_visual`. Verdict: **FAIL**, candidate delivery blocked.

This is a direct visual review of the four saved development images in `review-snapshot-01`, not an inherited verdict. Both user photographs were opened directly. Photo 1 supplies the basic trimmed head shape; photo 2 supplies only mouth and tongue reference. The selected round eyes, common nose family, stylized B head, and head-plus-short-neck scope remain applicable. Photorealistic fur and full-body work are not required.

The repository reading requirements exposed historical baseline v2 verdict text in README/handoff. No implementation success claim or current technical verdict was supplied before this first judgment. No previous PASS has been adopted.

## Direct coverage

- `views.png`: all four dogs, side/front/oblique, 12 cells.
- `attachments.png`: all four dogs, rear/top/ear-hidden side/ear-hidden oblique, 16 cells.
- `expressions.png`: all four dogs, basic/half-closed eyes/closed eyes/mid opening/full opening/tongue out/nose lick, 28 cells.
- `mouth-side.png`: all four dogs, basic/mid opening/full opening/tongue out/nose lick with ears hidden, 20 cells.
- Total directly viewed: 76 cells, including every delivered row and dog. These are static observations, not continuous-animation verification. A proposed extra Maltipoo detail board is not included in this snapshot review.

## Findings

### V01 - MAJOR - short rounded fur muzzle not yet conveyed

Files: all four boards; Maltipoo; front, oblique, side and ear-hidden side; muzzle/chin.

Direct observation: the front/oblique cheeks create a broad nearly vertical facial disk, while a separate narrow upper-lip ledge projects below the nose and a large rounded lower-lip/chin piece protrudes below it. In side and ear-hidden views the cream upper ledge reaches nearly the same forward extent as the nose and reads as an isolated thin lip; the lower piece reads as a bulb or small bowl. The strongest mouth cue is two projecting lips rather than a short rounded coated muzzle.

Reference/requirement: photo 1 shows short rounded muzzle fur spreading to both sides of the nose, blending into the cheeks and rounded chin. Keeping simplified masses is appropriate, but adding a protruding upper lip and enlarged isolated chin does not establish that shape. This is a large silhouette and volume issue within the user's actual photo-refinement request.

Recheck condition: side/front/oblique basic and opening states should show a coherent short, round muzzle mass around and below the nose; the chin should support the mouth without an isolated bowl silhouette; the neck should still descend from behind the jaw with a smooth submental transition. Do not merely conceal the issue with fur texture.

### V02 - MAJOR - nose-lick tongue visually split

File: `expressions.png`; Maltipoo; nose-lick oblique; tongue/upper muzzle.

Direct observation: a pink segment is visible against the nose and another pink segment is visible on the lower mouth, while the broad cream upper-lip ledge masks the entire connecting middle segment. The normal delivered oblique state therefore reads as two disconnected pink pieces. The side diagnostic does show a connecting path, so this is a direct presentation/occlusion issue rather than a proven topological break.

Reference/requirement: the approved nose-lick state must retain a legible supported tongue leading from the mouth to the nose. The review policy explicitly requires connection, support and nose contact; a connection only readable in a diagnostic view is insufficient when the delivered expression appears broken.

Recheck condition: render oblique and front nose lick after correction. A continuous pink tongue surface or an unambiguous continuous bend around the muzzle must be legible while preserving support at the mouth floor and nose contact.

## Other observations and limits

The enlarged ear masses have visible volume and rounded ends in rear/top/side views. The short neck joins the head without an obvious detached plate in the displayed views. Eye states remain readable. In the other three dogs no new visible regression was identified by direct review; byte-level isolation remains a technical-review question. Exact anatomy, unseen photographic ear roots, and owner likeness approval are not inferred from these images.

No technical verdict is issued here. A new final board set requires direct re-review and new hashes.

<!-- review-verdict: {"status": "FAIL", "reviewer": "/root/maltipoo_photo_visual", "artifacts": {"review-snapshot-01/views.png": "e7752f79d116e2e738e75e89417509d2ce6528d813592a32b8189bf94b1b2dc8", "review-snapshot-01/attachments.png": "8236122d65b57b35202a906a3962f5e435a64f5804a5f987c03d536a3deb800c", "review-snapshot-01/expressions.png": "c39226e7a462b8755e35e75ba36dafff2cd5da15750c3805f5f0ac1f302c1607", "review-snapshot-01/mouth-side.png": "770123251a6eb2d78f561a4b378acd981f7bd3a4bd10fc90dcf854f4b7140196"}, "coverage_complete": true, "unresolved": {"V01": "MAJOR", "V02": "MAJOR"}} -->
