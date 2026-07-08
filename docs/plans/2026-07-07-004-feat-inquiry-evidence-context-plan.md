---
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
execution: code
title: "feat: Inquiry evidence context"
created: 2026-07-07
origin: docs/plans/2026-07-07-003-feat-inquiry-live-prototype-plan.md
---

# feat: Inquiry Evidence Context

## Goal Capsule

The live prototype now captures real browser telemetry into SQLite and renders replay, heatmap, and repair prompts. The dogfood session showed the next product gap: replay repeats raw `copied-passage` markers and cannot describe what was copied or seen beyond hashed page metadata. This plan adds a narrow evidence-context layer that turns noisy browser events into privacy-aware episodes, clearer heatmap evidence, and repair prompts that say what is known, what is not stored, and what action the user can take next.

## Problem Frame

The current system is technically working but not yet meaningfully explanatory. A 36-second live session produced 85 scrolls, 30 selections, 12 highlights, and 3 copies, but the UI repeated "Copied or highlighted passage" because each event became an isolated marker. The payload stores selection length, range count, URL hash, hostname hash, and visibility, so default replay should not pretend it knows raw copied text. It should instead summarize the episode: number of selection/highlight/copy events, duration, selection-size range, page reference, and the privacy limitation. When local stimulus is explicitly attached, replay can add segment IDs and opt-in snippets.

## Scope Boundaries

In scope:

- Coalesce repeated copy/highlight/selection events into episode-level evidence.
- Add privacy-aware descriptions for copied/selected evidence using counts, selection-length ranges, source hashes, and stimulus segment refs.
- Render the episode narrative in desktop replay before raw marker details.
- Make copied-passage repair prompts refer to the evidence episode rather than implying raw passage content exists.
- Add focused tests covering noisy copy/highlight sessions and document-opt-in boundaries.

Out of scope:

- Raw arbitrary-page text capture by default.
- Camera feature UX changes.
- Cloud/Railway/Modal activation.
- Broad `coherence-testbench` or neurophenom research changes.

## Key Technical Decisions

- **Add an episode layer inside `packages/signals`.** Keep raw events and heuristic markers intact for provenance, but create `EvidenceEpisode` summaries for UI and repair copy. This avoids changing persisted schema for the first useful pass.
- **Use privacy-safe provenance by default.** Descriptions may include hashed host/page refs, event counts, selection-length ranges, duration, and evidence IDs. Raw text only appears through existing `document_opt_in` stimulus segmentation.
- **Coalesce noisy copy evidence at the marker source.** `markCopiedPassages` should group nearby `browser.selection`, `browser.highlight`, and `browser.copy` events so behavior-only heatmap does not create a separate band per highlight.
- **Keep stimulus binding deterministic and local.** For this tranche, use existing `StimulusInput` and `StimulusSegment` support rather than adding hidden page scraping.

## Implementation Units

### U1. Evidence Episodes and Copied-Passage Coalescing

- **Goal:** Summarize repeated browser selection/highlight/copy telemetry into stable evidence episodes and reduce marker spam.
- **Requirements:** U4/U5 from the live prototype plan; dogfood finding that replay repeated generic copied markers.
- **Dependencies:** None.
- **Files:** `apps/inquiry-black-box/packages/signals/src/episodes.ts`, `apps/inquiry-black-box/packages/signals/src/heuristics.ts`, `apps/inquiry-black-box/packages/signals/src/index.ts`, `apps/inquiry-black-box/packages/signals/tests/heuristics.test.ts`
- **Approach:** Add `buildEvidenceEpisodes(events, markers)` and `EvidenceEpisode` types. Group nearby copy/highlight/selection events by session and page hash within a short window. Include event counts, selection-length min/max, source refs, time span, evidence IDs, concise summary, details, and privacy note. Update copied-passage marker generation to emit one marker per group instead of one marker per raw event.
- **Test scenarios:** A burst of selections/highlights/copies produces one copied-passage marker; the marker evidence names counts and selection-size range; raw text does not appear; separated bursts produce separate markers.
- **Verification:** Fixture and live-like event sequences no longer render one marker per highlight.

### U2. Replay Report Carries Evidence Narrative

- **Goal:** Make desktop replay reports expose episode summaries for the renderer and repair logic.
- **Requirements:** U3/U4/U5 from the live prototype plan.
- **Dependencies:** U1.
- **Files:** `apps/inquiry-black-box/packages/signals/src/heuristics.ts`, `apps/inquiry-black-box/apps/desktop/src/main/reports/sessionReplay.ts`, `apps/inquiry-black-box/apps/desktop/tests/replay.test.ts`
- **Approach:** Extend `ReplayMemo` with `episodes`. Build episodes from the same event set used for markers. Keep `markers`, `heatmap`, and `next_actions` backward compatible. Include report limitations that state raw copied text is unavailable unless a stimulus/document opt-in is attached.
- **Test scenarios:** A replay report for copied evidence includes an episode with summary/details/privacy note; report JSON omits raw document text unless opt-in; existing next actions still emit.
- **Verification:** Desktop IPC can return the richer report without schema migration.

### U3. Renderer Evidence Narrative

- **Goal:** Render readable evidence episodes before low-level marker rows.
- **Requirements:** U5 from the live prototype plan.
- **Dependencies:** U2.
- **Files:** `apps/inquiry-black-box/apps/desktop/src/renderer/replay/ReplayTimeline.tsx`, `apps/inquiry-black-box/apps/desktop/tests/replay.test.ts`
- **Approach:** Add an "Evidence" section to replay. Show each episode's summary, span, details, and privacy note. Keep heatmap and marker rendering for provenance, but avoid making raw marker rows the first thing the user sees.
- **Test scenarios:** Renderer output includes episode summary, privacy note, and coalesced count text; heatmap still renders confidence/evidence/limitations.
- **Verification:** A noisy copied-passage fixture reads as one coherent episode in the replay text.

### U4. Evidence-Aware Repair Prompts

- **Goal:** Make copied-passage repair prompts acknowledge what the app actually knows.
- **Requirements:** U5 repair loop acceptance from the live prototype plan.
- **Dependencies:** U1, U2.
- **Files:** `apps/inquiry-black-box/packages/signals/src/repairs.ts`, `apps/inquiry-black-box/packages/signals/tests/repairs.test.ts`
- **Approach:** When a copied-passage heatmap segment has count/range evidence, ask what the selected/copied evidence was preserving rather than "why did this copied passage matter" as if the text is known. Preserve the action type so existing outcome storage remains compatible.
- **Test scenarios:** Copied-passage segments generate an evidence-aware prompt; low-confidence/no-evidence segments remain filtered; repair events retain evidence IDs and local-derived privacy.
- **Verification:** The first repair prompt after a copy-heavy replay is answerable even without raw page text.

## Verification Contract

Run from `apps/inquiry-black-box`:

- `bun run lint`
- `bun run typecheck`
- `bun run test`
- `bun run test:e2e`
- `bun run build:prototype`

Also run repo hygiene:

- `git diff --check`

## Definition of Done

- A noisy copy/highlight/selection burst is summarized as one evidence episode and one copied-passage marker.
- Replay UI describes what was observed using privacy-safe details and explicitly says when raw copied text was not stored.
- Behavior-only heatmap no longer creates a separate band for every highlight in a burst.
- Copied-passage repair prompts are answerable with or without attached stimulus text.
- Focused tests prove the episode, renderer, and repair behavior.
- Lint, typecheck, tests, E2E, build, and diff checks pass before PR.
