"""The .app build script: the plist that decides whether TCC grants stick.

These tests run anywhere, because ``packaging/setup_app.py`` is deliberately
import-safe. They check the parts that are actually checkable off a Mac — the
bundle identity, the usage strings the user will read in the permission dialog,
and the fact that importing the module builds nothing. They do not test py2app,
and they cannot tell you the bundle will launch.
"""

from __future__ import annotations

import ast
import importlib.util
import plistlib
from pathlib import Path

import pytest

import gazenotes

APP_ROOT = Path(__file__).resolve().parents[1]
SETUP_APP_PATH = APP_ROOT / "packaging" / "setup_app.py"


def _load_setup_app(name: str = "gazenotes_setup_app"):
    """Import the build script by path, without touching ``sys.path``."""
    spec = importlib.util.spec_from_file_location(name, SETUP_APP_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


setup_app = _load_setup_app()

USAGE_KEYS = [key for key in setup_app.PLIST if key.endswith("UsageDescription")]


# -- bundle identity ----------------------------------------------------
def test_the_bundle_id_is_the_constant_the_tcc_grants_are_attached_to():
    assert setup_app.BUNDLE_ID == "com.gazenotes.app"
    assert setup_app.PLIST["CFBundleIdentifier"] == "com.gazenotes.app"


def test_the_plist_has_every_key_a_launchable_bundle_needs():
    required = {
        "CFBundleName",
        "CFBundleIdentifier",
        "CFBundleVersion",
        "CFBundleShortVersionString",
        "CFBundlePackageType",
        "LSMinimumSystemVersion",
        "LSUIElement",
        "NSCameraUsageDescription",
    }
    assert required <= set(setup_app.PLIST)
    assert setup_app.PLIST["CFBundleName"] == "GazeNotes"


def test_lsuielement_is_true_so_the_menu_bar_app_gets_no_dock_icon():
    assert setup_app.PLIST["LSUIElement"] is True


def test_the_plist_survives_a_round_trip_through_plistlib():
    """py2app writes this dict with plistlib; unserialisable values fail late."""
    restored = plistlib.loads(plistlib.dumps(setup_app.PLIST))
    assert restored == setup_app.PLIST


# -- version ------------------------------------------------------------
def test_the_bundle_version_tracks_the_package_version():
    assert setup_app.VERSION == gazenotes.__version__
    assert setup_app.PLIST["CFBundleVersion"] == gazenotes.__version__
    assert setup_app.PLIST["CFBundleShortVersionString"] == gazenotes.__version__


def test_the_version_is_read_not_hardcoded():
    plist = setup_app.build_plist("9.9.9")
    assert plist["CFBundleVersion"] == "9.9.9"
    assert plist["CFBundleShortVersionString"] == "9.9.9"
    assert setup_app.PLIST["CFBundleVersion"] == gazenotes.__version__  # unchanged


def test_the_source_fallback_reads_the_same_version_as_the_import():
    init_path = APP_ROOT / "gazenotes" / "__init__.py"
    assert setup_app._version_from_source(init_path) == gazenotes.__version__


def test_a_source_file_without_a_version_is_an_error_not_a_silent_default(tmp_path):
    path = tmp_path / "__init__.py"
    path.write_text('"""no version here"""\n', encoding="utf-8")
    with pytest.raises(RuntimeError):
        setup_app._version_from_source(path)


# -- usage strings ------------------------------------------------------
def test_the_camera_string_describes_what_gazenotes_does_with_the_camera():
    text = setup_app.PLIST["NSCameraUsageDescription"]
    assert len(text) > 60
    lowered = text.lower()
    assert "webcam" in lowered or "camera" in lowered
    assert "look" in lowered or "read" in lowered or "gaze" in lowered


def test_the_documents_string_names_superwhisper_the_actual_reason_for_access():
    text = setup_app.PLIST["NSDocumentsFolderUsageDescription"]
    assert "superwhisper" in text.lower()


def test_every_usage_string_is_a_real_sentence():
    assert USAGE_KEYS, "the bundle needs at least a camera usage string"
    for key in USAGE_KEYS:
        text = setup_app.PLIST[key]
        assert isinstance(text, str)
        assert text.strip() == text
        assert len(text) > 40, f"{key} is too short to explain anything"
        assert text.endswith("."), f"{key} should read as a sentence"


def test_no_microphone_string_because_gazenotes_never_opens_the_mic():
    """Superwhisper records the audio; gazenotes only reads its transcripts."""
    assert "NSMicrophoneUsageDescription" not in setup_app.PLIST


# -- py2app options -----------------------------------------------------
def test_the_options_carry_the_plist_and_the_awkward_packages():
    options = setup_app.OPTIONS
    assert options["plist"]["CFBundleIdentifier"] == setup_app.BUNDLE_ID
    for package in ("gazenotes", "mediapipe", "cv2", "numpy", "playwright"):
        assert package in options["packages"], f"{package} must be copied wholesale"
    assert options["argv_emulation"] is False
    assert options["strip"] is False


def test_tkinter_is_included_because_calibration_is_a_tk_ui():
    assert "tkinter" in setup_app.OPTIONS["includes"]
    assert "tkinter" not in setup_app.OPTIONS["excludes"]


def test_dev_only_packages_are_excluded_from_the_bundle():
    assert "pytest" in setup_app.OPTIONS["excludes"]


def test_build_options_hands_back_a_copy_callers_cannot_corrupt():
    options = setup_app.build_options()
    options["packages"].append("nonsense")
    options["plist"]["CFBundleIdentifier"] = "com.example.wrong"
    assert "nonsense" not in setup_app.OPTIONS["packages"]
    assert setup_app.PLIST["CFBundleIdentifier"] == setup_app.BUNDLE_ID


# -- importing builds nothing -------------------------------------------
def test_no_build_call_runs_at_import_time():
    """setup() and the launcher write both sit inside functions, not at module level."""
    source = SETUP_APP_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    body = tree.body
    guards = [node for node in body if isinstance(node, ast.If)]
    assert guards, "the build must sit behind a __main__ guard"
    assert 'if __name__ == "__main__":' in source

    executed_on_import = [
        node
        for node in body
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.If))
    ]
    called = {
        sub.func.id
        for node in executed_on_import
        for sub in ast.walk(node)
        if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name)
    }
    assert "setup" not in called
    assert "write_launcher" not in called
    assert "main" not in called


def test_importing_the_module_writes_no_files(tmp_path):
    copy = tmp_path / "setup_app.py"
    copy.write_bytes(SETUP_APP_PATH.read_bytes())
    spec = importlib.util.spec_from_file_location("gazenotes_setup_app_copy", copy)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.PLIST["CFBundleIdentifier"] == setup_app.BUNDLE_ID
    created = {p.name for p in tmp_path.iterdir()} - {"__pycache__"}
    assert created == {"setup_app.py"}, f"importing created {created - {'setup_app.py'}}"


# -- the generated launcher ---------------------------------------------
def test_the_launcher_is_only_written_when_asked_and_runs_the_daemon(tmp_path):
    target = setup_app.write_launcher(tmp_path / "launcher")
    assert target.is_file()
    source = target.read_text(encoding="utf-8")
    compile(source, str(target), "exec")  # it has to be valid Python
    assert "from gazenotes.cli import main" in source
    assert '["run"]' in source, "the bundle has no argv, so it must pass the subcommand"
