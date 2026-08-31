"""The top-level composer of the bio-claim-firewall verifier.

This is the only entry point external callers use. `verify()` fails closed
on every unexpected exception and never returns a verdict that violates
spec/verdict.schema.json. See src/INTERFACES.md's `verifier` contract.
"""

from .config import VerifierConfig
from .errors import VerifierError
from .verify import verify

__all__ = ["verify", "VerifierConfig", "VerifierError"]
