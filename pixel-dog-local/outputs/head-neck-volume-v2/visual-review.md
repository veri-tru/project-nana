# Final independent visual review — head-neck-volume-v2

Reviewer: `/root/volume_visual_review`. Date: 2026-11-05. **VISUAL=PASS for the four exact files and hashes below. Unresolved BLOCKER/MAJOR: 0.** One minor surface-shading observation remains. This is visual candidate clearance, not owner likeness approval, technical approval, or an animation-quality claim.

The reviewer did not generate or edit the model. The first assessment began with clean saved images before diagnostics, and no technical PASS or implementation-success evaluation was read. Development failures were recorded in separate reports and retained. The implementer supplied saved-file signals and descriptions of changed scope for later re-reviews. Final pass 09 was judged by reopening all four actual final PNGs; no earlier PASS was transferred to changed files.

## Actual reference basis

- User sighthound photo `../.codex-attachments/768d9f11-0441-440b-a272-2d05ac586b78/6802266b-b4f1-4a70-9d32-d6584792f9da/55757.jpg`, relative to the project root: long shallow jaw and supported rear jaw/neck relationship.
- User skeleton schematic `../.codex-attachments/f8618f8f-16c8-4b59-bce1-14a37f5c588e/4deadebd-9d6c-4b85-bc47-cd8bb0f68b32/55759.jpg`: connection relationships only, not measured coordinates.
- `outputs/deformation-b-face-v2/golden-reference.png`: actual golden photo region and broad muzzle reference.
- `private-data/breed-standing-pair-v1/dachshund-source.png`: actual dachshund photo, long muzzle and rear-skull ear placement.
- `private-data/volume-refs/maltipoo.jpg`: particular cream puppy with a short rounded muzzle; not a universal breed standard.
- `outputs/deformation-b-round-eyes-v1/round-eyes-before-after.png`: approved round-eye treatment baseline.
- Previous rejection constraints from `outputs/cranio-cervical-v1/visual-review-v2.md`.

All those images were actually opened during this review task. Exact biological proportions, hidden anatomy and owner-specific likeness are not claimed. The target remains a deformed, simplified character with a head and short neck; photorealistic fur and detail are not required.

## Final observed result by dog

| Dog | Closed shape and attachment | Expression states |
|---|---|---|
| Golden | Broad muzzle retained. Short neck now joins the rear skull continuously in side/oblique and has real width in rear/top. No separate neck slab, white rear-jaw slot, circular rear socket, or hanging U-shaped throat band remains. Front lower jaw has no handle corners. | Half/closed-eye states preserve the same shape. Mid/open mouth retains a connected rear jaw, with an actual opening. Tongue lies along the mouth floor and reaches the nose in lick views. |
| Whippet | Long, shallow lower jaw retained without the rejected bowl underside. Neck has thickness and a continuous rear-jaw transition. Small dark mouth-corner accents remain a coherent stylized lip feature, not the previous large cut-out wedges. | All seven oblique states and five ear-hidden side states keep the shallow jaw and support. No floating tongue or disconnected jaw is visible. |
| Dachshund | Long muzzle and high rear ear attachment retained visually. Ear-hidden views now show continuous jaw-to-neck volume; the old angular neck step, rear disk/rings and isolated lower throat band are absent. | Mouth opens through the supplied intermediate and open states without the rear jaw detaching. Tongue support and nose reach are visible. |
| Cream Maltipoo | Short rounded muzzle and small dark nose remain, without a long beak/funnel. Ear roots are closed soft volumes with no hollow loops, upright tabs or flared paper sheets. Short neck is supported rather than a V-shaped throat membrane. In the final top view the exposed maroon mouth patches and projecting lower rim are gone. Front/oblique lower lip stays within a coherent muzzle footprint. | Basic, eye states, mid/open mouth, tongue-out and lick all directly checked. The narrowed lower mouth does not erase the opening or leave the tongue floating; tongue-out remains supported and lick reaches the nose. |

Round eyes remain readable in all four basic views, with perspective ellipses expected on curved surfaces. The shared dark rounded nose family and different per-dog scale remain visually apparent. Exact coordinate/parameter preservation of eyes, nose and the existing three ear roots is a technical-review responsibility; it is not inferred solely from these renderings.

## Full file × dog × view coverage

Every cell below was directly inspected in the final saved files. No dog was approved by similarity to another or by common generator code.

| Final file | Golden | Whippet | Dachshund | Maltipoo |
|---|---|---|---|---|
| `views.png` | Side, front, oblique | Side, front, oblique | Side, front, oblique | Side, front, oblique |
| `attachments.png` | Rear, top, ear-hidden side, ear-hidden oblique | Rear, top, ear-hidden side, ear-hidden oblique | Rear, top, ear-hidden side, ear-hidden oblique | Rear, top, ear-hidden side, ear-hidden oblique |
| `expressions.png` | Basic, half-closed eyes, closed eyes, mid-open, open, tongue-out, nose-lick | Basic, half-closed eyes, closed eyes, mid-open, open, tongue-out, nose-lick | Basic, half-closed eyes, closed eyes, mid-open, open, tongue-out, nose-lick | Basic, half-closed eyes, closed eyes, mid-open, open, tongue-out, nose-lick |
| `mouth-side.png` | Basic, mid-open, open, tongue-out, nose-lick | Basic, mid-open, open, tongue-out, nose-lick | Basic, mid-open, open, tongue-out, nose-lick | Basic, mid-open, open, tongue-out, nose-lick |

This totals 76 directly viewed static cells. Whole-board silhouette/readability and the individual problem regions were inspected. Review-only enlarged crops from the failed pass 08 are diagnostic evidence, not final candidate artifacts. Static intermediate poses do not constitute continuous-animation testing. Hidden tongue contact, self-intersection and exact geometry are not established by visual inspection alone.

## Finding closure

| Earlier finding | Final image evidence | Final status |
|---|---|---|
| VV01: lower-jaw tray/handle corners | Front and oblique mouths terminate into cheek volume without projecting handle corners; side opening has a supported rear jaw. Thin stylized lips alone are not a failure. | Resolved |
| VV02: rear-jaw slot/notch | Ear-hidden side/oblique and all five mouth states show continuous support, with no white vertical slot or sharp separation. | Resolved |
| VV03: Maltipoo hollow ear tabs | Front/rear/top/oblique show closed rounded hanging ears without exposed loops or sheet corners. | Resolved |
| VV04: fixed large triangular cheek cuts | Closed mouth seams are coherent; whippet's remaining small corner accent does not remove a large cheek region. | Resolved |
| VV05: neck slab/ridge/step | Ear-hidden side and oblique silhouettes join continuously; neck width is confirmed in rear and top. | Resolved |
| VV06: rear neck disk/rings | Existing three rear views are smooth broad volumes, with no central rivet/socket motif. | Resolved |
| VV07: isolated U-shaped throat band | Front/oblique and ear-hidden oblique no longer show a separate hanging band below the jaw. | Resolved |
| VV08: Maltipoo top-view exposed mouth patches | Final `attachments.png` top view has no maroon patches beside the nose or projecting lower rim; front/oblique/open states remain coherent after correction. | Resolved |

**VV09 / MINOR remains:** `views.png` Maltipoo front/oblique and corresponding `expressions.png` views show faint broad shading bands across the nasal bridge. They do not form a long cone, disconnected nose, sharp seam or unsupported volume, and are visible chiefly as tonal transitions. Optional future smoothing should preserve the current short rounded muzzle and small nose and requires fresh image review if changed. No other unresolved findings were identified in the reviewed static scope.

## Exact final artifact hashes

Paths are relative to this report's folder. A change to any image invalidates this report for that changed file.

| File | SHA-256 |
|---|---|
| `views.png` | `ad625378de94d723e30bf6aaefbed49193c6cd672531947a3da2e383e9340369` |
| `attachments.png` | `5fa54baa1cb12d11eb6f2c2404dc1f52f05531d81e3c011762dbaa9cdd33fd5e` |
| `expressions.png` | `b99527e00b59ae5b1b1995696fdb261940e013907195e6dd17740978bb10f584` |
| `mouth-side.png` | `e39c718ce287ae0c9dd93726deaa0e6d5b95bc5a34194cdacc0d439437442605` |

<!-- review-verdict: {"status":"PASS","reviewer":"/root/volume_visual_review","artifacts":{"views.png":"ad625378de94d723e30bf6aaefbed49193c6cd672531947a3da2e383e9340369","attachments.png":"5fa54baa1cb12d11eb6f2c2404dc1f52f05531d81e3c011762dbaa9cdd33fd5e","expressions.png":"b99527e00b59ae5b1b1995696fdb261940e013907195e6dd17740978bb10f584","mouth-side.png":"e39c718ce287ae0c9dd93726deaa0e6d5b95bc5a34194cdacc0d439437442605"},"coverage_complete":true,"unresolved":{"VV09":"MINOR"}} -->
