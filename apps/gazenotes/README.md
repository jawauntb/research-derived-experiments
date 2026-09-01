# gazenotes

Hands-free note capture for macOS. You read on screen and talk; the mic
captures *what you said*, the webcam estimates *where you were looking*, and a
screenshot of that region captures *what you were looking at*. Each spoken note
becomes an entry in a daily markdown file with the transcript, a cropped
screenshot, the app context, and a link back to the source.

Nothing leaves the machine.

```markdown
## 14:30:22 — Google Chrome · arxiv.org

> "This is the same move Arendt makes about natality — worth pairing with the intention sheet."

**Looking at:** "…the model's outputs are constrained not by what it knows but by what it has been asked to be…"
**Source:** [Constraints of the Political](https://arxiv.org/abs/xxxx#:~:text=the%20model's%20outputs)
**Capture:** ![](captures/2026-09-01/143022.png)
Gaze confidence: 0.82 · [full screen](captures/2026-09-01/143022.full.png) · [meta](captures/2026-09-01/143022.json)
```

## The idea

Gaze is not a mouse. Webcam gaze is far too coarse to click a button, but it is
easily good enough to tell you **which paragraph someone was reading**. So:

- **eyes** handle attention (what is this note *about*),
- **voice** handles precision (commands, clicks),
- **screenshots** handle evidence (what was actually on screen).

When the frontmost app is Chrome, Playwright attached to your *real* browser
over CDP does better than pixels: `document.elementFromPoint` on the gaze
coordinate returns the actual text block, so the note quotes the real prose and
links back with a `#:~:text=` fragment that reopens the page at that passage.

## Design rules

These are load-bearing; the code enforces them.

- **Intentional capture.** Nothing is recorded until you speak. No ambient
  screen recording, no always-on audio, no gaze history on disk.
- **Local only.** The default configuration makes no network calls at all —
  including the nightly summary pass, whose default backend is heuristics.
- **Plain files.** Markdown, PNG and JSON in a folder. Obsidian-compatible, no
  database.
- **Coarse gaze, precise voice.** No action depends on gaze finer than about a
  sixth of the screen height.
- **Degrade, never block.** Webcam covered, uncalibrated, Chrome closed, CDP
  dropped — the note still gets written, just with less context. Every
  enrichment step is wrapped; a failure downgrades an entry, it never loses one.

## Install

```bash
cd apps/gazenotes
python3 -m venv .venv && source .venv/bin/activate
pip install -e '.[all]'      # or pick capabilities: .[macos,gaze,browser,watch]
playwright install chromium  # only needed for the browser extras
gazenotes doctor
```

`doctor` reports every permission and dependency, and *attempts* each access so
macOS shows you the TCC prompt for the process that actually needs it:

```
✓ Notes folder         /Users/you/GazeNotes
! Superwhisper folder  no meta.json yet
                       → Dictate once, and enable retention in Superwhisper settings
✓ Screen recording     418 KB test capture
✓ Camera               frame 640x480
! Gaze calibration     not calibrated
                       → Run `gazenotes calibrate`
```

The core package has **no** required dependencies. Each extra adds one
capability, and the daemon reports what is missing rather than refusing to run.

## Use

```bash
gazenotes config --init   # write ~/GazeNotes/config.toml
gazenotes doctor          # check permissions; grant what it asks for
gazenotes displays        # what screens exist, and which are calibrated
gazenotes calibrate       # 9 dots, ~15 seconds, once per display
gazenotes calibrate --display display2-2560x1440   # ...and again per monitor
gazenotes chrome          # relaunch Chrome with the CDP port open (optional)
gazenotes run             # the daemon; menu-bar item if rumps is installed
```

Then just talk. Dictate with Superwhisper as usual; every transcript that is
not a command becomes an entry in `~/GazeNotes/YYYY-MM-DD.md`.

### Voice commands

Anything starting with `computer` (configurable) is a command, not a note:

| Say | Does |
|---|---|
| `computer scroll down` / `up` | scroll the page (CDP, or a synthesised event) |
| `computer page down` / `up` | scroll a full screen |
| `computer show numbers` | badge every link and button on the page |
| `computer click seven` | click badge 7 (spelled-out numbers work) |
| `computer click sign in` | click by visible text |
| `computer recalibrate` | rerun gaze calibration |
| `computer pause` / `resume` | stop and restart the camera |
| `computer dwell on` / `off` | toggle gaze-driven scrolling |
| `computer new section <title>` | start a new heading in today's file |

### Nightly summary

```bash
gazenotes nightly today
```

Prepends a `## Summary` block with bullets, a `### To-dos` list built from
intention phrasing ("I should…", "need to check…"), and `### Related` links to
earlier days sharing a URL or keywords. Rerunning replaces the block; it never
duplicates it and never touches an entry. Schedule it with
`launchd/com.gazenotes.nightly.plist`.

`~/GazeNotes/config.toml` can point the pass at a local model or an API
instead — but the default is `backend = "none"`, which is pure heuristics and
no network.

## How it works

```
Superwhisper ──transcript files──▶ watcher ──▶ command? ──▶ commands
                                      │
FaceTime cam ──30 fps──▶ gaze engine ─┤ (ring buffer, in memory only)
                                      ▼
                                  pipeline
                                      │  1. full screenshot FIRST
                                      │  2. dominant fixation over [t_start-2s, t_end]
                                      │  3. Chrome? → elementFromPoint via CDP
                                      │  4. crop: element shot > gaze band > full frame
                                      ▼
                          ~/GazeNotes/2026-09-01.md
                                    + captures/2026-09-01/143022{.png,.full.png,.json}
```

The screenshot is taken *first*, before any DOM query, because the screen can
change within 100 ms of you finishing a sentence.

### Layout

```
gazenotes/
  config.py       config.toml → typed Config
  geometry.py     quartz / cocoa / pixel conversions (one internal convention)
  events.py       NoteEvent, GazeSample, Fixation, AppContext, BrowserContext, Capture
  watcher.py      Superwhisper folder → NoteEvent
  screen.py       Quartz: frontmost app, window bounds, screenshot, crop
  gaze/
    features.py   face-mesh landmarks → 10-d feature vector
    regress.py    dependency-free ridge regression over degree-2 features
    calibrate.py  dot scheduling, fit, acceptance gate, Tk UI
    model.py      one-euro filter, ring buffer, fixation detection
    capture.py    camera thread; frame → screen-space sample
  browser.py      Playwright/CDP: elementFromPoint, text fragments, element shots
  ocr.py          Apple Vision: "Looking at" for PDFs and native apps
  displays.py     display enumeration, gaze→display resolution, per-screen calibration
  dwell.py        gaze-driven scrolling (off by default)
  screenbuffer.py rolling in-memory pre-note screen buffer (off by default)
  commands.py     transcript → Command; execution against Chrome or the system
  pipeline.py     one note in, one entry out
  notes.py        daily file, entry formatting, sidecars, purge
  nightly.py      heuristic summary, to-dos, cross-day links
  lock.py         advisory lock shared by the daemon and the nightly pass
  daemon.py       wiring
  cli.py          run · doctor · displays · calibrate · nightly · chrome · purge · config
packaging/        py2app build script — a stable bundle id so TCC grants stick
```

The package splits into a **pure core** and thin **platform adapters**. Quartz,
MediaPipe, OpenCV, Playwright and rumps are all imported lazily, so every
module imports — and the whole test suite runs — on any platform.

## Tests

```bash
python -m pytest tests -q     # 382 tests, no macOS or hardware needed
```

Coordinate conversions, fixation detection, the calibration fit and gate, entry
formatting, Superwhisper schema variants, command parsing, text fragments, the
nightly pass's idempotency, and the whole capture pipeline (including every
degradation path) are covered with fakes.

## Beyond the core capture loop

Four extras sit on top of the Phase 1–5 pipeline. Two are **off by default** on
purpose:

| Feature | Default | What it does |
|---|---|---|
| **Vision OCR** (`ocr.py`) | **on** | When the frontmost app is not Chrome, OCRs the gaze crop so PDFs and native apps get a "Looking at" line too. Rendered as `**Looking at (OCR):**`, because OCR of a screenshot is weaker evidence than the live DOM and the note should say so. Local; it only reads a capture that was being saved anyway. |
| **Multi-display** (`displays.py`) | on | Enumerates screens, resolves which one the gaze landed on, and keeps one calibration per display. Handles monitors placed left of or above the built-in screen, where macOS gives them **negative** origin coordinates. A display rearranged in System Settings gets its calibration offset rather than invalidated. |
| **Dwell scrolling** (`dwell.py`) | **off** | Gaze resting in the top/bottom 15% for 400 ms scrolls a chunk. After firing it *latches*: the same zone cannot fire again until you actually look away, so parking your eyes at the end of a paragraph while thinking does not run away with the page. `computer dwell on` to try it. |
| **Pre-note screen buffer** (`screenbuffer.py`) | **off** | A rolling in-memory buffer so "note that" can capture what already scrolled off, saved beside the entry as `HHMMSS.before.png`. Frames never touch disk unless a note fires, and the buffer is capped by both age and total bytes. |

The buffer is off by default for a reason: it is the only component that records
*before* you speak, and intentional capture is the design, not a limitation.
Set `screen_buffer_seconds` if you want it.

## Status and limits

Phases 0–6 of the design are implemented. What is **not** done, and what will
bite you:

- **Gaze accuracy is the risk.** Expect the "which third of the screen" level
  of precision after a good calibration, degrading with lighting changes,
  glasses glare, leaning back, or moving the laptop. Recalibrate when the crops
  start looking wrong. Calibration refuses to save a fit worse than 120 pt of
  median error, because a confidently wrong crop is worse than no crop.
- **Verify the Superwhisper path.** `superwhisper_dir` defaults to
  `~/Documents/superwhisper/recordings`; it has moved across versions. Check
  yours and make sure transcript retention is on. The parser accepts the meta
  schema variants seen in the wild, not one fixed shape.
- **Chrome CDP needs a cold start.** Chrome only opens the debugging port when
  launched with the flag from a fully quit state.
- **One display.** Calibration is keyed by display geometry, so an external
  monitor gets its own model, but the daemon currently tracks the main display
  only.
- **The `.app` build is written but has never been run.** `packaging/` exists so
  TCC grants attach to a stable bundle id instead of to your terminal, but it was
  authored on Linux. Freezing mediapipe and opencv with py2app usually takes a
  few iterations; `packaging/README.md` states exactly what is unverified.
- **Vision OCR has never met real Vision.** Passage assembly, reading order and
  confidence filtering are covered by tests; the pyobjc call sequence needs a Mac.
- **Not yet built:** a computer-use agent fallback for commands in non-browser
  apps.

## Privacy

Captures can contain anything that was on your screen — inboxes, passwords,
private documents. `~/GazeNotes` should be excluded from cloud sync. Use
`gazenotes purge <date>` to delete a day's note and every capture behind it;
it asks you to type the date first.
