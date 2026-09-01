"""Voice commands: parsing (pure) and execution (adapters).

A transcript beginning with the configured prefix — "computer" by default — is
a command, not a note, and is never written to the daily file.

Parsing is deliberately forgiving: dictation gives "computer, scroll down."
with punctuation, spelled-out numbers, and the occasional homophone.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass

log = logging.getLogger(__name__)

__all__ = ["Command", "parse_command", "word_to_int", "CommandRouter"]

_NUMBER_WORDS = {
    "zero": 0, "one": 1, "won": 1, "two": 2, "to": 2, "too": 2, "three": 3,
    "four": 4, "for": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "ate": 8,
    "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40,
    "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}


def word_to_int(text: str) -> int | None:
    """Parse "17", "seventeen", or "twenty three" into an int."""
    text = text.strip().lower().replace("-", " ")
    if not text:
        return None
    if text.isdigit():
        return int(text)
    total = 0
    matched = False
    for token in text.split():
        if token.isdigit():
            total += int(token)
            matched = True
        elif token in _NUMBER_WORDS:
            total += _NUMBER_WORDS[token]
            matched = True
        elif token in {"and"}:
            continue
        else:
            return None
    return total if matched else None


@dataclass(frozen=True)
class Command:
    """A parsed voice command."""

    name: str
    argument: str = ""
    number: int | None = None


def _normalise(text: str) -> str:
    return re.sub(r"[^\w\s]", " ", text.lower()).strip()


def parse_command(transcript: str, prefix: str = "computer") -> Command | None:
    """Parse a transcript into a :class:`Command`, or ``None`` if it is a note.

    An unrecognised phrase after the prefix returns ``Command("unknown", ...)``
    rather than ``None``: the user clearly addressed the machine, and silently
    filing that as a note would be worse than reporting that it missed.
    """
    words = _normalise(transcript).split()
    prefix_words = _normalise(prefix).split()
    if not words or words[: len(prefix_words)] != prefix_words:
        return None
    rest = words[len(prefix_words):]
    if not rest:
        return Command("unknown", "")

    joined = " ".join(rest)
    head = rest[0]

    if head in {"scroll", "page"}:
        direction = rest[1] if len(rest) > 1 else "down"
        if direction in {"up", "back", "backward"}:
            return Command("page_up" if head == "page" else "scroll_up")
        if direction in {"down", "forward"}:
            return Command("page_down" if head == "page" else "scroll_down")
        if direction in {"top", "bottom"}:
            return Command(f"scroll_{direction}")
        return Command("scroll_down")

    if head in {"click", "press", "open"} and len(rest) > 1:
        number = word_to_int(" ".join(rest[1:]))
        if number is not None:
            return Command("click", number=number)
        return Command("click_text", argument=" ".join(rest[1:]))

    if head in {"show", "hide"} and "number" in joined:
        return Command("show_numbers" if head == "show" else "hide_numbers")

    if head in {"recalibrate", "calibrate"} or joined.startswith("re calibrate"):
        return Command("recalibrate")

    if joined.startswith("new section"):
        return Command("new_section", argument=" ".join(rest[2:]).strip())

    if head in {"back", "backward"}:
        return Command("back")
    if head in {"forward"}:
        return Command("forward")
    if head == "dwell" and len(rest) > 1:
        return Command("dwell_on" if rest[1] in {"on", "start"} else "dwell_off")

    if head in {"pause", "stop"}:
        return Command("pause")
    if head in {"resume", "start"}:
        return Command("resume")

    return Command("unknown", argument=joined)


NUMBER_OVERLAY_SCRIPT = """
(options) => {
  const OLD = document.getElementById('__gazenotes_badges');
  if (OLD) OLD.remove();
  if (!options.show) return 0;
  const host = document.createElement('div');
  host.id = '__gazenotes_badges';
  host.style.cssText = 'position:fixed;inset:0;z-index:2147483647;pointer-events:none';
  const targets = Array.from(document.querySelectorAll('a[href],button,[role=button],input,select,textarea,summary'));
  const map = [];
  let index = 0;
  for (const el of targets) {
    const r = el.getBoundingClientRect();
    if (r.width < 8 || r.height < 8) continue;
    if (r.bottom < 0 || r.top > innerHeight || r.right < 0 || r.left > innerWidth) continue;
    const style = getComputedStyle(el);
    if (style.visibility === 'hidden' || style.display === 'none' || style.opacity === '0') continue;
    index += 1;
    map.push(index);
    el.setAttribute('data-gazenotes-badge', String(index));
    const badge = document.createElement('div');
    badge.textContent = String(index);
    badge.style.cssText =
      'position:absolute;left:' + Math.max(0, r.left - 6) + 'px;top:' + Math.max(0, r.top - 6) + 'px;' +
      'background:#ffcc00;color:#111;font:bold 11px/1.4 -apple-system,sans-serif;' +
      'padding:0 4px;border-radius:3px;box-shadow:0 1px 3px rgba(0,0,0,.4)';
    host.appendChild(badge);
    if (index >= options.limit) break;
  }
  document.body.appendChild(host);
  if (options.timeoutMs > 0) {
    setTimeout(() => { const h = document.getElementById('__gazenotes_badges'); if (h) h.remove(); },
               options.timeoutMs);
  }
  return map.length;
}
"""

CLICK_BADGE_SCRIPT = """
(n) => {
  const el = document.querySelector('[data-gazenotes-badge="' + n + '"]');
  if (!el) return false;
  el.scrollIntoView({block: 'center', behavior: 'instant'});
  el.click();
  return true;
}
"""


class CommandRouter:
    """Executes commands against Chrome when possible, Quartz otherwise.

    Every handler returns a short human-readable string for the log and menu
    bar, so a command that could not run says why instead of failing silently.
    """

    def __init__(
        self,
        *,
        bridge=None,
        screen=None,
        gaze=None,
        recalibrate: Callable[[], str] | None = None,
        new_section: Callable[[str], str] | None = None,
        dwell=None,
        badge_limit: int = 60,
        badge_timeout_ms: int = 10_000,
    ) -> None:
        self.bridge = bridge
        self.screen = screen
        self.gaze = gaze
        self._recalibrate = recalibrate
        self._new_section = new_section
        self.dwell = dwell
        self.badge_limit = badge_limit
        self.badge_timeout_ms = badge_timeout_ms

    def dispatch(self, command: Command, *, window_title: str = "") -> str:
        handler = getattr(self, f"_do_{command.name}", None)
        if handler is None:
            return f"unknown command: {command.argument or command.name}"
        try:
            return handler(command, window_title)
        except Exception as exc:  # noqa: BLE001 - a bad command never kills the daemon
            log.exception("command %s failed", command.name)
            return f"{command.name} failed: {exc}"

    # -- scrolling ------------------------------------------------------
    def _page(self, window_title: str):
        return self.bridge.active_page(window_title) if self.bridge is not None else None

    def scroll(self, amount: float, *, window_title: str = "") -> str:
        """Scroll the frontmost target. Public so dwell scrolling shares it."""
        return self._scroll(amount, window_title)

    def _scroll(self, amount: float, window_title: str) -> str:
        page = self._page(window_title)
        if page is not None:
            page.mouse.wheel(0, amount)
            return f"scrolled {amount:+.0f}"
        if self.screen is not None and hasattr(self.screen, "scroll"):
            self.screen.scroll(amount)
            return f"scrolled {amount:+.0f} (system)"
        return "no scrollable target"

    def _do_scroll_down(self, command: Command, window_title: str) -> str:
        return self._scroll(400, window_title)

    def _do_scroll_up(self, command: Command, window_title: str) -> str:
        return self._scroll(-400, window_title)

    def _do_page_down(self, command: Command, window_title: str) -> str:
        return self._scroll(900, window_title)

    def _do_page_up(self, command: Command, window_title: str) -> str:
        return self._scroll(-900, window_title)

    def _do_scroll_top(self, command: Command, window_title: str) -> str:
        page = self._page(window_title)
        if page is None:
            return "no page"
        page.evaluate("() => window.scrollTo({top: 0})")
        return "scrolled to top"

    def _do_scroll_bottom(self, command: Command, window_title: str) -> str:
        page = self._page(window_title)
        if page is None:
            return "no page"
        page.evaluate("() => window.scrollTo({top: document.body.scrollHeight})")
        return "scrolled to bottom"

    # -- clicking -------------------------------------------------------
    def _do_show_numbers(self, command: Command, window_title: str) -> str:
        page = self._page(window_title)
        if page is None:
            return "no page"
        count = page.evaluate(
            NUMBER_OVERLAY_SCRIPT,
            {"show": True, "limit": self.badge_limit, "timeoutMs": self.badge_timeout_ms},
        )
        return f"numbered {count} targets"

    def _do_hide_numbers(self, command: Command, window_title: str) -> str:
        page = self._page(window_title)
        if page is None:
            return "no page"
        page.evaluate(NUMBER_OVERLAY_SCRIPT, {"show": False, "limit": 0, "timeoutMs": 0})
        return "numbers hidden"

    def _do_click(self, command: Command, window_title: str) -> str:
        page = self._page(window_title)
        if page is None:
            return "no page"
        if command.number is None:
            return "no number heard"
        ok = page.evaluate(CLICK_BADGE_SCRIPT, command.number)
        return f"clicked {command.number}" if ok else f"no target numbered {command.number}"

    def _do_click_text(self, command: Command, window_title: str) -> str:
        page = self._page(window_title)
        if page is None:
            return "no page"
        locator = page.get_by_text(command.argument, exact=False).first
        locator.click(timeout=2000)
        return f"clicked {command.argument!r}"

    def _do_back(self, command: Command, window_title: str) -> str:
        page = self._page(window_title)
        if page is None:
            return "no page"
        page.go_back()
        return "went back"

    def _do_forward(self, command: Command, window_title: str) -> str:
        page = self._page(window_title)
        if page is None:
            return "no page"
        page.go_forward()
        return "went forward"

    # -- app ------------------------------------------------------------
    def _do_recalibrate(self, command: Command, window_title: str) -> str:
        if self._recalibrate is None:
            return "calibration not available"
        return self._recalibrate()

    def _do_new_section(self, command: Command, window_title: str) -> str:
        if self._new_section is None:
            return "notes not available"
        return self._new_section(command.argument)

    def _do_dwell_on(self, command: Command, window_title: str) -> str:
        if self.dwell is None:
            return "dwell scrolling unavailable"
        return self.dwell.set_enabled(True)

    def _do_dwell_off(self, command: Command, window_title: str) -> str:
        if self.dwell is None:
            return "dwell scrolling unavailable"
        return self.dwell.set_enabled(False)

    def _do_pause(self, command: Command, window_title: str) -> str:
        """Stop the camera. Nothing else pauses: notes are already opt-in."""
        if self.gaze is None:
            return "gaze engine unavailable"
        self.gaze.stop()
        return "gaze paused"

    def _do_resume(self, command: Command, window_title: str) -> str:
        if self.gaze is None:
            return "gaze engine unavailable"
        return self.gaze.start().reason

    def _do_unknown(self, command: Command, window_title: str) -> str:
        return f"did not understand {command.argument!r}"
