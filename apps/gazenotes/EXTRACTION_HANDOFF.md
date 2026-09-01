# gazenotes — extraction & bring-up handoff

**For:** a Claude Code agent starting from zero in a local `~/gaze` directory.
**Goal:** lift this app out of the research monorepo it was built in, give it its
own private GitHub repo, then get it actually working on this Mac.
**Written:** 2026-09-01, by the agent that built it (on Linux, with no Mac).

Read §0 and §5 before you touch anything. §5 is the part that will cost you a
day if you skip it.

---

## 0. What you are dealing with

**gazenotes** is a local, hands-free note-taking daemon for macOS. The user
reads on screen and talks. Superwhisper (a separate, already-installed app)
captures *what they said*; the webcam estimates *where they were looking*; a
screenshot of that region captures *what they were looking at*. Each spoken
note becomes an entry in a daily markdown file with the transcript, a cropped
screenshot, app/URL context, and a deep link back to the source. When the
focused app is Chrome, a Playwright CDP connection to the live browser adds the
real DOM text under the gaze and a `#:~:text=` link that reopens the page at
that passage. Nothing leaves the machine.

**The critical fact about its current state:** every line of it was written and
tested on Linux, with no camera, no macOS, and no browser. 387 tests pass
headless. That means the *logic* is well covered and the *hardware integration
is entirely unproven*. Your job is the second half. Do not assume something
works because a test passes; the tests were deliberately written to cover only
what could be honestly verified without a Mac.

---

## 1. Provenance — where the code is right now

| | |
|---|---|
| Source repo | `jawauntb/research-derived-experiments` (GitHub) |
| Path in that repo | `apps/gazenotes/` |
| Branch | `claude/create-this-6p3ecj` |
| Pull request | **#546** — "Add gazenotes: hands-free gaze- and voice-driven note capture for macOS" |
| Commits (oldest → newest) | `f83166a` initial app (Phases 0–5) · `a529cb2` Phase 6 config surface · `fef3586` Phase 6 layers + integration · `7f7a13b` buffer expiry + pause fixes |

The user also has a local clone of `research-derived-experiments` on this
machine — **prefer it** if you can find it (`git remote -v` should show
`jawauntb/research-derived-experiments`). It saves a clone and guarantees you
get the same commits.

The app is **already self-contained**: it has its own `pyproject.toml`, its own
`tests/`, and nothing inside `apps/gazenotes/` imports from or path-references
the parent repo. `tests/conftest.py` resolves its path relative to itself.
Extraction is therefore a directory promotion, not a refactor.

Do **not** carry over any parent-repo file. The parent's
`scripts/run_quality_checks.py`, `tests/test_run_quality_checks.py`,
`docs/system_design.md` and `docs/module_explainer.md` reference the app; those
references stay in the research repo and are none of your business.

---

## 2. Get the code

Work in `~/gaze`. Pick **one** of these.

### Option A — preserve history (recommended)

`git subtree split` rewrites just this subdirectory's commits so the new repo
keeps real history for these files.

```bash
cd ~/gaze
# Use the user's existing clone if you found one; otherwise clone fresh:
git clone https://github.com/jawauntb/research-derived-experiments.git _source
cd _source
git checkout claude/create-this-6p3ecj        # or main, if PR #546 is merged
git subtree split -P apps/gazenotes -b gazenotes-only

cd ~/gaze
mkdir gazenotes && cd gazenotes
git init -b main
git pull ../_source gazenotes-only            # app files land at the repo ROOT
```

Verify: `ls` shows `gazenotes/ tests/ packaging/ pyproject.toml README.md`,
**not** an `apps/` directory. Then `rm -rf ~/gaze/_source` once you are happy.

### Option B — clean start, no history

```bash
cd ~/gaze && mkdir gazenotes && cd gazenotes
cp -R /path/to/research-derived-experiments/apps/gazenotes/. .
git init -b main && git add -A && git commit -m "Import gazenotes from research-derived-experiments@7f7a13b"
```

Reference the source commit in that message either way — it is the only
provenance link the new repo will have.

### Either way, add a `.gitignore` (the parent repo's covered this)

```
__pycache__/
*.py[cod]
.venv/
.pytest_cache/
build/
dist/
*.egg-info/
.DS_Store
```

---

## 3. Create the private remote

```bash
cd ~/gaze/gazenotes
gh repo create jawauntb/gazenotes --private --source=. --remote=origin --push
```

Confirm it is actually private before pushing anything else:

```bash
gh repo view jawauntb/gazenotes --json isPrivate,url
```

**This must stay private.** The repo will accumulate nothing sensitive by
itself, but the app captures screenshots of whatever is on screen and the user
may end up pasting real capture output into an issue. Do not flip it public,
and do not add collaborators.

---

## 4. Prove the extraction was clean

Before changing a single line, confirm you have the same green suite:

```bash
cd ~/gaze/gazenotes
python3.12 -m venv .venv && source .venv/bin/activate    # 3.11 or 3.12; NOT system 3.9
pip install -U pip
pip install -e '.[dev]'
python -m pytest tests -q          # expect: 387 passed
```

If that is not 387 passed, the extraction is wrong — fix that before anything
else. Do not start debugging macOS integration on top of a bad copy.

Then install the real capabilities:

```bash
pip install -e '.[all]'            # macos, gaze, browser, watch, ocr
playwright install chromium
```

Use **Python 3.11 or 3.12**. macOS system Python is 3.9 and the package
requires ≥3.11; mediapipe and opencv wheel availability is also best on
3.11/3.12. On Apple Silicon, if `pip install mediapipe` fails, that is a known
ecosystem problem, not a bug in this code — check the wheel exists for your
Python version before trying to fix anything in the app.

---

## 5. Bring-up, in the order most likely to save you time

Everything below is **unverified**. This ordering is deliberate: each step
unblocks the next, and the early ones are where the design says failure is most
likely.

### 5.1 `gazenotes doctor` — do this first

```bash
gazenotes doctor
```

It attempts each access rather than reading a permissions database, because
macOS TCC prompts attach to the process that asks. Expect prompts. Grant
Camera, Screen Recording and Accessibility to **the binary you are running**
(your terminal, or the `.app` once built — see §5.6).

`doctor` returns non-zero on failures and prints a fix line for each. Work the
list until only warnings remain.

### 5.2 Verify the Superwhisper path — highest-value unknown

`superwhisper_dir` defaults to `~/Documents/superwhisper/recordings`. **This
location has moved across Superwhisper versions and is very likely wrong.**

```bash
ls -la ~/Documents/superwhisper/recordings 2>/dev/null
find ~ -name "meta.json" -path "*superwhisper*" -maxdepth 6 2>/dev/null | head
```

Then:
1. Point `superwhisper_dir` in `~/GazeNotes/config.toml` at the real folder.
2. In Superwhisper's settings, **enable transcript/recording retention** — if it
   deletes recordings after typing them, gazenotes has nothing to watch.
3. Dictate once and inspect the actual `meta.json`. `gazenotes/watcher.py`
   accepts several key spellings (`result`, `text`, `transcript`, `llmResult`,
   `processedResult`) and epoch-or-ISO timestamps. If the real file uses
   something else, extend `_TEXT_KEYS` / `_parse_timestamp` **and add a test
   with the real shape** to `tests/test_watcher.py`.

Phase 1 acceptance: speak with any app frontmost → within 2 s a new entry with
transcript and a full-screen screenshot appears in `~/GazeNotes/<today>.md`.
Get this working before touching gaze at all. It is a useful product by itself.

### 5.3 Calibrate, then measure gaze honestly — the real risk

```bash
gazenotes displays      # confirm the screens it sees
gazenotes calibrate     # 9 dots, ~15 s
```

Calibration **refuses to save** a fit worse than 120 pt median error. If it
refuses, that is the gate working, not a bug — improve lighting, sit still,
remove glare, retry. Do not raise `MAX_MEDIAN_RESIDUAL_PT` to make it pass; a
confidently wrong crop is worse than no crop.

Then run the **actual Phase 2 acceptance test**, which has never been run:

> Look at the top / middle / bottom third of the screen and speak. The crop
> must contain the correct third **≥90% of the time across 20 trials.**

Record the real number. If it fails, tune in this order, re-measuring each time:
1. Lighting and seating distance (biggest effect by far).
2. `crop_height_fraction` (default 0.35) — a taller band is more forgiving.
3. `min_gaze_confidence` (default 0.35) — raising it discards more fixations,
   so more notes fall back to full-screen captures but fewer are *wrong*.
4. 16-point calibration: `gazenotes calibrate --points 16`.
5. Only then touch the feature vector or the one-euro filter constants in
   `gazenotes/gaze/model.py`.

Also re-measure after moving the laptop, and **write down how badly it
degrades** — the design explicitly asks for this and nobody has ever done it.

### 5.4 Chrome enrichment — verify the coordinate conversion

```bash
gazenotes chrome        # Chrome only opens the CDP port on a COLD start; Cmd-Q first
```

The screen→viewport conversion (`window_to_viewport`, chrome height from
`outerHeight - innerHeight`) is unit-tested but has never met a real window.
Build the debug overlay the design calls for: inject a dot at the computed
viewport point and confirm it lands where the user is actually looking. If it
is off by a constant, the chrome-height probe or the window origin is wrong —
check `screen.py::_front_window_for_pid` returns the bounds you expect.

Acceptance: reading an article and speaking yields an entry whose "Looking at"
text is the paragraph being read, and whose source link reopens to it.

### 5.5 OCR — has never met real Vision

`gazenotes/ocr.py` calls Apple Vision via pyobjc. The passage assembly, reading
order and confidence filtering are tested; **the pyobjc call sequence is not.**

The trap, already handled but worth re-verifying: Vision reports normalised
**bottom-left** coordinates, so reading order has to invert y. An inverted sort
produces a perfectly plausible passage that reads bottom-up — it will not look
like a bug. Test on a screenshot of a PDF with several paragraphs and check the
recovered text is in the right order.

`MIN_CONFIDENCE = 0.3` is a guess; tune it against real screenshots.

### 5.6 The `.app` build — written on Linux, never executed

`packaging/setup_app.py` exists so TCC grants attach to a stable
`com.gazenotes.app` bundle id instead of to your terminal. Read
`packaging/README.md` first; it opens by saying it has never been run and lists
what to confirm.

Realistic expectation: a first py2app build of a mediapipe + opencv app failing
is the normal outcome. Budget iterations. Likely failure order:
1. A missing module, or mediapipe `.tflite` model files not landing in
   `Contents/Resources`.
2. `screen.py` shelling out to `screencapture` — the child *should* inherit the
   bundle as responsible process for the screen-recording grant, but that is
   the least certain assumption. Fallback: capture in-process via Quartz.
3. Hardened-runtime entitlements for the Python dylibs.

Grants only persist across rebuilds if you sign with a **stable certificate** —
an ad-hoc signature changes the `cdhash` every build and re-prompts every time.

This is the lowest-priority item. A working daemon run from a terminal is worth
more than a broken `.app`.

---

## 6. Design rules — do not violate these while "optimizing"

These are load-bearing. The code enforces them and the tests pin them.

1. **Intentional capture.** Nothing is recorded until the user speaks. No
   ambient screen or audio recording. The pre-note screen buffer is the single
   sanctioned exception and it ships **off** (`screen_buffer_seconds = 0.0`);
   leave it off unless the user asks. Do not "improve" the app by making it
   always-on.
2. **Local only.** No network calls in the default configuration, including the
   nightly pass (`backend = "none"`). Do not add telemetry, crash reporting, or
   a cloud model.
3. **Coarse gaze, precise voice.** Never make an action depend on gaze
   precision finer than ~1/6 of screen height.
4. **Degrade, never block.** Every enrichment is wrapped so a failure downgrades
   an entry rather than losing a note. If you add an enrichment, wrap it the
   same way. A note must always get written.
5. **Plain files.** Markdown + PNG + JSON in a folder. Do not introduce a
   database.
6. **Entries are append-only.** Only the nightly pass rewrites, and only the
   summary block.
7. **Honest provenance in output.** DOM text renders as `**Looking at:**`, OCR
   as `**Looking at (OCR):**`. Do not collapse them — OCR of a screenshot is
   weaker evidence and the note must say so.

If a fix requires breaking one of these, stop and ask the user.

---

## 7. Known risks already catalogued

- **Calibration orphans.** A display whose `CGDirectDisplayID` changes (GPU mux
  switch, OS upgrade, a monitor with no EDID) reads as uncalibrated and nothing
  prunes the stale `calibration.json` entry. Soft failure; recalibrate.
- **Dwell scrolling is conservative by design.** After firing, the zone latches
  until you actually look away, so repeated paging costs a glance. If it feels
  slow, the honest lever is a shorter `cooldown_seconds` — *not* removing the
  latch, which reintroduces the runaway-scroll case it exists to prevent.
- **Dwell fails silent under bad lighting.** Confidence hovering under 0.5
  resets the dwell, so the feature reads as "broken" when gaze is merely poor.
  There is no menu-bar signal for this. Worth adding one.
- **Byte cap is strict.** Set `screen_buffer_max_mb` below one PNG and the
  buffer is silently always empty.
- **Multi-display calibration is in global coordinates.** A display physically
  moved needs a real recalibration; one merely rearranged in System Settings is
  auto-offset. Nothing can detect the former.

## 8. Privacy

Captures can contain anything on screen — inboxes, credentials, private
documents. `~/GazeNotes` should be excluded from cloud sync (iCloud Desktop &
Documents especially). `gazenotes purge <date>` deletes a day's note and every
capture behind it; it makes you type the date. Never paste raw capture output
into a public issue.

## 9. First session checklist

- [ ] Code extracted to `~/gaze/gazenotes`, app files at the repo root
- [ ] `python -m pytest tests -q` → 387 passed
- [ ] Private GitHub repo created and pushed; `isPrivate: true` confirmed
- [ ] `gazenotes doctor` clean of failures
- [ ] Real Superwhisper path found, retention on, one note captured end to end
- [ ] Calibration accepted; **screen-third accuracy measured over 20 trials and
      written down**
- [ ] Chrome CDP verified with a debug overlay
- [ ] Findings and any schema fixes committed with tests
