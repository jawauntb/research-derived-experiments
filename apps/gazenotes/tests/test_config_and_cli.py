"""Config loading, the CLI surface, and the doctor report."""

from __future__ import annotations

from pathlib import Path

import pytest

from gazenotes import cli
from gazenotes.config import Config, config_from_mapping, load_config, write_default_config
from gazenotes.doctor import FAIL, OK, WARN, Check, format_report


# -- config -------------------------------------------------------------
def test_defaults_apply_when_there_is_no_config_file(tmp_path):
    config = load_config(tmp_path / "missing.toml")
    assert config.command_prefix == "computer"
    assert config.crop_height_fraction == 0.35
    assert config.keep_full_screenshot is True
    assert config.nightly.backend == "none"


def test_the_written_default_config_parses_back_to_the_defaults(tmp_path):
    path = write_default_config(tmp_path / "config.toml")
    loaded = load_config(path)
    defaults = Config()
    assert loaded.command_prefix == defaults.command_prefix
    assert loaded.crop_height_fraction == defaults.crop_height_fraction
    assert loaded.dwell_scroll == defaults.dwell_scroll
    assert loaded.nightly.backend == defaults.nightly.backend


def test_write_default_config_never_clobbers_an_existing_file(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text('command_prefix = "jarvis"\n')
    write_default_config(path)
    assert load_config(path).command_prefix == "jarvis"


def test_paths_are_expanded():
    config = config_from_mapping({"notes_dir": "~/Elsewhere"})
    assert "~" not in str(config.notes_dir)
    assert config.notes_dir.is_absolute()


def test_unknown_keys_are_ignored_rather_than_fatal():
    config = config_from_mapping({"notes_dir": "/tmp/x", "future_option": 3})
    assert config.notes_dir == Path("/tmp/x")


def test_a_malformed_config_raises_at_startup(tmp_path):
    # Better a loud failure at start-up than silently running on defaults
    # while the user believes their settings took effect.
    import tomllib

    path = tmp_path / "config.toml"
    path.write_text("this is not = = toml")
    with pytest.raises(tomllib.TOMLDecodeError):
        load_config(path)


def test_derived_paths_hang_off_the_notes_dir(tmp_path):
    config = Config(notes_dir=tmp_path)
    assert config.captures_dir == tmp_path / "captures"
    assert config.calibration_path == tmp_path / "calibration.json"
    assert config.config_path == tmp_path / "config.toml"


def test_nightly_section_overrides_only_what_it_names():
    config = config_from_mapping({"nightly": {"backend": "api"}})
    assert config.nightly.backend == "api"
    assert config.nightly.api_key_env == "GAZENOTES_API_KEY"


# -- doctor report ------------------------------------------------------
def test_the_report_shows_fixes_only_for_problems():
    report = format_report(
        [
            Check("Notes folder", OK, "/Users/x/GazeNotes"),
            Check("Camera", FAIL, "could not open", "Grant camera access"),
            Check("Chrome CDP", WARN, "unreachable", "Run gazenotes chrome"),
        ]
    )
    assert "Grant camera access" in report
    assert "Run gazenotes chrome" in report
    assert "1 ok, 1 warnings, 1 failures" in report
    assert report.count("→") == 2


# -- CLI ----------------------------------------------------------------
def test_every_subcommand_is_wired_to_a_handler():
    parser = cli.build_parser()
    subparsers = [a for a in parser._actions if hasattr(a, "choices") and a.choices][0]
    assert set(subparsers.choices) == set(cli._COMMANDS)


def test_a_missing_subcommand_is_an_error():
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args([])


@pytest.mark.parametrize(
    "value,expected_offset",
    [("today", 0), ("yesterday", 1), (None, 0)],
)
def test_relative_dates(value, expected_offset):
    from datetime import date, timedelta

    assert cli._parse_day(value) == date.today() - timedelta(days=expected_offset)


def test_an_explicit_date_is_parsed():
    from datetime import date

    assert cli._parse_day("2026-09-01") == date(2026, 9, 1)


def test_an_invalid_date_is_rejected():
    with pytest.raises(ValueError):
        cli._parse_day("last tuesday")


def test_config_init_creates_the_file(tmp_path, capsys):
    path = tmp_path / "config.toml"
    args = cli.build_parser().parse_args(["--config", str(path), "config", "--init"])
    assert cli.cmd_config(args, Config(notes_dir=tmp_path)) == 0
    assert path.exists()
    assert "gazenotes configuration" in path.read_text()


def test_config_without_init_reports_the_missing_file(tmp_path, capsys):
    args = cli.build_parser().parse_args(["--config", str(tmp_path / "none.toml"), "config"])
    cli.cmd_config(args, Config(notes_dir=tmp_path))
    assert "using defaults" in capsys.readouterr().out


def test_nightly_command_reports_when_there_is_nothing_to_do(tmp_path, capsys):
    args = cli.build_parser().parse_args(["nightly", "2026-09-01"])
    assert cli.cmd_nightly(args, Config(notes_dir=tmp_path)) == 0
    assert "Nothing to summarise" in capsys.readouterr().out


def test_purge_requires_typing_the_date(tmp_path, monkeypatch, capsys):
    from datetime import date, datetime

    from gazenotes.events import Capture, NoteEvent
    from gazenotes.notes import DailyNotes

    notes = DailyNotes(tmp_path)
    notes.append(Capture(event=NoteEvent("x", 0, 0, datetime(2026, 9, 1, 10, 0, 0))))

    args = cli.build_parser().parse_args(["purge", "2026-09-01"])
    monkeypatch.setattr("builtins.input", lambda *_a: "nope")
    assert cli.cmd_purge(args, Config(notes_dir=tmp_path)) == 1
    assert notes.path_for(date(2026, 9, 1)).exists()

    monkeypatch.setattr("builtins.input", lambda *_a: "2026-09-01")
    assert cli.cmd_purge(args, Config(notes_dir=tmp_path)) == 0
    assert not notes.path_for(date(2026, 9, 1)).exists()


def test_purge_yes_skips_the_prompt(tmp_path, monkeypatch):
    from datetime import date, datetime

    from gazenotes.events import Capture, NoteEvent
    from gazenotes.notes import DailyNotes

    notes = DailyNotes(tmp_path)
    notes.append(Capture(event=NoteEvent("x", 0, 0, datetime(2026, 9, 1, 10, 0, 0))))
    monkeypatch.setattr("builtins.input", lambda *_a: (_ for _ in ()).throw(AssertionError("prompted")))
    args = cli.build_parser().parse_args(["purge", "2026-09-01", "--yes"])
    assert cli.cmd_purge(args, Config(notes_dir=tmp_path)) == 0
    assert not notes.path_for(date(2026, 9, 1)).exists()


def test_purge_on_an_empty_day_is_a_no_op(tmp_path, capsys):
    args = cli.build_parser().parse_args(["purge", "2026-09-01"])
    assert cli.cmd_purge(args, Config(notes_dir=tmp_path)) == 0
    assert "Nothing stored" in capsys.readouterr().out


# -- Phase 6 settings ---------------------------------------------------
def test_the_screen_buffer_is_off_unless_a_duration_is_configured():
    # This is the only part of gazenotes that records before the user speaks,
    # so a default install must not do it.
    assert Config().screen_buffer_seconds == 0.0
    assert Config().screen_buffer_enabled is False
    assert config_from_mapping({"screen_buffer_seconds": 60}).screen_buffer_enabled is True


def test_the_written_default_config_leaves_the_screen_buffer_off(tmp_path):
    path = write_default_config(tmp_path / "config.toml")
    assert load_config(path).screen_buffer_enabled is False
    assert load_config(path).dwell_scroll is False


def test_dwell_settings_are_a_section_with_their_own_defaults():
    from gazenotes.config import DwellSettings

    assert Config().dwell == DwellSettings()
    tuned = config_from_mapping({"dwell": {"dwell_seconds": 0.8}})
    assert tuned.dwell.dwell_seconds == 0.8
    assert tuned.dwell.cooldown_seconds == DwellSettings().cooldown_seconds


def test_section_values_are_coerced_to_their_field_types():
    tuned = config_from_mapping({"dwell": {"zone_fraction": 1}, "nightly": {"backend": "local"}})
    assert isinstance(tuned.dwell.zone_fraction, float)
    assert tuned.nightly.backend == "local"


def test_ocr_defaults_on_because_it_only_reads_an_already_saved_capture():
    assert Config().ocr_enabled is True
    assert config_from_mapping({"ocr_enabled": False}).ocr_enabled is False
