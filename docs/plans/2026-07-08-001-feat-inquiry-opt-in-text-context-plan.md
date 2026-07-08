---
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
product_contract_source: ce-plan-bootstrap
execution: code
title: "Inquiry Opt-In Text Context - Plan"
type: feat
date: 2026-07-08
origin: docs/plans/2026-07-07-004-feat-inquiry-evidence-context-plan.md
---

# Inquiry Opt-In Text Context - Plan

## Goal Capsule

Add the first raw-text lane without turning Inquiry Black Box into ambient page surveillance. The product should keep derived telemetry as the default, then let the user explicitly opt in to storing selected/copied text locally so replay can show the snippet that generated an evidence episode.

## Product Contract

### Summary

The evidence-context PR made replay readable with counts, lengths, and hashed page refs. This tranche adds an off-by-default `selectedText` privacy toggle for selected/copied excerpts, stores those excerpts as `document-opt-in`, and teaches replay episodes to show opt-in snippets while continuing to say when raw text was not stored.

### Requirements

- R1. Raw selected/copied text is never captured under the existing selection metrics toggle.
- R2. A separate off-by-default opt-in allows copy/highlight events to include local raw selected text.
- R3. Browser events with selected text require `document-opt-in` privacy and are rejected by schema validation if emitted as derived telemetry.
- R4. The extension background rejects document-opt-in selected-text events unless the opt-in toggle is enabled.
- R5. Replay evidence episodes show a short opt-in snippet when present and keep privacy limitation copy when absent.
- R6. Local export may include document-opt-in excerpts, while cloud sync remains ineligible for document-opt-in payloads.

### Scope Boundaries

- In scope: selected/copied text from intentional copy/highlight events, extension privacy toggle, schema guardrails, replay snippets, tests, and docs.
- Out of scope: ambient viewport text, full-page DOM snapshots, pasted/typed content, camera gaze-to-DOM mapping, cloud document sync, and one-button desktop-extension recording unification.

## Planning Contract

### Key Technical Decisions

- KTD1. **Use a new `selectedText` toggle.** Reusing the existing `selection` toggle would silently widen selection metrics into raw text capture.
- KTD2. **Capture only copy/highlight text for now.** Selection-change events are too noisy and can imply "eyes over" without evidence.
- KTD3. **Store excerpts as `document-opt-in`.** Schema and bridge gates should prevent raw selected text from riding along as `local-derived`.
- KTD4. **Keep snippets bounded.** The extension should cap stored selected text and mark truncation so replay stays useful without large hidden payloads.

## Implementation Units

### U1. Extension Opt-In Toggle and Text Capture

- **Goal:** Add an off-by-default `selectedText` toggle and emit bounded selected text only for copy/highlight events when that toggle is enabled.
- **Requirements:** R1, R2, R4
- **Dependencies:** None.
- **Files:** `apps/inquiry-black-box/apps/extension/src/lib/localBridge.ts`, `apps/inquiry-black-box/apps/extension/src/content/index.ts`, `apps/inquiry-black-box/apps/extension/src/background/service-worker.ts`, `apps/inquiry-black-box/apps/extension/src/popup/PrivacyToggles.tsx`, `apps/inquiry-black-box/apps/extension/tests/content-events.test.ts`, `apps/inquiry-black-box/apps/extension/tests/pairing.test.ts`
- **Approach:** Extend `PrivacyToggles` with `selectedText`, default it to false, normalize stored bridge state, render a popup checkbox named "Selected text excerpts", and make content capture attach `selected_text` only for copy/highlight when opted in. Background gating should continue to require selection metrics and additionally require `selectedText` for document-opt-in selected-text events.
- **Test scenarios:** Default capture still omits selected text; opt-in copy/highlight emits `document-opt-in` with capped `selected_text`; opt-in does not add text to plain selection-change events; background rejects document-opt-in selected text when the toggle is false.
- **Verification:** Extension tests prove the opt-in boundary before app-wide checks run.

### U2. Schema Guardrails for Browser Text

- **Goal:** Reject raw selected/copied browser text unless the event is explicitly `document-opt-in`.
- **Requirements:** R3, R6
- **Dependencies:** U1.
- **Files:** `apps/inquiry-black-box/packages/schema/src/events.ts`, `apps/inquiry-black-box/packages/schema/tests/events.test.ts`
- **Approach:** Add a browser-text opt-in assertion for `browser.selection`, `browser.copy`, and `browser.highlight` payload fields such as `selected_text`. Keep stimulus text guards unchanged.
- **Test scenarios:** `browser.copy` with `selected_text` and `local-derived` throws; `browser.copy` with `selected_text` and `document-opt-in` validates; document-opt-in remains exportable and sync-ineligible.
- **Verification:** Schema tests fail if raw browser text can enter as derived telemetry.

### U3. Replay Snippets for Opt-In Evidence

- **Goal:** Show opt-in selected text in evidence episodes while retaining derived-only privacy language by default.
- **Requirements:** R5
- **Dependencies:** U1, U2.
- **Files:** `apps/inquiry-black-box/packages/signals/src/episodes.ts`, `apps/inquiry-black-box/packages/signals/tests/heuristics.test.ts`, `apps/inquiry-black-box/apps/desktop/tests/replay.test.ts`
- **Approach:** Episode grouping should collect bounded snippets from document-opt-in selected-text events, expose them on `EvidenceEpisode`, and switch the privacy note from "not stored" to "opt-in excerpt stored locally" when snippets exist. Renderer already prints episode details, so snippets can appear as details without a new UI surface.
- **Test scenarios:** Derived-only bursts keep the no-raw-text privacy note; opt-in copy/highlight bursts include a snippet detail; report JSON includes opted-in snippet only when the source event was document-opt-in.
- **Verification:** Replay tests prove the same episode path can explain both privacy modes.

### U4. Docs and Demo Guidance

- **Goal:** Document when raw text is stored and how to test the new opt-in lane.
- **Requirements:** R1, R2, R6
- **Dependencies:** U1-U3.
- **Files:** `apps/inquiry-black-box/docs/prototype-demo.md`, `apps/inquiry-black-box/docs/privacy-model.md`
- **Approach:** Update the demo and privacy docs to distinguish selection metrics from selected text excerpts. Make clear that document-opt-in excerpts remain local/exportable and are not cloud-sync eligible by default.
- **Test scenarios:** Documentation-only; validated through app build/tests and reviewer read-through.
- **Verification:** Docs match the implemented toggle names and privacy classes.

## Verification Contract

Run from `apps/inquiry-black-box`:

| Gate | Done Signal |
|---|---|
| Install check | `bun run install:check` passes. |
| Lint | `bun run lint` passes. |
| Typecheck | `bun run typecheck` passes. |
| Unit tests | `bun run test` passes. |
| E2E | `bun run test:e2e` passes. |
| Prototype build | `bun run build:prototype` passes. |
| Repo hygiene | `git diff --check` passes. |

## Definition of Done

- The extension has a visible off-by-default selected text opt-in.
- Raw selected text is emitted only for copy/highlight events when the opt-in is enabled.
- Raw selected text events use `document-opt-in` and are rejected if emitted as derived telemetry.
- Replay episodes show snippets only for opted-in events and keep no-raw-text copy for derived-only events.
- Docs explain the privacy model clearly enough to run a manual demo without guessing.
- All verification gates pass before commit and PR.
