import json
import math

import pytest

from audit import canonicalize_for_hash


def test_key_order_irrelevant():
    a = {"z": 1, "a": 2, "m": 3}
    b = {"a": 2, "m": 3, "z": 1}
    assert canonicalize_for_hash(a) == canonicalize_for_hash(b)


def test_nested_dict_key_order_irrelevant():
    a = {"outer": {"z": 1, "a": {"y": 2, "x": 3}}, "list": [{"b": 1, "a": 2}]}
    b = {"list": [{"a": 2, "b": 1}], "outer": {"a": {"x": 3, "y": 2}, "z": 1}}
    assert canonicalize_for_hash(a) == canonicalize_for_hash(b)


def test_nested_list_order_is_significant():
    a = {"xs": [1, 2, 3]}
    b = {"xs": [3, 2, 1]}
    assert canonicalize_for_hash(a) != canonicalize_for_hash(b)


def test_output_is_bytes_with_no_incidental_whitespace():
    out = canonicalize_for_hash({"a": 1, "b": [1, 2]})
    assert isinstance(out, bytes)
    assert b" " not in out
    assert out == b'{"a":1,"b":[1,2]}'


def test_unicode_round_trips_and_is_stable():
    obj = {"label": "ééé café \U0001f9ec完成"}
    out1 = canonicalize_for_hash(obj)
    out2 = canonicalize_for_hash(dict(obj))
    assert out1 == out2
    # Decodes cleanly as UTF-8 and the text is recoverable.
    assert json.loads(out1.decode("utf-8"))["label"] == obj["label"]


def test_unicode_differs_from_ascii_escaped_equivalent_content():
    # Different Python source for the *same* string must canonicalize
    # identically regardless of how it's spelled in source.
    a = {"k": "café"}
    b = {"k": "café"}
    assert canonicalize_for_hash(a) == canonicalize_for_hash(b)


@pytest.mark.parametrize(
    "value",
    [1.0, -0.0, 1e-10, 0.1, -1.5, 3.14159265358979, 100.0, 1e100, 1e-300],
)
def test_float_edge_cases_are_deterministic(value):
    out1 = canonicalize_for_hash({"v": value})
    out2 = canonicalize_for_hash({"v": value})
    assert out1 == out2
    # The rendered float text matches Python's own repr() -- the spec's
    # "floats via repr" requirement.
    rendered = out1.decode("utf-8")
    assert repr(value) in rendered


def test_negative_zero_and_positive_zero_are_distinct():
    assert canonicalize_for_hash({"v": -0.0}) != canonicalize_for_hash({"v": 0.0})


def test_int_and_float_are_distinct():
    assert canonicalize_for_hash({"v": 1}) != canonicalize_for_hash({"v": 1.0})


def test_bool_and_int_are_distinct():
    assert canonicalize_for_hash({"v": True}) != canonicalize_for_hash({"v": 1})
    assert canonicalize_for_hash(True) == b"true"
    assert canonicalize_for_hash(False) == b"false"


def test_none_renders_as_json_null():
    assert canonicalize_for_hash(None) == b"null"
    assert canonicalize_for_hash({"v": None}) == b'{"v":null}'


def test_two_dicts_differing_only_by_whitespace_or_key_order_hash_equal():
    text_a = '{"a": 1,   "b":   {"c": 2, "d": 3}}'
    text_b = '{"b": {"d": 3, "c": 2}, "a": 1}'
    obj_a = json.loads(text_a)
    obj_b = json.loads(text_b)
    assert canonicalize_for_hash(obj_a) == canonicalize_for_hash(obj_b)


def test_non_finite_floats_are_rejected():
    with pytest.raises(ValueError):
        canonicalize_for_hash({"v": float("nan")})
    with pytest.raises(ValueError):
        canonicalize_for_hash({"v": float("inf")})
    with pytest.raises(ValueError):
        canonicalize_for_hash({"v": float("-inf")})


def test_tuples_canonicalize_like_lists():
    assert canonicalize_for_hash((1, 2, 3)) == canonicalize_for_hash([1, 2, 3])


def test_unsupported_type_is_rejected():
    with pytest.raises(TypeError):
        canonicalize_for_hash({"v", "is a set, not JSON-shaped"})
