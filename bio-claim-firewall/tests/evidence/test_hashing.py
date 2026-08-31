from __future__ import annotations

import hashlib

from src.evidence.hashing import sha256_bytes, sha256_dir, sha256_file


def test_sha256_bytes_matches_stdlib_hashlib():
    data = b"hello bio-claim-firewall"
    assert sha256_bytes(data) == hashlib.sha256(data).hexdigest()


def test_sha256_bytes_is_deterministic():
    data = b"deterministic payload"
    assert sha256_bytes(data) == sha256_bytes(data)


def test_sha256_bytes_differs_for_different_input():
    assert sha256_bytes(b"a") != sha256_bytes(b"b")


def test_sha256_file_matches_sha256_bytes_of_its_contents(tmp_path):
    data = b"file contents for hashing test\n" * 100
    path = tmp_path / "sample.bin"
    path.write_bytes(data)

    assert sha256_file(path) == sha256_bytes(data)


def test_sha256_dir_is_deterministic_and_changes_with_content(tmp_path):
    d = tmp_path / "onto"
    d.mkdir()
    (d / "a.txt").write_text("alpha")
    (d / "b.txt").write_text("beta")

    first = sha256_dir(d)
    second = sha256_dir(d)
    assert first == second

    (d / "b.txt").write_text("beta-modified")
    assert sha256_dir(d) != first


def test_sha256_dir_is_independent_of_filesystem_creation_order(tmp_path):
    d1 = tmp_path / "onto1"
    d1.mkdir()
    (d1 / "a.txt").write_text("alpha")
    (d1 / "b.txt").write_text("beta")

    d2 = tmp_path / "onto2"
    d2.mkdir()
    (d2 / "b.txt").write_text("beta")
    (d2 / "a.txt").write_text("alpha")

    assert sha256_dir(d1) == sha256_dir(d2)


def test_sha256_dir_changes_when_a_file_is_added(tmp_path):
    d = tmp_path / "onto"
    d.mkdir()
    (d / "a.txt").write_text("alpha")
    before = sha256_dir(d)

    (d / "c.txt").write_text("gamma")
    after = sha256_dir(d)

    assert before != after
