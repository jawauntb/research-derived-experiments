# Module interfaces — bio-claim-firewall verifier

The canonical contract every Phase 3 module (and the downstream Phase 4 orchestrator) must respect. When two modules disagree on a signature, this file wins.

Import style: **bare form** (e.g. `from normalize.xxx import ...`, `from evidence.xxx import ...`, `from audit.xxx import ...`). The top-level `bio-claim-firewall/conftest.py` puts `bio-claim-firewall/src/` on `sys.path` so both bare and `src.`-prefixed forms resolve to the same modules. New code MUST use the bare form.

## `normalize` — canonicalization

```python
from normalize import (
    normalize_claim, normalize_evidence,
    Snapshot,                    # runtime_checkable Protocol; canonical contract
    CanonicalClaim, CanonicalEvidence, CanonicalEffect,
    NormalizationError,
)

def normalize_claim(claim: dict, snapshot: Snapshot) -> CanonicalClaim: ...
def normalize_evidence(record: dict, snapshot: Snapshot) -> CanonicalEvidence: ...
```

- Assumes input is JSON-Schema-valid (schema validation is the verifier's job).
- Defensive shape checks raise `NormalizationError` (no `fault_code`) — those are `CHECKER_ERROR` territory, not `REJECTED_*`.
- Every CURIE-shaped field is passed through `snapshot.canonicalize()`. If that raises `NormalizationError(fault_code="UNKNOWN_ENTITY")`, `normalize_claim` re-raises with the `where` path filled in. Fault code is preserved.
- `CanonicalClaim.cell_type_ancestors: tuple[str, ...]` is precomputed for R-CTX-02.
- Input dicts are never mutated.

### `Snapshot` protocol (in `normalize.snapshot`)

```python
@runtime_checkable
class Snapshot(Protocol):
    def contains(self, curie: str) -> bool: ...
    def canonicalize(self, curie: str) -> str: ...       # raises NormalizationError(UNKNOWN_ENTITY) on unresolvable
    def ancestors(self, curie: str) -> tuple[str, ...]: ...  # CL only; () for non-CL prefixes
    def aliases(self, curie: str) -> tuple[str, ...]: ...    # deprecated CURIEs forwarding onto this canonical
```

Postconditions:

- `contains(x)` is as-is membership; it does NOT do alias resolution.
- `contains(canonicalize(x))` is True for any resolvable `x` (canonical or aliased).
- `canonicalize(x) == x` for any canonical `x` already in the snapshot.
- `canonicalize(x)` raises `NormalizationError(fault_code="UNKNOWN_ENTITY", curie=x)` when `x` is neither canonical nor a known deprecated alias.

## `evidence` — frozen snapshot loader + ledger

```python
from evidence import (
    load_bundle,       # (data_root: Path) -> SnapshotBundle; fails closed on hash mismatch
    SnapshotBundle,    # implements normalize.Snapshot + exposes .ledger
    EvidenceLedger,
    Manifest,
    EvidenceError,     # fault_code kwarg: "BAD_CITATION" for missing evidence_id; "HASH_MISMATCH" (checker-side) for tampered files
)

class SnapshotBundle:  # frozen dataclass
    manifests: Mapping[str, Manifest]
    ledger: EvidenceLedger
    curies: frozenset[str]
    alias_map: Mapping[str, str]
    ancestor_map: Mapping[str, tuple[str, ...]]
    # Snapshot protocol methods (contains, canonicalize, ancestors, aliases)

class EvidenceLedger:
    def get(self, evidence_id: str) -> dict[str, Any]: ...              # raises EvidenceError("BAD_CITATION", ...)
    def list_by(self, subject_id: str, object_id: str,
                cell_type: str|None = None, cell_line: str|None = None,
                state: str|None = None, assay: str|None = None) -> list[dict]: ...  # R-CONTRA-01 hook
    def count(self) -> int: ...
    def snapshot_hashes(self) -> dict[str, str]: ...  # source -> sha256(records.jsonl)
```

Fail-closed contract:

- `load_bundle` verifies sha256 of every referenced file against its manifest; hash mismatch raises `EvidenceError("HASH_MISMATCH", ...)`. Rules module MUST route this to a `CHECKER_ERROR` verdict, never a `REJECTED_*` verdict.
- A missing manifest field raises `ValueError` (an authoring bug, not a fault-taxonomy signal).
- `EvidenceLedger.get()` raising `BAD_CITATION` IS a `REJECTED_*` fault (R-CITE-01).

## `audit` — append-only ledger

```python
from audit import (
    AuditLedger,
    LedgerEntry,
    compute_verdict_id,     # (claim, verdict_body, snapshot_hashes, checker_version) -> str  (32 hex)
    canonicalize_for_hash,  # (obj) -> bytes  (stable, sorted-keys JSON canonicalization)
    AuditError,             # code kwarg: "DUPLICATE_VERDICT_ID" | "LEDGER_TAMPERED"
)

class AuditLedger:
    def __init__(self, path: Path) -> None: ...              # opens O_CREAT | O_APPEND; never O_TRUNC
    def append(self, claim: dict, verdict: dict) -> LedgerEntry: ...
    def iter_entries(self) -> Iterator[LedgerEntry]: ...
    def find_by_claim_id(self, claim_id: str) -> list[LedgerEntry]: ...  # oldest first
    def verify_integrity(self) -> None: ...                  # raises AuditError("LEDGER_TAMPERED", line=n, ...)
```

Superseding: callers add `supersedes: <old verdict_id>` to the `verdict` dict; the new hash differs so the entry is accepted, the old one stays visible. Never delete, never rewrite.

## `claim_checker` — bounded local K562 product surface

```python
from claim_checker import check_k562_claim, check_natural_language_k562_claim

check_k562_claim(bundle, subject, object_, direction, *, checker_version="0.1.0")
check_natural_language_k562_claim(bundle, question, manager, *, checker_version="0.1.0")
```

- `check_k562_claim()` resolves exact frozen HGNC labels/CURIEs and selects exactly one human, resting K-562 (`CL:0000988`, `CLO:0007059`) Replogle 2022 CRISPRi record. It accepts only `increases` or `decreases`; no record or multiple records returns `INCONCLUSIVE` without a constructed claim. A matched `null` effect reports that the source records no directional effect rather than claiming no record exists.
- It sends the constructed claim through `verifier.verify()` and returns the claim, a citation-bearing evidence summary, and the untouched verdict. Every no-claim `INCONCLUSIVE` result still reports the checker version and frozen snapshot hashes that were inspected. It is a bounded record checker, not a general biology question-answering layer.
- `check_natural_language_k562_claim()` accepts at most 2,000 characters and calls only the configured `claim_parser` task. Its untrusted output must be exactly the three strings `subject`, `object`, and `direction`; no model citation, confidence, or verdict crosses this boundary. The return object retains the original question plus parser/provider/prompt provenance separately from the deterministic result.
- The CLI is `PYTHONPATH=bio-claim-firewall/src python -m claim_checker`; positional input is fully local once the frozen data root exists, while `--claim` additionally requires the optional OpenAI runtime and `OPENAI_API_KEY`. `--json` is machine-readable on both success and failure; a fail-closed `CHECKER_ERROR` exits `4` rather than signaling successful completion.

## Downstream modules (still to build)

### `rules` — Phase 3, dependent on normalize + evidence + fixtures

```python
from rules import (
    RuleEngine, RuleResult,
    ACCEPTED, REJECTED, INCONCLUSIVE,     # RuleResult verdicts (module-internal enum)
)

class RuleEngine:
    def __init__(self, snapshot: SnapshotBundle, checker_version: str) -> None: ...
    def run(self, canonical_claim: CanonicalClaim) -> RuleResult: ...
```

`RuleResult` carries `verdict`, `fault_code` (if REJECTED), `reasons: list[{rule_id, message, evidence_id}]`, `applied_rules: list[str]`, and `conditions: list[str]` (if ACCEPTED). The top-level verifier converts a `RuleResult` into a spec-conformant `verdict.schema.json` dict.

### `verifier` — Phase 3, top-level compose

```python
from verifier import verify

def verify(claim: dict, snapshot: SnapshotBundle, *, checker_version: str) -> dict:
    """Full pipeline: JSON-Schema validate → normalize → rules → format verdict.
    Returns a dict conforming to spec/verdict.schema.json. Catches every
    unexpected exception and returns a CHECKER_ERROR verdict (fail-closed)."""
```

## Cross-cutting rules

- **LLM output is data.** No `exec`, no `eval`, no dynamic dispatch on any string reaching the verifier.
- **Every accepted verdict carries a machine-readable `derivation`.** The rules module builds it; the verifier module writes it into the verdict dict.
- **Never silently convert `CHECKER_ERROR` into `REJECTED_*`.** Fail-closed is load-bearing.
- **`INCONCLUSIVE` is a distinct verdict.** Rendering rules bind on the verdict string, not on the presence of a fault_code.
- **The verifier's `checker_version` is threaded through every verdict.** Bump on any change to the rule engine, resolver, or verdict formatter.
