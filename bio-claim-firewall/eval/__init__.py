"""Phase 5 mechanical-suite evaluation tools (`eval.mutation`, ...).

# PHASE5A-DECISION: the task's file list only calls for
# `eval/mutation/__init__.py`, but `python -m eval.mutation` needs `eval`
# itself to resolve as an importable package too. Python 3 would resolve
# `eval` as an implicit namespace package even without this file, but a
# real `__init__.py` is more robust (works the same whether `eval/` is on
# `sys.path` via cwd, PYTHONPATH, or a namespace-package edge case) and
# matches how every other top-level package in this repo (`src/rules`,
# `src/evidence`, ...) declares itself. So it's added here even though not
# explicitly listed.
"""

from __future__ import annotations
