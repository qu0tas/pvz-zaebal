---
name: maintain-timepark-planner
description: Maintain the Time Park Garden Ops and Graveyard Ops editors: photo markers, wave catalogs, enemy limits, JSON plans, exact-baseline BIN writing, shared ChallengeSelector/RewardSpin settings, GitHub Pages, or Frosty mismatch investigations. Preserve placement identity, per-mode plans and service routes; distinguish static checks from game-runtime proof.
---

## Start

1. Read `AGENTS.md`, `README.md`, and `docs/OPS-EDITOR.md`. Read `docs/GAME-MODDING-NOTES.md` for past failures, not as the current generator spec.
2. Identify the requested mode and whether the change concerns photo positions, world positions, wave composition, min/max limits, shared settings, or runtime behavior. Do not substitute one for another.
3. Use `src/app.js`, `src/ops-panel.html`, `src/bin-builder.js`, `src/template.html`. Generate profiles/catalog with `scripts/generate_ops_profiles.py`; rebuild **both** pages with `scripts/build.py`.

## Preserve invariants

- Keep photo bytes/size and GUID/world coordinates unchanged for marker corrections. Photo x/y range 0..1; x right, y down. World order X/Y/Z; Y height. Do not mirror images to fix labels.
- Keep map correction v3: Rome A02↔A49, A23 moved by user annotation, A34 unchanged; Center seven pairs exchanged and A22 unchanged. Read `reference/layout-changes.json` before changing calibration. Egypt/China have no new runtime proof.
- Treat Axx/Eyy as project labels. Only 40 A-points are selectable; Volcano and Epic placements are excluded. Experimental IDs use 10000+number, not an engine-proven convention.
- Preserve Garden storage key `gw2-timepark-select-v1`; use separate `gw2-timepark-graveyard-v1` for Graveyard. Reject cross-mode GUIDs/plans. Old plans retain labels, not old visual positions.
- Keep all root groups: Garden147, Graveyard105. Preserve service routes, especially Graveyard Wave00 (native WaveNumber1, not a selectable wave1) and extraction.
- Change only existing enemy record min/max (0..500) and explicit group delays (0..300). Do not promise exact total enemy counts; other caps/pool remain original. Reject impossible ranges, unknown GUIDs, incompatible profiles, and unsupported AMBUSH.
- Treat shared subgroup GUIDs as aliases, not independent copies. Reject conflicting spawn assignments. Apply limits only to active composition subgroups.

## Shared resources

Read `docs/OPS-EDITOR.md` for branch mappings. Keep Selector lifecycle/reset/callbacks intact; change only the 20 request Target/TargetEvent pairs when a native condition is forced. `NoKnockouts`/`NoBaseDamage`/`NoPlayerDamage` remain objectives. Do not claim all tasks are disabled or add the old instant-callback shortcut without a new proven lifecycle analysis.

For RewardSpin, change only UniformDistribution and two existing float weight arrays. Validate money/horde mappings and reject horde-only requests impossible in WG01. Monetary outputs do not replace boss composition icons. Do not claim payouts, visual tease or all bonus events are fixed without a game test.

Always export five BIN for the selected mode. Include unchanged originals for shared settings set to vanilla so earlier patches can be reset. Explain that shared grid/selector/reward resources can conflict between mods; this is not a merged two-plan package.

## Validate

Run README's Python, JS profile/sweep, independent semantic and optional browser tests. Check actual desktop/mobile screenshots, empty/filled forms, custom weights, JSON errors, BIN reload/restore, ZIP download and SHA/CRC. Treat `artifacts/` as throwaway local test output. Do not stage it.

Use `verify_generated.py` to compare complete semantic objects, not just requested values. After actual Frosty import, request fresh XML exports and the Imported log only when needed. Record what is proven: input identity → static structure → semantic fields → Frosty roundtrip → runtime; never skip levels by assertion. Stop repeating the same failed hypothesis after repeated identical observations.

## Files and publication

The owner explicitly requested the 42 supplied BIN/XML listed in `originals/manifest.json` and five per-page embedded baselines. Preserve exact hashes; do not add other raw exports automatically. Keep generated BINs/FBMOD/projects/local-game-files out of the public package. Explain public exposure of embedded baseline bytes and check distribution rights before publishing. Do not push/deploy without user authorization and actual access.
