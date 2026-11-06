# Head–neck volume v2: independent visual review, development snapshot 01

Reviewer: `/root/volume_visual_review`. Date: 2026-11-05. **VISUAL=FAIL.** This report reviews the immutable files in `review-snapshot-01/`, copied after the implementer signalled saved development output. It does not apply to later overwritten files in the parent folder. No technical verdict or implementation-success evaluation was supplied before the first clean-image judgement. `views.png` was opened first; the first judgement was recorded before opening the diagnostic and expression boards. No generator edits were made by this reviewer.

## References actually opened

- User-provided sighthound photo `55757.jpg`: long shallow lower jaw, with substantial neck volume behind the rear jaw. Stylized proportions are allowed.
- User-provided `55759.jpg` skeleton schematic: connection relationships only, not measured breed coordinates.
- `outputs/deformation-b-face-v2/golden-reference.png`: actual golden photo region used for muzzle and mouth-corner relationships.
- `private-data/volume-refs/maltipoo.jpg`: particular cream puppy, not a breed standard. Short, rounded muzzle/chin and ears with substantial soft volume.
- `private-data/breed-standing-pair-v1/dachshund-source.png`: actual dachshund photograph.
- `outputs/deformation-b-round-eyes-v1/round-eyes-before-after.png`: approved eye treatment baseline.
- Existing rejection constraints in `outputs/cranio-cervical-v1/visual-review-v2.md`. No previous technical PASS was used as evidence.

## Findings

| ID / severity | File, dog, view, part | Direct observation and requirement | Required correction evidence |
|---|---|---|---|
| VV01 / BLOCKER | All four files; all four dogs; front and oblique most obvious; lower jaw | The lower jaw reads as a wide horizontal tray or rail beneath the face. Front views show lateral corners projecting beyond the mouth as handles. Golden and dachshund additionally have a rounded hanging throat mass below that rail. This is the rejected separate-plate jaw family, not merely an exaggerated cartoon mouth. | Closed, mid-open and open views must show a coherent lower muzzle volume supported at the rear jaw; front/oblique must not have handles or an independent tray contour. Preserve actual mouth opening. |
| VV02 / BLOCKER | `attachments.png` ear-hidden side/oblique; `mouth-side.png` every row; all four dogs, strongest golden/whippet/dachshund | The lower jaw ends in front of a steep notch or near-vertical cut into the neck. Golden has a narrow white vertical slot between jaw end and neck; whippet and dachshund have sharp inward cuts. The dark rising mouth corner is the only apparent rear continuation of the thin jaw. The head and neck are larger volumes, but the rear jaw still reads as separately suspended rather than supported. | Ear-hidden side/oblique must show a rounded, volumetric transition behind the lower jaw, with no visible slot or abrupt cut that makes the jaw look detached. Check the same connection through closed/mid/open states. |
| VV03 / BLOCKER | `views.png` front/oblique; `attachments.png` rear/top; `expressions.png` every row; Maltipoo ears | Ear roots are thin rectangular uprights and folded strips. Front and rear show open gaps enclosed by the ear strip, and top shows flared sheet-like corners. This repeats the rejected tab/paper attachment defect. It is more conspicuous than ordinary simplified hanging ears. | Soft, supported ear-root volume in front/rear/top and oblique, without hollow loops, upright tabs, or sheet corners; maintain the intended root placement. |
| VV04 / MAJOR | `views.png` front/side/oblique; `expressions.png` basic/half-closed/closed-eye; all four, strongest whippet and Maltipoo | Basic closed-mouth views retain large dark triangular wedges rising at the mouth corners. The mouth slit and lower jaw appear disconnected in width; front Maltipoo and whippet look cut apart across the cheek. This is not a normal shallow lip seam. | Closed view should have a coherent lip seam and cheek volume. Opening should arise from that closed seam, rather than retaining a large fixed triangular cut in every state. |
| VV05 / MAJOR | `attachments.png` ear-hidden side; `mouth-side.png`; golden and dachshund particularly | A narrow vertical shaded groove separates the back of the skull from the neck mass; the front of the golden neck is almost vertical with an abrupt lower step. Rear views establish genuine neck width, so this is not the old uniformly thin plate; nevertheless the side-view neck still reads as a bolted-on slab at the join. | Smooth volume transition must be readable in side and oblique without ear coverage; retain a short neck and anatomical direction without adding an isolated slab or smoothing over the mouth. |

## Coverage and observations

All four saved files were directly opened and every dog in every row was inspected. This is complete coverage of the supplied static boards, not a continuous animation test.

| File | Golden | Whippet | Dachshund | Maltipoo |
|---|---|---|---|---|
| `views.png`: side, front, oblique | All 3 inspected; VV01/VV02/VV04/VV05 | All 3 inspected; VV01/VV02/VV04 | All 3 inspected; VV01/VV02/VV04/VV05 | All 3 inspected; VV01/VV02/VV03/VV04 |
| `attachments.png`: rear, top, ear-hidden side, ear-hidden oblique | All 4 inspected; broad rear neck present, side attachment still fails | All 4 inspected; shallow jaw and broad rear neck present, rear-jaw notch fails | All 4 inspected; long muzzle retained, rear-jaw notch fails | All 4 inspected; rounded top muzzle improved, ear-sheet and jaw defects fail |
| `expressions.png`: basic, half-closed eyes, closed eyes, mid-open, open, tongue-out, nose-lick | All 7 inspected; lower-jaw rail persists | All 7 inspected; lower-jaw rail persists | All 7 inspected; lower-jaw rail persists | All 7 inspected; jaw and ear-root defects persist |
| `mouth-side.png`: basic, mid-open, open, tongue-out, nose-lick | All 5 inspected; thin jaw and rear slot persist | All 5 inspected; thin jaw and abrupt notch persist | All 5 inspected; thin jaw and abrupt notch persist | All 5 inspected; thin jaw and rear corner defect persist |

The whippet no longer has the earlier deep bowl-like closed underside. The Maltipoo muzzle is materially shorter and rounded in front/top; it is not judged as the old long beak in this snapshot. Round eyes remain readable, and common dark nose family with breed scale variation is apparent. Those improvements do not resolve the jaw and attachment failures. The tongue-out surfaces appear to rest along the lower mouth edge and nose-lick strips reach the nose in the supplied side and oblique views; no separate floating-tongue finding is made. This does not establish hidden interior contact or animated continuity. Exact unchanged ear-root coordinates and nose/eye parameters remain technical-review matters.

## Artifact hashes

| Snapshot file | SHA-256 |
|---|---|
| `review-snapshot-01/views.png` | `cd83e85ce2087d500c7a81a3f96a053ebbefca0257d601c629b08da42a9d2b1f` |
| `review-snapshot-01/attachments.png` | `6f70b3f1b2e35e8da794228ed5380b87466f997a4dd2ce1aaa40b38d7e116ceb` |
| `review-snapshot-01/expressions.png` | `a94040a67be96bae27410ec6dcbac3d3cd7a9f93e42e273fd3233ba44a1fe015` |
| `review-snapshot-01/mouth-side.png` | `1daf9d0aaf4be622eea324ee7cc22f07e54a0656c4379f1b9175e13002ccd8c1` |

<!-- review-verdict: {"status":"FAIL","reviewer":"/root/volume_visual_review","artifacts":{"review-snapshot-01/views.png":"cd83e85ce2087d500c7a81a3f96a053ebbefca0257d601c629b08da42a9d2b1f","review-snapshot-01/attachments.png":"6f70b3f1b2e35e8da794228ed5380b87466f997a4dd2ce1aaa40b38d7e116ceb","review-snapshot-01/expressions.png":"a94040a67be96bae27410ec6dcbac3d3cd7a9f93e42e273fd3233ba44a1fe015","review-snapshot-01/mouth-side.png":"1daf9d0aaf4be622eea324ee7cc22f07e54a0656c4379f1b9175e13002ccd8c1"},"coverage_complete":true,"unresolved":{"VV01":"BLOCKER","VV02":"BLOCKER","VV03":"BLOCKER","VV04":"MAJOR","VV05":"MAJOR"}} -->
