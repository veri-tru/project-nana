# Independent visual review — development pass 03

Reviewer: `/root/skull_volume_visual` · 2026-11-06

**VISUAL=FAIL. Delivery remains BLOCKED.** Two unresolved MAJOR findings remain. This is a review of anatomical support relationships for the future character foundation; it is not a demand for matched-breed CT measurements, finished skin, teeth, fur, or photorealistic bone texture.

## Independence and evidence

I read AGENTS.md and docs/visual-review-policy.md, then directly opened private-data/skull-anatomy-v2/lateral.jpg, dorsal.jpg and rostral.jpg before opening any candidate image. These are three views from the same generic IMAIOS atlas module, not four breed-specific datasets. I inspected the four saved candidate PNGs after the implementer's saved signal. The first visual finding and FAIL assessment were sent before inspecting generation code or receiving any technical verdict. I did not generate or modify these images. The generator was not inspected for this visual decision.

README.md and references.json correctly distinguish authored proportions, preserved shortened muzzle controls, structural reference and unperformed model training. Labels and existence of named components do not by themselves establish the visible relationship.

## Direct coverage

| File | Directly inspected cells |
|---|---|
| structure.png | Golden retriever, whippet, dachshund, Maltipoo: side, oblique, front and top; all 16 cells |
| jaw-motion.png | All four dogs: 0°, 10° and 20°; all 12 cells |
| structure-detail.png | Golden: side, oblique with nasal attachment, top, front/open mouth; all 4 cells |
| jaw-detail.png | All four dogs: isolated side, rear oblique and top; all 12 cells |

All 44 provided cells were inspected, along with whole-board readability. Coverage of the supplied files is complete. The hidden assembled joint relationship remains insufficiently exposed, as detailed below. Static frames do not establish collision-free motion between those frames.

## Visible improvements established by the images

- Cranial and maxillary surfaces now have visible finite depth. They are no longer only contour lines or a cage.
- The maxillary block has a roof, side support, basal edge and anterior nasal aperture. The head-to-muzzle transition is present in side and oblique views. The shortened profile family is visually retained; exact coordinate identity belongs to technical review.
- The arch stands laterally from the cranial surface, leaving visible space in the top view. The orbit is not surrounded by an added closed outer upper bony ring.
- Oral space remains open between upper and lower structures in all supplied mouth states. No obvious lower-jaw detachment or gross penetration is visible in those whole views, but the actual joint contact is concealed.
- Isolated jaw views show a continuous left/right mandibular body, ascending rear regions, tall coronoid regions and separate smaller posterior condylar protrusions. Those named parts are distinguishable.
- The Maltipoo remains the shortest muzzle, while the whippet remains the longest/slenderest. No demand is made to reverse the user's accepted muzzle shortening.

## Unresolved findings

### V03-01 — MAJOR: mandibular body and ramus remain rod-and-post support

**Files / cells / region:** jaw-detail.png, all four rows, side and rear oblique; structure.png and jaw-motion.png, all four dogs, rear mandibular body through ascending ramus.

**Direct observation:** The mandibular body is a long, nearly constant thin rail. At its rear it turns abruptly into a narrow vertical column with a rounded tall end; the small posterior condylar knob branches from that column. Some widening exists at the very bottom, but there is very little broad supporting face between posterior body, coronoid and condyle. In the isolated rear oblique views the two tall pieces read as narrow freestanding posts. Whippet length makes this rail/post construction especially conspicuous; Golden, dachshund and Maltipoo repeat the same issue at different lengths.

**Reference / requested relationship:** In the actual lateral atlas image, the posterior mandibular body transitions into a broad ascending plate beneath the zygomatic arch. The coronoid is the upper extension of that plate, and the condylar area belongs to its rear, rather than being a knob on a narrow stalk. The rostral image also shows finite paired mandibular side support. The user specifically requested structural volume before later pixel simplification, and the prior missing jaw body/ramus volume was a rejection reason. Merely giving the former rail a rounded cross-section does not finish that relationship.

**Correction and recheck:** Form a broader, finite ramus plate that transitions gradually out of the posterior mandibular body and supports both coronoid and condylar regions. Preserve the anterior slenderness needed by the whippet and accepted muzzle lengths; no blanket thickening of the whole chin is requested. Reopen isolated side/rear-oblique/top and assembled 0°/10°/20° for every dog, checking that widening does not fill oral space or intersect the arch.

### V03-02 — MAJOR: assembled condyle-to-temporal support cannot be visually verified

**Files / cells / region:** structure.png and jaw-motion.png, all four dogs; structure-detail.png side/oblique; posterior joint behind the green arch and brown ramus.

**Direct observation:** The isolated jaw board exposes the small posterior condyles, but hides the upper skull entirely. In the assembled boards the region where those condyles must be seated is occluded by the arch/rear cranium. The currently supplied views do not expose both mating structures together at any mouth state. The opening boards show rotation of a plausible connected silhouette, but cannot establish whether the condyle is actually seated in a credible support surface or passes through it.

**Reference / requirement:** The actual lateral reference locates the joint in the posterior arch/temporal region. The visual-review policy explicitly requires diagnostic views for concealed attachments and forbids assuming that an obscured connection is valid. The requested result includes credible attachment and nonpenetrating opening. This finding is missing visible evidence, not an assertion that penetration has been proven.

**Correction and recheck:** Add a close rear-oblique or local section/cutaway of the assembled joint that shows condyle and temporal support together, at 0°/10°/20° for each dog. Use the same model; show the diagnostic hiding/section explicitly. Pair the direct visual check with the independent technical collision/contact review. If the current geometry already supports the joint correctly, this may require only diagnostic rendering rather than a geometry change.

## Additional nonblocking observation

The cranial/maxillary seam is visibly jagged in the Golden close view and there is coarse faceting along the muzzle. That surface quality does not independently block the structural foundation. It should not be mistaken for anatomical sutures or used as such in future training annotations.

## Exact reviewed hashes

- structure.png — 696c26e379fa90ac90d4a9c737790df4d45c809bfa8c1688a8f578b77bd75097
- jaw-motion.png — e49f24d2b4f95acd313e4d10ac8500feffa7c68fa9f285f445eab73bc224139f
- structure-detail.png — e5a82256a696cbad9f2cc499e010cfbd27e5436cbc85004b30366c88c525fa79
- jaw-detail.png — 02bc5ef8519de93e1e3a585716ba3841cb4f607baaf14adeff7532fd906e0918

These conclusions do not authorize learned-reference, measured-anatomy, or completed-skin claims. Re-review is required for changed final files.

<!-- review-verdict: {"status":"FAIL","reviewer":"/root/skull_volume_visual","artifacts":{"structure.png":"696c26e379fa90ac90d4a9c737790df4d45c809bfa8c1688a8f578b77bd75097","jaw-motion.png":"e49f24d2b4f95acd313e4d10ac8500feffa7c68fa9f285f445eab73bc224139f","structure-detail.png":"e5a82256a696cbad9f2cc499e010cfbd27e5436cbc85004b30366c88c525fa79","jaw-detail.png":"02bc5ef8519de93e1e3a585716ba3841cb4f607baaf14adeff7532fd906e0918"},"coverage_complete":true,"unresolved":{"V03-01":"MAJOR","V03-02":"MAJOR"}} -->
