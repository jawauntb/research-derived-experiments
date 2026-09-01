"""py2app build for GazeNotes — a bundle so macOS stops forgetting the grants.

macOS attaches TCC permissions (camera, screen recording, accessibility, the
Documents folder) to a *code identity*, not to a script. Run the daemon as
``python -m gazenotes`` and the camera grant belongs to Terminal, or to
whichever ``python3`` binary happened to be first on PATH. Rebuild the venv,
upgrade Python, move the checkout, or start the daemon from a different shell,
and the identity changes: macOS re-prompts, or worse, silently hands back black
frames. A re-prompt in the middle of a sentence is a lost note.

A ``.app`` with a fixed bundle identifier — ``com.gazenotes.app`` — gives the
daemon one identity that survives all of that. Grant camera and screen
recording once, to the bundle, and the grants stick across rebuilds as long as
the identifier *and* the code signature stay the same. That is the whole point
of this file. Distribution is not: nobody is shipping this to anyone.

This module is import-safe: it defines the Info.plist and the py2app options as
plain data, needs no py2app to import, and builds nothing until ``main()`` is
called from ``__main__``. That is what lets ``tests/test_packaging.py`` assert
on the plist from Linux.

Build (on a Mac, see ``packaging/README.md``)::

    cd apps/gazenotes/packaging
    python setup_app.py py2app

**Nothing in this file has been executed.** It was written on Linux against the
py2app docs and this app's imports. See the "Not verified" section of
``packaging/README.md`` before trusting a line of it.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

__all__ = [
    "APP_NAME",
    "BUNDLE_ID",
    "LAUNCHER_SOURCE",
    "OPTIONS",
    "PLIST",
    "VERSION",
    "app_version",
    "build_options",
    "build_plist",
    "main",
    "write_launcher",
]

HERE = Path(__file__).resolve().parent
APP_ROOT = HERE.parent
LAUNCHER_DIR = HERE / "build" / "launcher"

APP_NAME = "GazeNotes"
BUNDLE_ID = "com.gazenotes.app"
MIN_MACOS = "13.0"
COPYRIGHT = "MIT licensed. Nothing leaves the machine."


# -- version ------------------------------------------------------------
def _version_from_source(init_path: Path) -> str:
    """Read ``__version__`` out of ``gazenotes/__init__.py`` without importing.

    The build venv normally has gazenotes installed, but a source read keeps
    the bundle version honest even when it does not — better a correct version
    from the file next door than a hardcoded string that silently goes stale.
    """
    text = init_path.read_text(encoding="utf-8")
    match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
    if match is None:
        raise RuntimeError(f"no __version__ in {init_path}")
    return match.group(1)


def app_version() -> str:
    """The bundle version — always ``gazenotes.__version__``, never a literal."""
    try:
        from gazenotes import __version__
    except ImportError:
        return _version_from_source(APP_ROOT / "gazenotes" / "__init__.py")
    return __version__


VERSION = app_version()


# -- Info.plist ---------------------------------------------------------
# Usage strings are what the user reads in the permission dialog, so they say
# what gazenotes actually does. Keys the app does *not* need are deliberately
# absent and listed in packaging/README.md — an untrue usage string is worse
# than a missing one, and macOS only shows the key that is actually requested.
#
# Two permissions gazenotes needs have no Info.plist key at all:
#   * Screen recording — granted on first `screencapture`/CGWindowList attempt
#     and only editable in System Settings; there is no usage-description key.
#   * Accessibility — same, via AXIsProcessTrustedWithOptions.
# Both still attach to the bundle identity, which is why they benefit from the
# .app just as much as the camera does.
def build_plist(version: str = VERSION) -> dict[str, object]:
    """The Info.plist body. Pure data, so a test can read it anywhere."""
    return {
        "CFBundleName": APP_NAME,
        "CFBundleDisplayName": APP_NAME,
        "CFBundleIdentifier": BUNDLE_ID,
        # Both version keys track gazenotes.__version__. CFBundleVersion is the
        # build identity macOS compares; keeping them equal keeps it simple.
        "CFBundleVersion": version,
        "CFBundleShortVersionString": version,
        "CFBundlePackageType": "APPL",
        "CFBundleInfoDictionaryVersion": "6.0",
        "LSMinimumSystemVersion": MIN_MACOS,
        "LSApplicationCategoryType": "public.app-category.productivity",
        # The daemon is a menu-bar item (rumps). LSUIElement keeps it out of
        # the Dock and the app switcher; without it macOS gives the bundle a
        # Dock icon and a menu bar it has no windows for.
        "LSUIElement": True,
        "NSHighResolutionCapable": True,
        # The daemon holds a camera thread and an advisory lock. Letting macOS
        # terminate it behind our back would drop in-flight notes.
        "NSSupportsAutomaticTermination": False,
        "NSSupportsSuddenTermination": False,
        "NSHumanReadableCopyright": COPYRIGHT,
        "NSCameraUsageDescription": (
            "GazeNotes watches your eyes through the webcam to estimate which part of the screen "
            "you are reading, so a note you dictate can be paired with the passage you were "
            "looking at. Frames are processed in memory, are never written to disk, and never "
            "leave this Mac."
        ),
        "NSDocumentsFolderUsageDescription": (
            "GazeNotes reads the transcripts Superwhisper saves in your Documents folder to know "
            "when you have spoken a note. It reads nothing else there and writes nothing."
        ),
    }


PLIST = build_plist()


# -- py2app options -----------------------------------------------------
# `packages` copies a package directory wholesale into the bundle; `includes`
# adds single modules to the import graph. Anything with data files, lazy
# imports or bundled dylibs has to be in `packages` — py2app's import tracing
# finds .py files, not .tflite models or .dylibs sitting next to them.
PACKAGES = [
    # Our own package: every platform adapter is imported lazily (that is the
    # design), so tracing from the launcher would miss screen.py, capture.py,
    # browser.py and menubar.py entirely.
    "gazenotes",
    # MediaPipe: face-mesh .tflite models and binary graph configs live inside
    # the package, plus the _framework_bindings extension. Tracing gets none of it.
    "mediapipe",
    # protobuf runtime that mediapipe imports as `google.protobuf`.
    "google",
    # opencv-python ships its own dylibs and a generated config*.py that
    # computes paths at import time.
    "cv2",
    "numpy",
    # Playwright carries a node driver binary under playwright/driver.
    "playwright",
    "rumps",
    "watchdog",
]

INCLUDES = [
    # Lazily imported by cli.py / daemon.py, named explicitly so the graph is
    # not relying solely on the `gazenotes` package copy above.
    "gazenotes.cli",
    "gazenotes.daemon",
    "gazenotes.menubar",
    "gazenotes.screen",
    "gazenotes.browser",
    "gazenotes.nightly",
    "gazenotes.gaze.capture",
    "gazenotes.gaze.calibrate",
    # The calibration UI is Tk. Excluding tkinter to slim the bundle breaks
    # `computer recalibrate` and nothing tells you until you try it.
    "tkinter",
]

EXCLUDES = [
    # Dev-only, or pulled in transitively by things that only need them at
    # build time. None of these are imported by the daemon.
    "pytest",
    "_pytest",
    "ruff",
    "matplotlib",
    "pandas",
    "scipy",
    "IPython",
    "jupyter",
    "notebook",
    "PyQt5",
    "PyQt6",
    "PySide2",
    "PySide6",
    "tests",
    "pip",
    "wheel",
]

# Copied verbatim into Contents/Resources. Empty on purpose: the model files
# gazenotes needs belong to mediapipe and arrive via `packages` above, which is
# the reliable path. Add an .icns here if one is ever drawn — an LSUIElement
# app shows no Dock icon, so it would only matter in Finder.
RESOURCES: list[str] = []


def build_options(plist: dict[str, object] | None = None) -> dict[str, object]:
    """The ``py2app`` option dict. Also pure data — no py2app import needed."""
    return {
        "plist": dict(PLIST if plist is None else plist),
        "packages": list(PACKAGES),
        "includes": list(INCLUDES),
        "excludes": list(EXCLUDES),
        "resources": list(RESOURCES),
        # argv_emulation needs Carbon event handling and hangs LSUIElement apps.
        # The bundle takes no arguments anyway.
        "argv_emulation": False,
        # Stripping rewrites the binaries mediapipe and cv2 ship and can break
        # their signatures. A fat bundle that runs beats a lean one that does not.
        "strip": False,
        "optimize": 0,
        "alias": False,
        "semi_standalone": False,
    }


OPTIONS = build_options()


# -- entry point --------------------------------------------------------
# `gazenotes/__main__.py` calls `main()` with no argv, and the CLI requires a
# subcommand — an app bundle passes none, so it would exit with an argparse
# error. The bundle therefore gets a generated launcher that always runs the
# daemon. It is generated rather than committed so there is exactly one place
# (this file) that decides what the .app does on launch.
LAUNCHER_SOURCE = '''\
"""Generated by packaging/setup_app.py — do not edit, do not commit.

The .app has no command line, so it always runs the daemon.
"""

import sys

from gazenotes.cli import main

sys.exit(main(["run"]))
'''


def write_launcher(directory: Path = LAUNCHER_DIR) -> Path:
    """Write the generated bundle entry point and return its path."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "gazenotes_app.py"
    target.write_text(LAUNCHER_SOURCE, encoding="utf-8")
    return target


def main(argv: list[str] | None = None) -> int:
    """Run the py2app build. Only ever called from ``__main__``."""
    if importlib.util.find_spec("py2app") is None:
        print(
            "py2app is not installed in this interpreter.\n"
            "  pip install py2app\n"
            "and build with the same interpreter that has gazenotes[all] installed.",
            file=sys.stderr,
        )
        return 1
    if sys.platform != "darwin":
        print(f"py2app builds macOS bundles; this is {sys.platform}.", file=sys.stderr)
        return 1

    from setuptools import setup

    launcher = write_launcher()
    setup(
        name=APP_NAME,
        version=VERSION,
        app=[str(launcher)],
        options={"py2app": build_options()},
        script_args=list(argv) if argv is not None else sys.argv[1:],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
