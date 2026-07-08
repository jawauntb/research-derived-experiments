# Privacy Model

Inquiry Black Box treats privacy controls as product behavior. The default app
captures derived signals, not raw surveillance artifacts.

## Default Capture

- Browser: scroll, dwell, visibility, tab, media, selection length, copy/highlight
  metrics, and typing rhythm aggregates.
- Camera: face-present ratio, gaze-away proxy, blink proxy, head-pose variance,
  motion score, confidence, and quality flags.
- Desktop activity: foreground app name, bundle ID, hashed process/window
  identifiers, timing spans, and optional bounded window titles only after the
  separate window-title toggle is enabled.
- Typing: burst length, pause length, backspace count, edit churn, and field role.
- User input: explicit labels, probes, recall answers, notification outcomes.
- Local interpretation: report summaries, evidence ids, suggestion candidates,
  daily review sections, and suggestion feedback.

## Not Stored By Default

- Raw camera frames or image blobs.
- Raw screenshots, screen recordings, OCR text, screen text, or image frames.
- Raw key names, raw typed text, passwords, or document text.
- Full page text or selected/copied text unless a document-level opt-in explicitly
  allows it.
- Hidden/background recording after the user stops or pauses a session.

## Desktop Activity

Desktop activity is off by default. When enabled, the first lane records only
foreground app/window metadata during an active recording session. App identity
remains `local-derived`; optional window titles use `document-opt-in` retention
because titles can reveal filenames, meeting names, or private chats.

Screen snapshots are not part of the default product path. A later
ScreenCaptureKit feature must use a separate explicit opt-in, macOS Screen
Recording permission/picker UX, local-only retention by default, and tests that
reject screenshot, image, OCR, document text, and screen text payload fields.

## Explicit Text Opt-In

Selection metrics and selected text are separate controls. The default
`Selection metrics` toggle stores only derived values such as character count,
range count, timing, and hashed page references. The off-by-default
`Selected text excerpts` toggle allows copy/highlight events to store a bounded
`selected_text` excerpt as `document-opt-in`.

Document-opt-in selected text stays local by default and is eligible for local
export so the user can inspect what was stored. It is not eligible for cloud
sync; only `public` and `redacted-sync` payloads can leave the device through
the normal sync path.

## Privacy Classes

- `public`: safe metadata and documentation-like payloads.
- `local-derived`: derived local features that stay on device by default.
- `redacted-sync`: payloads eligible for optional cloud sync.
- `document-opt-in`: user-selected document snapshots or selected text excerpts
  for explicit local analysis.
- `debug-sensitive`: local debug artifacts omitted from default export.
- `blocked-sensitive`: payloads that should be rejected by normal flows.

Only `public` and `redacted-sync` are cloud-sync eligible. Default export omits
`debug-sensitive` and `blocked-sensitive` events.

## Deletion

Local deletion removes the session and dependent local events. If cloud sync was
used, a redacted cloud-deletion request is placed in `sync_queue` without a
foreign-key dependency on the deleted session, so the delete request survives.

## Interpretation And Daily Review

Session interpretations and daily reviews are local-derived artifacts. They
summarize marker kinds, evidence ids, timing/count patterns, labels, repair
outcomes, and explicit user feedback. They do not require raw typed text, raw
selected text, screenshots, OCR, or raw page text.

Care candidates are confirmation prompts, not settled preferences. Suggestion
feedback is explicit: accepted/useful patterns can be boosted, while dismissed
or not-useful patterns move toward the `ignore` section instead of being treated
as hidden personalization.

## Optional Redacted LLM Summaries

The optional Modal session-summary job accepts only a redacted session
interpretation payload. It includes counts, theme titles, suggestion titles,
limitations, and provenance, and it explicitly excludes raw typed text, selected
text, page text, screenshots, OCR, desktop event objects, app names, and window
titles. App/window identifiers remain local-only even when desktop activity is
enabled.

## Notifications

Notifications are off by default. When enabled, they are generated only from
inspectable daily review suggestions, respect quiet hours and cooldowns, and
record local candidate/delivery events plus whether the user accepted, snoozed,
dismissed, or rated the prompt.
