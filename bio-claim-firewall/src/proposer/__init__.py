"""The untrusted claim proposer.

`Proposer.propose()` is the only entry point: it calls the configured
`ModelManager` task `"proposer"` and returns a contract-checked
`ClaimBundle` of plain `dict` claims (never a proposer-owned typed claim
class -- LLM output stays data all the way to `src/verifier`). See
`proposer.py`'s module docstring for the MIDAS adaptation this is based on
and the scope of the proposer-side contract check.
"""

from .errors import ProposerError
from .proposer import Proposer
from .types import ClaimBundle

__all__ = ["Proposer", "ClaimBundle", "ProposerError"]
