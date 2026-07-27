# DCR3b counterfactual scoring prompt

Committed to disk before any subagent call. SHA-256 pinned in
`run_dcr3b.py`.

---

## Prompt

> You are a scientific-reasoning analyst. Below is a set of physics-related
> commitments extracted from an early-1900s electrodynamics corpus.
>
> For each commitment, produce a single integer score from 0 to 10 measuring
> **counterfactual dependence**: how many of the OTHER commitments in the
> set would become false, incoherent, or underdetermined if this one were
> false?
>
> Scoring rubric (fixed):
>
> - 0 — no other commitment depends on this one; removing it changes nothing
>   in the rest of the set.
> - 1-2 — one or two closely-related commitments would be affected.
> - 3-5 — several commitments across different documents would need to be
>   revised or would lose their meaning.
> - 6-8 — many commitments explicitly or implicitly rely on this one; its
>   removal would cascade through much of the set's reasoning.
> - 9-10 — the commitment is a pervasive background presupposition;
>   removing it invalidates whole classes of arguments across the set.
>
> Judge each commitment on how the OTHER commitments in the set would be
> affected — not on how well-known or historically important the commitment
> is in physics generally. Consider both explicit derivations and implicit
> presuppositions.
>
> Read the propositions carefully. For each `id` in the input, produce a
> score. Return a JSON object mapping `id` to integer score.
>
> Read ONLY the input file named in your instructions. Do not read, list,
> search, or open any other file. Do not explore the repository. Do not use
> any tool except the one that reads the input and writes your output.
>
> Return your output as JSON with shape:
>
>     {"kind": "dcr3b_counterfactual_scores", "cut_year": <int>,
>      "verifier_id": "<A/B/C>",
>      "scores": {"<id>": <int>, ...},
>      "reasoning": {"<id>": "<one-sentence justification>", ...}}
>
> to the exact output path in your instructions.
>
> Reply with only the number of scored propositions.
