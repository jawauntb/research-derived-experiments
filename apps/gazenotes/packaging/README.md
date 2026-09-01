# Packaging gazenotes as a `.app`

> **Status: written, never run.** This build script was authored on Linux. No
> `.app` has been produced, launched, signed or granted a permission from it.
> Every command below is the *intended* procedure, not a transcript of one that
> worked. See [What has not been verified](#what-has-not-been-verified) before
> you trust any of it.

## Why a bundle at all

Not distribution. Nobody is shipping gazenotes to anyone.

macOS attaches TCC permissions — camera, screen recording, accessibility, the
Documents folder — to a **code identity**, not to a script. Run the daemon as
`python -m gazenotes` and the camera grant is recorded against your terminal, or
against whichever `python3` binary happened to resolve first. That identity is
not stable:

- rebuild `.venv`, or upgrade Python, and the interpreter path or its signature
  changes → macOS re-prompts, or hands back frames that are silently black;
- start the daemon from a different shell, from `launchd`, or from an editor,
  and the *responsible process* differs → a different grant;
- grant it to Terminal and you have granted the camera to **everything you ever
  run in a terminal**, which is worse than the problem.

A `.app` with the fixed bundle identifier `com.gazenotes.app` gives the daemon
one identity. Grant camera and screen recording once, to the bundle, and the
grants survive rebuilds — provided the identifier *and* the code signature stay
the same. That caveat is the whole story of the
[re-prompt section](#when-a-rebuild-re-prompts) below.

This is also the item listed as not-yet-built at the end of the app README:
"`.app` packaging for a stable TCC bundle ID".

## What gets built

| | |
|---|---|
| Bundle | `packaging/dist/GazeNotes.app` |
| Bundle ID | `com.gazenotes.app` |
| Version | read from `gazenotes.__version__` — never hardcoded |
| Launch behaviour | menu-bar only (`LSUIElement`), runs `gazenotes run` |
| Entry point | `packaging/build/launcher/gazenotes_app.py`, generated at build time |

`gazenotes/__main__.py` is *not* the bundle's entry point: it calls the CLI with
no arguments, and the CLI requires a subcommand, so a bundle launched from
Finder would die on an argparse error. `setup_app.py` generates a four-line
launcher that calls `main(["run"])` instead. It is generated rather than
committed so exactly one file decides what the app does on launch.

### Info.plist keys and why each one is there

| Key | Value | Why |
|---|---|---|
| `CFBundleIdentifier` | `com.gazenotes.app` | the TCC identity — the point of this exercise |
| `CFBundleVersion`, `CFBundleShortVersionString` | `gazenotes.__version__` | one source of truth |
| `LSUIElement` | `true` | menu-bar app: no Dock icon, no app switcher entry |
| `LSMinimumSystemVersion` | `13.0` | System Settings paths in `doctor` assume Ventura or later |
| `NSHighResolutionCapable` | `true` | Retina backing scale matters to the crop maths |
| `NSSupportsAutomaticTermination` / `NSSupportsSuddenTermination` | `false` | the daemon holds a camera thread and an advisory lock; a silent kill drops in-flight notes |
| `NSCameraUsageDescription` | see below | gaze estimation |
| `NSDocumentsFolderUsageDescription` | see below | reading Superwhisper transcripts |

The usage strings are what the user reads in the dialog, so they say what
gazenotes actually does:

- **Camera** — "watches your eyes through the webcam to estimate which part of
  the screen you are reading… Frames are processed in memory, are never written
  to disk, and never leave this Mac."
- **Documents folder** — "reads the transcripts Superwhisper saves in your
  Documents folder… It reads nothing else there and writes nothing."

**Keys deliberately absent:**

- `NSMicrophoneUsageDescription` — gazenotes never opens the microphone.
  Superwhisper records; gazenotes reads the transcript files it leaves behind.
  Claiming mic access would be a lie in a dialog box. (If the daemon ever grows
  its own audio capture, this key becomes mandatory — macOS terminates a process
  that touches the mic without one.)
- `NSAppleEventsUsageDescription` — Chrome is driven over CDP (a TCP socket) and
  files are opened with `/usr/bin/open` via LaunchServices. Neither sends an
  Apple event from our process.
- **Screen recording** and **Accessibility** have *no* Info.plist key at all.
  There is no usage-description string for either; macOS prompts on the first
  attempt and thereafter they are toggles in System Settings. They still attach
  to the bundle identity, so they benefit from the `.app` exactly as the camera
  does.

## Build

Use a **non-editable** install. py2app collects packages off the filesystem, and
a PEP 660 editable install (`pip install -e .`) leaves a `__editable__` finder
shim that it cannot follow into a bundle.

```bash
cd apps/gazenotes
python3.11 -m venv .venv-build
source .venv-build/bin/activate
pip install '.[all]'          # NOT -e
pip install py2app
playwright install chromium   # only if you want the browser extras to work

cd packaging
python setup_app.py py2app    # → dist/GazeNotes.app
```

Then, before anything else:

```bash
/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' \
    dist/GazeNotes.app/Contents/Info.plist          # must print com.gazenotes.app
/usr/libexec/PlistBuddy -c 'Print :LSUIElement' \
    dist/GazeNotes.app/Contents/Info.plist          # must print true
open dist/GazeNotes.app                              # 👁 appears in the menu bar
```

If nothing appears in the menu bar, run the executable directly — a bundle
launched from Finder swallows stderr:

```bash
dist/GazeNotes.app/Contents/MacOS/GazeNotes
```

Missing-module tracebacks at this stage are the normal outcome of a first
py2app build; add the module to `INCLUDES` or its package to `PACKAGES` in
`setup_app.py` and rebuild.

## Signing

An unsigned bundle gets an ad-hoc signature applied by the linker, and its
`cdhash` changes on **every rebuild**. Screen recording in particular keys off
the signature, so an unsigned bundle re-prompts after each build. For a stable
identity, sign with a real certificate (a free "Apple Development" identity from
Xcode is enough for local use):

```bash
security find-identity -v -p codesigning        # pick one

cat > entitlements.plist <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>com.apple.security.device.camera</key><true/>
  <!-- CPython and mediapipe/cv2 load unsigned or differently-signed dylibs -->
  <key>com.apple.security.cs.disable-library-validation</key><true/>
  <key>com.apple.security.cs.allow-unsigned-executable-memory</key><true/>
</dict>
</plist>
EOF

codesign --force --deep --options runtime \
  --entitlements entitlements.plist \
  --sign "Apple Development: you@example.com (TEAMID)" \
  dist/GazeNotes.app

codesign -dv --verbose=4 dist/GazeNotes.app     # check Identifier= and TeamIdentifier=
spctl -a -vv dist/GazeNotes.app                 # will complain unless notarised; fine locally
```

`entitlements.plist` is a build artifact — write it where you build, do not
commit it. `--deep` is deprecated by Apple; for a bundle with as many nested
dylibs as this one it is still the pragmatic choice, and the correct alternative
is to sign every `.so`/`.dylib` inner-out before the bundle.

## Granting permissions the first time

1. Launch `GazeNotes.app`.
2. Menu bar → the app runs `doctor`'s accesses as a side effect of starting:
   the camera opens (→ camera prompt) and the first note takes a screenshot
   (→ screen recording prompt). To force all prompts up front, run
   `dist/GazeNotes.app/Contents/MacOS/GazeNotes` once from a terminal — but note
   that then *the terminal* may become the responsible process for the prompt.
   Launching the bundle from Finder is the reliable way to attribute grants to
   `com.gazenotes.app`.
3. System Settings → Privacy & Security. Confirm **GazeNotes** (not "Terminal",
   not "Python") is listed and enabled under:
   - **Camera**
   - **Screen & System Audio Recording**
   - **Accessibility** (only needed for voice scrolling outside Chrome)
   - **Files and Folders → Documents Folder** (Superwhisper transcripts)
4. Screen recording requires a **restart of the app** after granting; macOS does
   not hand the permission to an already-running process.
5. If Terminal or Python still holds the old grants, revoke them — that is the
   cleanup this whole exercise is for:
   ```bash
   tccutil reset Camera            # all clients; then re-grant GazeNotes only
   tccutil reset ScreenCapture
   ```

### Verifying the grant landed on the bundle, not on Python

```bash
codesign -dv --verbose=4 dist/GazeNotes.app 2>&1 | grep Identifier
```

`Identifier=com.gazenotes.app` is what TCC records. To read TCC's own view you
need Full Disk Access for your terminal:

```bash
sqlite3 ~/Library/Application\ Support/com.apple.TCC/TCC.db \
  "select service, client, auth_value from access where client like '%gazenotes%';"
```

`kTCCServiceCamera` and `kTCCServiceScreenCapture` rows with
`client = com.gazenotes.app` and `auth_value = 2` mean the grants are attached
to the bundle and will survive an interpreter change.

## When a rebuild re-prompts

Re-prompting after a rebuild means the identity moved. In order of likelihood:

1. **Ad-hoc signature.** Unsigned/ad-hoc bundles get a new `cdhash` every build.
   Fix: sign with a stable certificate (above). This is the usual cause.
2. **The bundle moved.** TCC records the path alongside the identity for
   unsigned apps. Keep the app in one place — `/Applications` or
   `~/Applications` — and rebuild in place rather than dragging a fresh copy
   around.
3. **The identifier changed.** `codesign -dv` will show it. `BUNDLE_ID` in
   `setup_app.py` is a constant and `tests/test_packaging.py` asserts it, so
   this should only happen if someone edits both.
4. **A stale duplicate.** Two `GazeNotes.app`s on disk are two identities to
   macOS if unsigned. Delete the old one.

To start clean:

```bash
tccutil reset Camera com.gazenotes.app
tccutil reset ScreenCapture com.gazenotes.app
tccutil reset Accessibility com.gazenotes.app
tccutil reset SystemPolicyDocumentsFolder com.gazenotes.app
```

(`tccutil reset <service> <bundle-id>` only works for a bundle ID — another
small reason for the `.app`.)

## The hard parts, and what `setup_app.py` does about them

These are the dependencies that break py2app builds. `OPTIONS` encodes what can
be encoded; the rest is here.

- **mediapipe** — ships `.tflite` face-mesh models, binary graph configs and a
  `_framework_bindings` extension. py2app traces `import` statements, which
  finds none of that, so `mediapipe` is in `packages` (copied wholesale). If the
  bundle starts but gaze never produces a sample, look for a
  "graph config file not found" error on stderr and check
  `Contents/Resources/lib/python3.*/mediapipe/modules/` actually has the model
  files. The usual fallback is to add the missing directory to `resources`.
- **opencv-python** — bundles its own dylibs and a generated `config-*.py` that
  computes paths at import time. Also in `packages`. `strip` is turned **off**
  in `OPTIONS` because stripping these binaries invalidates their signatures.
- **playwright** — carries a Node driver binary under `playwright/driver/`.
  It is in `packages`, but the browser itself lives in
  `~/Library/Caches/ms-playwright` **outside** the bundle. That is fine here:
  gazenotes connects to your *existing* Chrome over CDP rather than launching a
  browser, so the driver matters and the downloaded chromium mostly does not.
  Expect this to be the first thing to break, and remember `browser.py` is a
  degradation path — the note still gets written without it.
- **numpy** — in `packages`; py2app's tracing of its lazy submodules is
  unreliable.
- **tkinter** — the calibration UI. It is in `includes` precisely because the
  instinct to exclude it (to slim the bundle) silently breaks
  `computer recalibrate`, and nothing tells you until you try.
- **pyobjc** — Quartz, Cocoa, ApplicationServices and rumps are handled by
  py2app's own recipes and are not listed explicitly. If `screen.py` fails to
  import Quartz inside the bundle, add the framework packages to `INCLUDES`.
- **`screencapture` as a subprocess** — `screen.py` shells out to
  `/usr/sbin/screencapture` rather than calling `CGWindowListCreateImage`. The
  child process should inherit the bundle as its *responsible process*, so the
  screen-recording grant should apply. **This is the single most uncertain
  assumption in the design** — if screenshots come back black or empty inside
  the bundle while `gazenotes doctor` in a terminal works, this is why, and the
  fix is to capture through Quartz in-process instead.
- **Bundle size** — mediapipe + opencv + numpy + playwright is several hundred
  megabytes before compression. Nothing in `OPTIONS` meaningfully changes that,
  and for a local daemon it does not matter.

## Running it as a login item

Once the bundle works, replace the `launchd` job's interpreter path:
System Settings → General → Login Items → add `GazeNotes.app`. Launching the
*bundle* is the point; a `launchd` plist that runs `/usr/local/bin/gazenotes`
puts you back on the unstable identity. `launchd/com.gazenotes.nightly.plist`
can stay as it is — the nightly pass touches no TCC-protected resource.

## What has not been verified

Written on Linux. Confirm every one of these on a Mac before believing them:

- [ ] **The build runs at all.** `python setup_app.py py2app` has never been
      executed. Syntax and options are from the py2app docs, not from a build.
- [ ] **The bundle launches.** A first py2app build of a mediapipe/opencv app
      failing on a missing module is the *expected* outcome, not a surprise.
- [ ] **`packages`/`includes` are sufficient.** The list is reasoned from this
      app's imports and the known behaviour of these libraries. It is a
      starting point; expect to add entries.
- [ ] **mediapipe's model files land in the bundle** and the face mesh actually
      loads from inside it.
- [ ] **The camera prompt is attributed to `com.gazenotes.app`** rather than to
      a parent process.
- [ ] **Screen recording works through `screencapture` inside the bundle** (see
      above — the most likely failure).
- [ ] **Grants survive a rebuild** with a stable signing identity. The claim
      that a Developer ID signature makes them stick is standard practice, not
      something measured here.
- [ ] **The entitlements list is right.** `disable-library-validation` and
      `allow-unsigned-executable-memory` are the usual pair for a hardened
      Python bundle; whether *this* bundle needs both is untested.
- [ ] **Tk calibration renders** from inside the bundle (Tk in a py2app bundle
      has its own history of missing framework issues).
- [ ] **`LSUIElement` behaves** — that the app really shows only a menu-bar item
      and that rumps' event loop is happy as the bundle's main thread.
- [ ] The minimum macOS version. `13.0` is an assumption, not a tested floor.

`tests/test_packaging.py` covers the parts that *are* checkable off a Mac: the
bundle ID, the plist keys, `LSUIElement`, that the version tracks
`gazenotes.__version__`, that the usage strings are real sentences describing
real behaviour, and that importing `setup_app.py` builds nothing. It cannot
tell you the bundle will launch, and it does not test py2app.
