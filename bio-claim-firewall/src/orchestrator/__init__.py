"""The propose -> verify -> repair -> re-verify loop.

`Orchestrator.run()` is the only entry point: given a question and the
evidence records available, it calls the configured `Proposer`, verifies
every emitted claim via `verifier.verify()`, attempts `Repairer.repair()`
on any `REJECTED` claim (capped at `config.max_repair_attempts`), and
returns an `OrchestratorResult`. See `orchestrator.py`'s module docstring
for the MIDAS adaptation this is based on and its PHASE4B-DECISIONs.
"""

from .errors import OrchestratorError
from .orchestrator import Orchestrator
from .types import OrchestratorConfig, OrchestratorResult

__all__ = ["Orchestrator", "OrchestratorConfig", "OrchestratorResult", "OrchestratorError"]
