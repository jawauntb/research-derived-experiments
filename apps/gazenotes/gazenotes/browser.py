"""Chrome enrichment over CDP: what text was actually under the gaze point.

Playwright attaches to the user's *own* Chrome (``--remote-debugging-port``),
so cookies and logins are already there. Pages are never navigated
programmatically except for explicit user commands.

The pure parts — text-fragment construction, page selection, the injected
JavaScript — are module-level functions so they can be tested without a
browser. :class:`ChromeBridge` is the only part that needs Playwright, and it
swallows every failure: enrichment is a bonus, never a precondition for a note.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any
from urllib.parse import quote

from .events import BrowserContext
from .geometry import Point, Rect, window_to_viewport

log = logging.getLogger(__name__)

__all__ = [
    "text_fragment_url",
    "pick_page_index",
    "EXTRACT_SCRIPT",
    "ChromeBridge",
    "browser_context_from_payload",
]

MIN_BLOCK_CHARS = 40
MAX_TEXT_CHARS = 2000

# Walks up from the gaze point to the nearest block that actually holds prose.
EXTRACT_SCRIPT = """
(point) => {
  const BLOCK = new Set(['P','LI','BLOCKQUOTE','PRE','H1','H2','H3','H4','H5','H6',
                         'TD','ARTICLE','SECTION','FIGCAPTION','DD','DT','DIV']);
  const cssPath = (el) => {
    const parts = [];
    while (el && el.nodeType === 1 && parts.length < 6) {
      let part = el.tagName.toLowerCase();
      if (el.id) { parts.unshift(part + '#' + el.id); break; }
      const parent = el.parentElement;
      if (parent) {
        const siblings = Array.from(parent.children).filter(c => c.tagName === el.tagName);
        if (siblings.length > 1) part += ':nth-of-type(' + (siblings.indexOf(el) + 1) + ')';
      }
      parts.unshift(part);
      el = el.parentElement;
    }
    return parts.join(' > ');
  };
  let el = document.elementFromPoint(point.x, point.y);
  if (!el) return null;
  let best = null;
  while (el && el !== document.body) {
    const text = (el.innerText || '').trim();
    if (text.length >= __MIN_CHARS__ && BLOCK.has(el.tagName)) { best = el; break; }
    el = el.parentElement;
  }
  if (!best) best = document.elementFromPoint(point.x, point.y);
  if (!best) return null;
  const rect = best.getBoundingClientRect();
  return {
    text: (best.innerText || '').trim().slice(0, __MAX_CHARS__),
    tag: best.tagName.toLowerCase(),
    selector: cssPath(best),
    url: location.href,
    title: document.title,
    scrollY: window.scrollY,
    bbox: {x: rect.x, y: rect.y, width: rect.width, height: rect.height},
    chromeHeight: window.outerHeight - window.innerHeight
  };
}
""".replace("__MIN_CHARS__", str(MIN_BLOCK_CHARS)).replace("__MAX_CHARS__", str(MAX_TEXT_CHARS))

CHROME_HEIGHT_SCRIPT = "() => ({chromeHeight: window.outerHeight - window.innerHeight, dpr: window.devicePixelRatio})"


def text_fragment_url(url: str, text: str, *, words: int = 8) -> str:
    """Append a ``#:~:text=`` fragment so the link reopens at the passage.

    Uses the first few words only: long fragments break on any whitespace or
    markup difference, and Chrome matches a short prefix reliably. Existing
    fragments are replaced, since ours is the more specific target.
    """
    if not url:
        return ""
    snippet = " ".join(text.split())[:400]
    tokens = snippet.split(" ")[:words]
    # Trailing punctuation is part of the rendered text but a common mismatch.
    while tokens and not re.search(r"\w", tokens[-1]):
        tokens.pop()
    if len(tokens) < 3:
        return url
    base = url.split("#", 1)[0]
    return f"{base}#:~:text={quote(' '.join(tokens), safe='')}"


def pick_page_index(titles: Sequence[str], window_title: str) -> int | None:
    """Choose the page matching the frontmost window title.

    macOS window titles are the page title, sometimes with a suffix such as
    " - Google Chrome" or an audio indicator. Exact match wins; then containment
    either way; then, if there is exactly one page, that page.
    """
    if not titles:
        return None
    cleaned = re.sub(r"\s+[-—]\s+Google Chrome.*$", "", window_title or "").strip()
    if cleaned:
        for index, title in enumerate(titles):
            if title.strip() == cleaned:
                return index
        for index, title in enumerate(titles):
            title = title.strip()
            if title and (title in cleaned or cleaned in title):
                return index
    return 0 if len(titles) == 1 else None


def browser_context_from_payload(payload: dict[str, Any] | None) -> BrowserContext | None:
    """Convert the injected script's return value into a typed context."""
    if not payload or not isinstance(payload, dict):
        return None
    text = str(payload.get("text") or "").strip()
    url = str(payload.get("url") or "")
    if not text and not url:
        return None
    bbox = payload.get("bbox") or {}
    return BrowserContext(
        url=url,
        title=str(payload.get("title") or ""),
        text=text,
        selector=str(payload.get("selector") or ""),
        scroll_y=float(payload.get("scrollY") or 0.0),
        fragment_url=text_fragment_url(url, text) if text else url,
        bbox=(
            float(bbox.get("x", 0.0)),
            float(bbox.get("y", 0.0)),
            float(bbox.get("width", 0.0)),
            float(bbox.get("height", 0.0)),
        )
        if bbox
        else None,
    )


class ChromeBridge:
    """Lazy, self-healing CDP connection to the user's Chrome.

    Every public method returns ``None`` on any failure and logs at debug
    level. A dead browser must never stall or fail a capture.
    """

    def __init__(self, cdp_url: str = "http://localhost:9222") -> None:
        self.cdp_url = cdp_url
        self._playwright = None
        self._browser = None

    # -- connection -----------------------------------------------------
    @property
    def connected(self) -> bool:
        return self._browser is not None and getattr(self._browser, "is_connected", lambda: True)()

    def connect(self) -> bool:
        """Connect if not already connected. Safe to call on every capture."""
        if self.connected:
            return True
        self.close()
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            log.debug("playwright not installed; Chrome enrichment disabled")
            return False
        try:
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.connect_over_cdp(self.cdp_url)
        except Exception as exc:  # noqa: BLE001 - any failure means "no browser"
            log.debug("CDP connect failed (%s): %s", self.cdp_url, exc)
            self.close()
            return False
        return True

    def close(self) -> None:
        for attr in ("_browser", "_playwright"):
            obj = getattr(self, attr, None)
            if obj is None:
                continue
            try:
                (obj.close if attr == "_browser" else obj.stop)()
            except Exception:  # noqa: BLE001
                pass
            setattr(self, attr, None)

    def pages(self) -> list:
        """Every open page across every context, or an empty list."""
        if not self.connect():
            return []
        try:
            return [page for ctx in self._browser.contexts for page in ctx.pages]
        except Exception as exc:  # noqa: BLE001
            log.debug("listing pages failed: %s", exc)
            return []

    def active_page(self, window_title: str = ""):
        """The page matching the frontmost Chrome window, or ``None``."""
        pages = [p for p in self.pages() if not p.is_closed()]
        if not pages:
            return None
        titles = []
        for page in pages:
            try:
                titles.append(page.title())
            except Exception:  # noqa: BLE001
                titles.append("")
        index = pick_page_index(titles, window_title)
        return pages[index] if index is not None else None

    def chrome_height(self, page) -> float | None:
        """Vertical browser chrome (tab strip + omnibox + bookmarks) in points."""
        try:
            return float(page.evaluate(CHROME_HEIGHT_SCRIPT)["chromeHeight"])
        except Exception as exc:  # noqa: BLE001
            log.debug("chrome height probe failed: %s", exc)
            return None

    # -- enrichment -----------------------------------------------------
    def extract_at(
        self,
        screen_point: Point,
        window: Rect,
        *,
        window_title: str = "",
    ) -> BrowserContext | None:
        """Text block under a *screen* point, or ``None``.

        The screen point is converted through the window origin and the
        measured chrome height; a point that lands in the browser chrome
        (negative viewport y) is rejected rather than snapped into the page.
        """
        page = self.active_page(window_title)
        if page is None:
            return None
        chrome = self.chrome_height(page)
        if chrome is None:
            return None
        viewport = window_to_viewport(screen_point, window, chrome)
        if viewport.x < 0 or viewport.y < 0:
            log.debug("gaze point is in browser chrome, not the page")
            return None
        try:
            payload = page.evaluate(EXTRACT_SCRIPT, {"x": viewport.x, "y": viewport.y})
        except Exception as exc:  # noqa: BLE001
            log.debug("DOM extraction failed: %s", exc)
            return None
        return browser_context_from_payload(payload)

    def screenshot_element(
        self,
        context: BrowserContext,
        destination: Path,
        *,
        margin: float = 12.0,
        window_title: str = "",
    ) -> Path | None:
        """Clip a screenshot to the matched block, with a little breathing room."""
        if context.bbox is None:
            return None
        page = self.active_page(window_title)
        if page is None:
            return None
        x, y, w, h = context.bbox
        if w <= 0 or h <= 0:
            return None
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            page.screenshot(
                path=str(destination),
                clip={
                    "x": max(0.0, x - margin),
                    "y": max(0.0, y - margin),
                    "width": w + 2 * margin,
                    "height": h + 2 * margin,
                },
            )
        except Exception as exc:  # noqa: BLE001
            log.debug("element screenshot failed: %s", exc)
            return None
        return destination if destination.exists() else None
