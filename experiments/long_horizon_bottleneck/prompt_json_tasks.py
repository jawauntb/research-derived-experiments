"""Prompt JSON task helpers shared by Modal prompt-level sweeps."""

from __future__ import annotations

import math
import random
from typing import Any

from experiments.long_horizon_bottleneck.core import parse_prompt_json_action

SYSTEM_PROMPT = """You are a tool-planning model. Reply with exactly one JSON object and no prose.

Valid JSON actions:
{"tool":"read_slot","slot":"<exact slot phrase>","value":0}
{"tool":"read_slot","slot":"<exact slot phrase>","value":1}
{"tool":"noop"}

The slot field must be one of the allowed slot phrases named in the user prompt.
"""


def text_argument_phrase(slot: int, variant_index: int) -> str:
    ordinals = (
        "first",
        "second",
        "third",
        "fourth",
        "fifth",
        "sixth",
        "seventh",
        "eighth",
        "ninth",
        "tenth",
        "eleventh",
        "twelfth",
    )
    if variant_index == 0:
        return f"clue_{slot}"
    if variant_index == 1:
        ordinal = ordinals[slot] if slot < len(ordinals) else f"slot {slot}"
        return f"{ordinal} clue"
    if variant_index == 2:
        return f"memory slot {slot}"
    return f"slot {slot} phrase {variant_index}"


def slot_phrase(slot: int, variants_per_slot: int) -> str:
    return text_argument_phrase(slot, slot % variants_per_slot)


def mean(values: list[float]) -> float:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    return sum(finite) / len(finite) if finite else float("nan")


def episode_bits(rng: random.Random, n_slots: int) -> list[int]:
    return [rng.randrange(2) for _ in range(n_slots)]


def context_lines(bits: list[int], n_slots: int, slot_gap: int, variants_per_slot: int) -> list[str]:
    slot_lines = {slot_gap + slot * slot_gap: slot for slot in range(n_slots)}
    total_lines = slot_gap * (n_slots + 1)
    lines: list[str] = []
    for line_index in range(total_lines):
        if line_index in slot_lines:
            slot = slot_lines[line_index]
            lines.append(f"Memory record {line_index:02d}: {slot_phrase(slot, variants_per_slot)} = {bits[slot]}.")
        else:
            marker = (line_index * 37 + sum(bits) * 11) % 997
            lines.append(f"Trace filler {line_index:02d}: ignore marker {marker:03d}.")
    return lines


def bottleneck_user_prompt(
    bits: list[int],
    critical_slot: int,
    n_slots: int,
    slot_gap: int,
    variants_per_slot: int,
) -> str:
    phrase = slot_phrase(critical_slot, variants_per_slot)
    allowed = ", ".join(f'"{slot_phrase(slot, variants_per_slot)}"' for slot in range(n_slots))
    lines = context_lines(bits, n_slots, slot_gap, variants_per_slot)
    return "\n".join(
        [
            "Long-horizon moved-bottleneck task.",
            "Read the records, find the requested slot phrase, and emit one JSON action.",
            f"Allowed slot phrases: {allowed}.",
            *lines,
            f"Requested slot phrase: {phrase}",
            f"Emit the read_slot JSON for {phrase} with its recorded value.",
        ]
    )


def visible_user_prompt(bits: list[int], critical_slot: int, variants_per_slot: int) -> str:
    phrase = slot_phrase(critical_slot, variants_per_slot)
    value = bits[critical_slot]
    return "\n".join(
        [
            "Visible-control task.",
            f"The requested slot phrase is {phrase}, and the value is already visible: {value}.",
            "The environment already has the answer. Emit only the no-op JSON action.",
        ]
    )


def short_user_prompt(bits: list[int], critical_slot: int, variants_per_slot: int) -> str:
    phrase = slot_phrase(critical_slot, variants_per_slot)
    value = bits[critical_slot]
    return "\n".join(
        [
            f"Allowed slot phrases: \"{phrase}\".",
            f"Record: {phrase} = {value}.",
            f"Requested slot phrase: {phrase}.",
            f"Emit the read_slot JSON for {phrase} with its value.",
        ]
    )


def format_user_prompt() -> str:
    return "Format-control task. Emit exactly this action as JSON: {\"tool\":\"noop\"}"


def messages(user_prompt: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def repair_messages(user_prompt: str, assistant_text: str, failed: bool) -> list[dict[str, str]]:
    if failed:
        repair_text = (
            "Tool result: ERROR. The previous action failed before recording any value. "
            "Repair by emitting the same read_slot JSON action again."
        )
    else:
        repair_text = (
            "Tool result: SUCCESS. The value was recorded already. "
            "Emit only the no-op JSON action."
        )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
        {"role": "assistant", "content": assistant_text},
        {"role": "user", "content": repair_text},
    ]


def failure_flags(rng: random.Random, episodes: int, failure_probability: float) -> list[bool]:
    flags = [rng.random() < failure_probability for _ in range(episodes)]
    if 0.0 < failure_probability < 1.0 and episodes >= 2:
        if not any(flags):
            flags[0] = True
        if all(flags):
            flags[-1] = False
    return flags


def call_correct(parsed: dict[str, Any], critical_slot: int, value: int) -> bool:
    return (
        parsed["valid"]
        and parsed["opcode"] == "call"
        and parsed["slot"] == critical_slot
        and parsed["value"] == value
    )


def compact_parsed(parsed: dict[str, Any]) -> dict[str, Any]:
    return {
        "opcode": parsed["opcode"],
        "slot": parsed["slot"],
        "variant_index": parsed["variant_index"],
        "value": parsed["value"],
        "valid": parsed["valid"],
        "executable": parsed["executable"],
        "reason": parsed["reason"],
        "json_text": parsed["json_text"],
    }


def encode_messages(tokenizer: Any, message_list: list[dict[str, str]], device: Any) -> dict[str, Any]:
    import torch

    if getattr(tokenizer, "chat_template", None):
        input_ids = tokenizer.apply_chat_template(
            message_list,
            add_generation_prompt=True,
            return_tensors="pt",
        ).to(device)
        return {"input_ids": input_ids, "attention_mask": torch.ones_like(input_ids)}
    prompt = "\n\n".join(f"{message['role'].title()}: {message['content']}" for message in message_list)
    prompt += "\n\nAssistant:"
    encoded = tokenizer(prompt, return_tensors="pt")
    return {key: value.to(device) for key, value in encoded.items()}


def generate_action(
    model: Any,
    tokenizer: Any,
    message_list: list[dict[str, str]],
    max_new_tokens: int,
    n_slots: int,
    variants_per_slot: int,
) -> tuple[str, dict[str, Any]]:
    import torch

    encoded = encode_messages(tokenizer, message_list, model.device)
    with torch.inference_mode():
        output = model.generate(
            **encoded,
            do_sample=False,
            max_new_tokens=max_new_tokens,
            pad_token_id=tokenizer.eos_token_id,
        )
    generated = output[0, encoded["input_ids"].shape[-1] :]
    text = tokenizer.decode(generated, skip_special_tokens=True).strip()
    return text, parse_prompt_json_action(text, n_slots, variants_per_slot)
