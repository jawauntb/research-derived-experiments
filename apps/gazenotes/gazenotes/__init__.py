"""gazenotes — hands-free, gaze-contextualised note capture for macOS.

The package is deliberately split into a **pure core** (no platform imports)
and thin **platform adapters** that import macOS/AI dependencies lazily:

pure core
    :mod:`gazenotes.config`, :mod:`gazenotes.geometry`, :mod:`gazenotes.events`,
    :mod:`gazenotes.notes`, :mod:`gazenotes.commands`, :mod:`gazenotes.nightly`,
    :mod:`gazenotes.gaze.model`, :mod:`gazenotes.gaze.regress`,
    :mod:`gazenotes.gaze.features`, and the pure helpers in
    :mod:`gazenotes.watcher` / :mod:`gazenotes.browser`.

platform adapters
    :mod:`gazenotes.screen` (Quartz), :mod:`gazenotes.gaze.capture`
    (OpenCV + MediaPipe), :mod:`gazenotes.browser` (Playwright/CDP),
    :mod:`gazenotes.menubar` (rumps).

Every adapter degrades to ``None``/inert behaviour when its dependency is
missing, so the core imports and the test suite run on any platform.
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["__version__"]
