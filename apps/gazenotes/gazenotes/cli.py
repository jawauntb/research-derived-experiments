"""``gazenotes`` command line: run, doctor, calibrate, nightly, chrome, purge."""

from __future__ import annotations

import argparse
import logging
import shutil
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from . import __version__
from .config import Config, load_config, write_default_config

__all__ = ["main", "build_parser"]

CHROME_BINARY = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def _parse_day(value: str | None) -> date:
    """Accept ``YYYY-MM-DD``, ``today``, or ``yesterday``."""
    if value in (None, "", "today"):
        return date.today()
    if value == "yesterday":
        return date.today() - timedelta(days=1)
    return datetime.strptime(value, "%Y-%m-%d").date()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gazenotes", description=__doc__)
    parser.add_argument("--version", action="version", version=f"gazenotes {__version__}")
    parser.add_argument("--config", type=Path, default=None, help="path to config.toml")
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("run", help="run the daemon (default)")
    sub.add_parser("doctor", help="check permissions and dependencies")

    calibrate = sub.add_parser("calibrate", help="calibrate gaze on this display")
    calibrate.add_argument("--points", type=int, default=9, choices=(9, 16))

    nightly = sub.add_parser("nightly", help="write the summary block for a day")
    nightly.add_argument("date", nargs="?", default="today")

    chrome = sub.add_parser("chrome", help="launch Chrome with remote debugging")
    chrome.add_argument("--port", type=int, default=9222)
    chrome.add_argument("--profile", default=None, help="user-data-dir (default: your own)")

    purge = sub.add_parser("purge", help="delete a day's note and captures")
    purge.add_argument("date")
    purge.add_argument("--yes", action="store_true", help="skip the confirmation prompt")

    config_cmd = sub.add_parser("config", help="show or create the config file")
    config_cmd.add_argument("--init", action="store_true", help="write a default config.toml")

    return parser


def _load(args) -> Config:
    return load_config(args.config)


def cmd_run(args, config: Config) -> int:
    from .daemon import Daemon
    from .menubar import build_menu

    daemon = Daemon(config)
    menu = build_menu(
        open_today=daemon.open_today,
        recalibrate=daemon.recalibrate,
        toggle_gaze=daemon.toggle_gaze,
        quit=lambda: sys.exit(0),
    )
    menu.set_runner(daemon.run)
    try:
        menu.run()
    except KeyboardInterrupt:
        daemon.stop()
    return 0


def cmd_doctor(args, config: Config) -> int:
    from .doctor import FAIL, format_report, run_checks

    checks = run_checks(config)
    print(format_report(checks))
    return 1 if any(c.status == FAIL for c in checks) else 0


def cmd_calibrate(args, config: Config) -> int:
    from .daemon import Daemon
    from .gaze.calibrate import CalibrationPlan

    daemon = Daemon(config)
    if daemon.gaze is None:
        print("Gaze engine unavailable. Run `gazenotes doctor`.", file=sys.stderr)
        return 1

    status = daemon.gaze.start(require_calibration=False)
    if not status.available and status.reason.startswith("missing dependency"):
        print(f"Cannot calibrate: {status.reason}", file=sys.stderr)
        return 1

    from .gaze.calibrate import show_calibration_ui

    result = show_calibration_ui(
        daemon.display_rect(),
        daemon.gaze.current_features,
        calibration_path=config.calibration_path,
        display_key=daemon.display_key(),
        plan=CalibrationPlan(points=args.points),
    )
    daemon.gaze.stop()
    if result.accepted:
        print(f"Calibrated: median error {result.residual_px:.0f} pt over {result.samples} samples.")
        print(f"Saved to {config.calibration_path}")
        return 0
    print(f"Calibration rejected: {result.reason}", file=sys.stderr)
    return 1


def cmd_nightly(args, config: Config) -> int:
    from .nightly import run_nightly

    path = run_nightly(config, _parse_day(args.date))
    if path is None:
        print("Nothing to summarise.")
        return 0
    print(f"Wrote summary to {path}")
    return 0


def cmd_chrome(args, config: Config) -> int:
    """Launch Chrome with CDP enabled, against the user's real profile."""
    if not Path(CHROME_BINARY).exists() and shutil.which("google-chrome") is None:
        print("Google Chrome not found.", file=sys.stderr)
        return 1
    binary = CHROME_BINARY if Path(CHROME_BINARY).exists() else shutil.which("google-chrome")
    command = [str(binary), f"--remote-debugging-port={args.port}"]
    if args.profile:
        command.append(f"--user-data-dir={Path(args.profile).expanduser()}")
    print(" ".join(command))
    print(
        "\nNote: Chrome only opens the debugging port on a cold start. Quit Chrome\n"
        "completely (Cmd-Q) before running this, or the flag is ignored."
    )
    subprocess.Popen(command, start_new_session=True)
    return 0


def cmd_purge(args, config: Config) -> int:
    from .notes import DailyNotes

    day = _parse_day(args.date)
    notes = DailyNotes(config.notes_dir)
    targets = [p for p in (notes.path_for(day), notes.capture_dir(day)) if p.exists()]
    if not targets:
        print(f"Nothing stored for {day}.")
        return 0
    if not args.yes:
        print("This will permanently delete:")
        for target in targets:
            print(f"  {target}")
        if input("Type the date to confirm: ").strip() != day.isoformat():
            print("Aborted.")
            return 1
    for removed in notes.purge(day):
        print(f"removed {removed}")
    return 0


def cmd_config(args, config: Config) -> int:
    path = args.config or config.config_path
    if args.init:
        written = write_default_config(path)
        print(f"Config at {written}")
        return 0
    if not Path(path).expanduser().is_file():
        print(f"No config at {path} (using defaults). Run `gazenotes config --init`.")
        return 0
    print(Path(path).expanduser().read_text(encoding="utf-8"))
    return 0


_COMMANDS = {
    "run": cmd_run,
    "doctor": cmd_doctor,
    "calibrate": cmd_calibrate,
    "nightly": cmd_nightly,
    "chrome": cmd_chrome,
    "purge": cmd_purge,
    "config": cmd_config,
}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    config = _load(args)
    return _COMMANDS[args.command](args, config)
