---
name: maintain-timepark-planner
description: Maintain the Time Park Garden Ops planner for Plants vs Zombies Garden Warfare 2. Use to change map markers, screenshots, wave catalog, point assignments, JSON import/export, GitHub Pages build, local BIN generation, or investigate Frosty spawn-plan mismatches. Preserve placement identity and distinguish browser layout fixes from game-runtime fixes.
---

## Start

1. Read `AGENTS.md`, `README.md`, and `docs/ARCHITECTURE.md` from the repository root.
2. Read `docs/BIN-BUILDER.md` for the browser generator; read `docs/GAME-MODDING-NOTES.md` for BIN/XML/Frosty work. Read `reference/layout-changes.json` when the request depends on previously corrected positions.
3. Establish whether the request changes visual marker positions, point identities, wave assignments, or game assets. Do not silently substitute one for another.
4. For an ambiguous mirror request, ask which zone and axis, or obtain two paired landmarks and an annotated screenshot. A correct A34 alongside misplaced A02/A49/A23 is NOT a whole-image mirror.

## Locate the source of truth

- Edit UI/CSS in `src/template.html`, interactions in `src/app.js`.
- Edit photo marker `x/y` in `data/photo-layout.json`; range 0–1, X right, Y down.
- Treat `data/placements.json` as the original point→GUID/world lookup. World order is X/Y/Z, Y height.
- Treat A01–A55 and E01–E05 as project labels, not engine IDs. Only 40 A-points appear on the site; the Volcano's 15 A-points and 5 E-points are not selectable.
- Edit wave display metadata in `data/catalog.json`; preserve GUIDs, composition/subgroup linkage and numerical gameplay data unless explicitly asked to change them.
- Do not edit the generated `index.html` as the only change.

## Change map markers safely

1. Preserve the photo bytes unless the user asks to replace/rotate/mirror the background.
2. Preserve `id`, `guid` and `world` when moving a marker. Exchange `x/y` positions for confirmed swaps; never exchange point identities to make the picture look right.
3. Transfer an annotation into original-photo coordinates. Account for screenshot cropping/scaling; do not divide an arbitrary cropped screenshot's pixel X/Y by the original image dimensions.
4. For small user-marked moves, use the indicated marker center, not the arrow shaft. For transformations, register fixed landmarks or use an image homography and check residuals visually.
5. Keep unrelated zones unchanged. Initial corrections: Rome A02↔A49, A23 at the marked lower-left floor tile, A34 unchanged. Center uses seven left/right paired swaps; A22 unchanged. Exact baseline and pairs are in the reference report and tests.
6. Update the `placementMap` version in `src/app.js` and relevant README/test expectations after an explicitly requested correction. Preserve the historical baseline.
7. Warn that importing old plans preserves selected A-labels; the user must reconsider assignments made on the old map. Do not auto-migrate assignments without a defined, approved mapping.

## Build and test

Run from repository root:

```bash
python scripts/build.py
python scripts/build.py --check
python -m unittest discover -s tests -v
node tests/bin_builder.cjs
```

Use Python 3.10+, no build dependencies; Node.js 20+ without packages is needed only for JS tests. Open `index.html` directly or serve the root with `python -m http.server 8000`.

For UI changes, inspect at desktop width around 1440 and mobile width around 390. Check all changed zones, no overlapping labels or clipping, selection, import, export, localStorage behavior, and console errors. Validate that exported photos contain the new visual positions but unchanged GUID/world. Keep downloaded test files and screenshots outside tracked source (`artifacts/` is ignored).

Do not equate a self-generated fixture with an independent Frosty round-trip. State which browser tests and actual exports were inspected.

## Handle Frosty work only when requested

1. Obtain local exports from the user's own game/project. Consult `reference/game-originals-manifest.json` for prior baseline filenames, resource paths and hashes; raw exports are intentionally absent.
2. Use `scripts/check_originals.py` to identify baseline files; a version mismatch is not automatically corruption. Use the optional legacy EBX reader as a diagnostic, not a universal parser/writer.
3. Distinguish original resources, imported project state, exported FBMOD and enabled Mod Manager version. Earlier repeated XML exports were identical because files were selected from a Test06 folder, not Test07. Inspect the actual Frosty import log path instead of blaming the user or guessing.
4. Verify all subgroup GUIDs and requested IDs against the map registry, selected group/composition, and event graph. Handle regenerated non-exported XML GUIDs by semantic object identity, not raw temporary GUID equality.
5. Do not delete root wave groups to force choices. Do not bypass challenge initialization with immediate completion; Test06 showed early wave start / frozen timer after that experiment.
6. Do not invent ID range fixes, teleport commands or verified-runtime claims. Test07 retained all 147 groups and had correct imported XML, but runtime spawns were still reported wrong. Photo mapping corrections do not prove the runtime issue solved.
7. Preserve original files locally, change one understood mechanism, provide reproducible checks, and request actual in-game observations only where necessary. After repeated identical failures, stop and change the diagnostic approach.
8. Never bypass anti-cheat, DRM, or ownership checks; use only permitted private/user-controlled test environments. Do not distribute full game exports through this repository.

## GitHub handoff

- Keep root `index.html` current for branch-based Pages; use the included workflows for Actions-based Pages. Deploy only `_site/`, not local game files.
- Keep existing repository domains and configuration. Never replace CNAME or credentials blindly.
- Publish or push only with the user's request and a known repository/access. If unavailable, deliver a repository-ready ZIP and explain that no remote change occurred.
- Include outcome, changed zones/files, tests actually run, remaining uncertainties, and how to load/export a new plan.

## Example tasks

- “Swap Rome A02 and A49, move A23 under old A02, leave A34”: change only three photo positions, rebuild, test identities and background hashes.
- “Center is mirrored: A55 must occupy A01 and A30 must occupy A09”: confirm horizontal paired mapping, preserve A22 and point identities; use the documented seven pairs when approved.
- “Export looks right but wave six spawns near Volcano”: separate photo-label verification from actual spawner behavior; compare observed world coordinates before generating another speculative patch.

## Maintain the BIN generator

Edit `src/bin-builder.js` and `src/bin-panel.html`; never disable exact input size/SHA checks. `data/bin-schema.json` contains offsets, not payloads. Reproduce it with `scripts/generate_bin_schema.py` from local originals. Keep the three-resource/Time Park boundary explicit, block unsupported AMBUSH and preserve service routes outside waves 1–10. Default/random challenges and rewards are unchanged. Do not call the experimental 100xx method runtime-proven. Run JS tests, and, when originals are available, use `scripts/browser_smoke.py` and independent EBX decoding. Do not commit generated test BINs.
