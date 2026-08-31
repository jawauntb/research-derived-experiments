import ast
import inspect
from pathlib import Path

from audit import AuditLedger
from audit import ledger as ledger_module


def _claim(claim_id="11111111-1111-4111-8111-111111111111"):
    return {"claim_id": claim_id, "subject": {"id": "HGNC:1097", "label": "BRCA1"}}


def _verdict(**overrides):
    body = {
        "verdict": "ACCEPTED_CONDITIONALLY",
        "snapshot_hashes": {"ontology": "a" * 64},
        "checker_version": "0.1.0",
    }
    body.update(overrides)
    return body


def test_source_never_truncates_the_ledger_file():
    # Walk the actual parsed AST (not raw source text, which also contains
    # comments/docstrings *about* not truncating) for any truncating file
    # open: os.open(..., flags) where flags reference O_TRUNC, a bare
    # open(..., "w"/"w+"/"x") stdlib call, or a call to .truncate(...).
    source = inspect.getsource(ledger_module)
    tree = ast.parse(source)

    def flags_mention_o_trunc(node: ast.AST) -> bool:
        for sub in ast.walk(node):
            if isinstance(sub, ast.Attribute) and sub.attr == "O_TRUNC":
                return True
            if isinstance(sub, ast.Name) and sub.id == "O_TRUNC":
                return True
        return False

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        func_name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)

        if func_name == "truncate":
            raise AssertionError("found a call to .truncate(...) in ledger.py")

        if func_name == "open":
            for arg in list(node.args) + list(node.keywords):
                value = arg.value if isinstance(arg, ast.keyword) else arg
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    mode = value.value
                    assert "w" not in mode and "x" not in mode, (
                        f"open() called with truncating/exclusive-create mode {mode!r}"
                    )

        if func_name == "os.open" or (isinstance(func, ast.Attribute) and func.attr == "open"):
            for arg in node.args + [kw.value for kw in node.keywords]:
                assert not flags_mention_o_trunc(arg), "os.open(...) flags include O_TRUNC"


def test_ledger_class_exposes_no_delete_or_truncate_method():
    public_methods = {
        name
        for name, _ in inspect.getmembers(AuditLedger, predicate=inspect.isfunction)
        if not name.startswith("_")
    }
    forbidden = {"delete", "truncate", "remove", "clear", "rewrite", "edit", "update"}
    assert public_methods.isdisjoint(forbidden)
    assert public_methods == {"append", "iter_entries", "find_by_claim_id", "verify_integrity"}


def test_append_writes_exactly_one_line_ending_in_newline(tmp_path: Path):
    path = tmp_path / "ledger.jsonl"
    ledger = AuditLedger(path)
    ledger.append(_claim(), _verdict())

    raw = path.read_bytes()
    assert raw.endswith(b"\n")
    lines = raw.splitlines()
    assert len(lines) == 1
    # Exactly one newline byte total (single line, no embedded newline).
    assert raw.count(b"\n") == 1


def test_two_appends_produce_two_entries_in_order(tmp_path: Path):
    path = tmp_path / "ledger.jsonl"
    ledger = AuditLedger(path)
    entry_a = ledger.append(_claim("11111111-1111-4111-8111-111111111111"), _verdict(verdict="ACCEPTED_CONDITIONALLY"))
    entry_b = ledger.append(_claim("22222222-2222-4222-8222-222222222222"), _verdict(verdict="REJECTED", fault_code="BAD_CITATION"))

    entries = list(ledger.iter_entries())
    assert [e.verdict_id for e in entries] == [entry_a.verdict_id, entry_b.verdict_id]
    assert entries[0].claim_id == "11111111-1111-4111-8111-111111111111"
    assert entries[1].claim_id == "22222222-2222-4222-8222-222222222222"

    raw = path.read_bytes()
    assert raw.count(b"\n") == 2


def test_init_creates_missing_file_without_truncating_existing_one(tmp_path: Path):
    path = tmp_path / "ledger.jsonl"
    assert not path.exists()
    AuditLedger(path)
    assert path.exists()
    assert path.read_bytes() == b""

    # Re-opening an AuditLedger over a file that already has content must
    # not wipe it.
    ledger = AuditLedger(path)
    ledger.append(_claim(), _verdict())
    assert path.stat().st_size > 0

    AuditLedger(path)  # re-open
    assert path.stat().st_size > 0
    assert len(list(AuditLedger(path).iter_entries())) == 1
