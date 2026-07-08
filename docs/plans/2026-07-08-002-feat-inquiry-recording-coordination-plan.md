---
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
product_contract_source: ce-plan-bootstrap
execution: code
title: "Inquiry Recording Coordination - Plan"
type: feat
date: 2026-07-08
origin: docs/plans/2026-07-07-004-feat-inquiry-evidence-context-plan.md
---

# Inquiry Recording Coordination - Plan

## Goal Capsule

Make the local demo stop depending on a hidden two-button ritual. When the
extension is paired with the desktop bridge, pressing Record in the extension
should start or resume the desktop session before browser capture begins, and
pressing Stop should stop local browser capture and ask the desktop to stop the
session. The popup should also describe queue health clearly enough that "0
queued" reads as healthy rather than broken.

## Product Contract

### Summary

The prototype currently has two independent recording controls. The desktop
Start button creates the authoritative SQLite session, while the extension
Record button only enables content-script capture. This tranche adds a paired
session-control endpoint on the desktop bridge and has the extension coordinate
Record/Stop with it.

### Requirements

- R1. A paired extension Record action starts a desktop session when no active
  desktop session exists.
- R2. A paired extension Record action resumes a paused desktop session and is
  idempotent when desktop is already recording.
- R3. A paired extension Stop action stops extension capture locally and asks
  desktop to stop the active session when one exists.
- R4. The desktop session-control endpoint uses the same origin and pairing
  token protections as extension event ingest.
- R5. The extension stores the desktop session id returned by the control
  endpoint so subsequent browser events are labeled with the authoritative
  session id.
- R6. The popup queue line distinguishes a clear retry queue from queued events,
  so a healthy recording state is not reported as only "0 queued".

### Scope Boundaries

- In scope: extension-to-desktop Record/Stop coordination, desktop bridge
  session-control route, popup feedback text, focused tests, and demo docs.
- Out of scope: desktop-to-extension control without a native Chrome channel,
  automatic timed desktop resume for extension-only pauses, native messaging,
  cloud sync, camera preview UI, and new browser automation.

## Planning Contract

### Key Technical Decisions

- KTD1. **Coordinate extension to desktop first.** The extension can already
  call the localhost desktop bridge; desktop cannot directly command Chrome
  without a new native messaging surface.
- KTD2. **Keep Pause local for now.** The existing extension Pause 15m is a
  content-capture pause. Mapping it to desktop pause would strand the desktop in
  paused state after the extension auto-resumes.
- KTD3. **Use the same bridge auth.** The control endpoint should require the
  same allowed origin and pairing token as `/v1/extension/events`.
- KTD4. **Return the authoritative session id.** The extension should update its
  stored session id from desktop responses instead of assuming
  `local-browser-session`.

## Implementation Units

### U1. Desktop Session-Control Endpoint

- **Goal:** Add a local `/v1/extension/session` endpoint that handles extension
  Record/Stop coordination behind existing bridge auth.
- **Requirements:** R1, R2, R3, R4
- **Dependencies:** None.
- **Files:** `apps/inquiry-black-box/apps/desktop/src/main/ingest/server.ts`,
  `apps/inquiry-black-box/apps/desktop/tests/ingest.test.ts`
- **Approach:** Route the new path through the same CORS/origin/token checks as
  event ingest. Accept `recording_state: "recording" | "stopped"`. For
  recording, start a default "Research session" when there is no active session,
  resume a paused session, or return the active recording session. For stopped,
  stop the active session when present and otherwise return an idle stopped
  response.
- **Test scenarios:** Missing/bad token is rejected; extension Record starts a
  desktop session; repeated Record is idempotent; Stop ends the active session.
- **Verification:** Desktop ingest tests cover both auth and state transitions.

### U2. Extension Control Client and State Sync

- **Goal:** Have extension Record/Stop coordinate with desktop and store the
  desktop session id before content capture changes state.
- **Requirements:** R1, R2, R3, R5
- **Dependencies:** U1.
- **Files:** `apps/inquiry-black-box/apps/extension/src/lib/localBridge.ts`,
  `apps/inquiry-black-box/apps/extension/src/background/service-worker.ts`,
  `apps/inquiry-black-box/apps/extension/tests/pairing.test.ts`,
  `apps/inquiry-black-box/tests/e2e/extension-pairing.spec.ts`
- **Approach:** Add a `postSessionControl` helper that derives the session
  endpoint from the configured events endpoint. Background Record calls the
  helper, updates local `recordingState`, and replaces `sessionId` with the
  returned desktop session id. Background Stop always stops local capture and
  best-effort calls desktop stop.
- **Test scenarios:** Record sends the pairing token to the session endpoint;
  background Record saves returned desktop session id and broadcasts settings;
  Stop still makes local capture stopped even if desktop is unavailable.
- **Verification:** Extension pairing tests and E2E prove browser telemetry lands
  in the desktop session started through the extension path.

### U3. Popup Feedback and Demo Docs

- **Goal:** Make the popup explain queue health instead of showing a confusing
  bare `0 queued`.
- **Requirements:** R6
- **Dependencies:** U2.
- **Files:** `apps/inquiry-black-box/apps/extension/src/popup/App.tsx`,
  `apps/inquiry-black-box/docs/prototype-demo.md`
- **Approach:** Replace the queue copy with "Queue clear" when no retry backlog
  exists and "N queued for retry" when events are waiting. Update the demo runbook
  to say extension Record starts the desktop session when paired, while the
  desktop Start button remains useful for desktop-only camera/label sessions.
- **Test scenarios:** Existing popup and E2E tests cover the rendered model; docs
  are reviewed against implementation.
- **Verification:** App build and tests stay green.

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

- Extension Record starts/resumes the desktop session when paired.
- Extension Stop stops local capture and asks desktop to stop the active session.
- Extension state uses the desktop session id returned by the control endpoint.
- The desktop control endpoint reuses pairing-token and origin protections.
- Popup queue copy makes a clear retry queue distinguishable from a healthy
  no-backlog state.
- Demo docs explain which button to press for browser-plus-desktop sessions.
- All verification gates pass before commit and PR.
