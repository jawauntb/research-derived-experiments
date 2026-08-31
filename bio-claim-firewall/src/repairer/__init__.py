"""The untrusted claim repairer.

`Repairer.repair()` is the only entry point: given one REJECTED claim, its
verdict, and the evidence records, it calls the configured `ModelManager`
task `"repairer"` and returns a `RepairResult` -- either a schema-shaped
repaired claim dict or an explicit abstain. See `repairer.py`'s module
docstring for the MIDAS adaptation this is based on.
"""

from .errors import RepairerError
from .repairer import Repairer
from .types import RepairResult

__all__ = ["Repairer", "RepairResult", "RepairerError"]
