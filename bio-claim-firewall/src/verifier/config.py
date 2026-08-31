"""VerifierConfig: the frozen configuration bundle threaded through `verify()`.

Not part of the fail-closed runtime contract itself -- constructing a bad
`VerifierConfig` (a non-semver `checker_version`) is a caller/programmer
error that fails loudly at construction time, before any claim is ever
verified. `verify()`'s "never raises" guarantee is about the verification
*call*, not about misusing this dataclass's constructor.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from audit import AuditLedger

# Default location of claim.schema.json: `bio-claim-firewall/spec/`, resolved
# relative to this file (`bio-claim-firewall/src/verifier/config.py`) so it
# doesn't depend on the caller's current working directory.
_DEFAULT_SCHEMA_DIR = Path(__file__).resolve().parents[2] / "spec"

_SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


@dataclass(frozen=True, slots=True)
class VerifierConfig:
    """Configuration for one `verify()` pipeline.

    Attributes:
        checker_version: semver of the verifier binary (e.g. "0.1.0"),
            threaded into every verdict per spec/verdict.schema.json.
        schema_dir: directory containing `claim.schema.json`. Defaults to
            `bio-claim-firewall/spec/`.
        audit_ledger: if given, every verdict `verify()` produces is
            durably appended here before being returned. `None` (the
            default) means "no ledger" -- `verify()` still runs the full
            pipeline and returns a verdict, it just isn't recorded
            anywhere.
    """

    checker_version: str
    schema_dir: Path = field(default_factory=lambda: _DEFAULT_SCHEMA_DIR)
    audit_ledger: AuditLedger | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.checker_version, str) or not _SEMVER_RE.match(
            self.checker_version
        ):
            raise ValueError(
                "VerifierConfig.checker_version must be a semver string like "
                f"'0.1.0', got {self.checker_version!r}"
            )
        if not isinstance(self.schema_dir, Path):
            # CONFIG-DECISION: accept any os.PathLike/str for convenience
            # (e.g. a caller passing a plain string), coerced once here so
            # every downstream read (`schema.load_claim_schema`) can rely
            # on `Path` methods without its own defensive check.
            object.__setattr__(self, "schema_dir", Path(self.schema_dir))
