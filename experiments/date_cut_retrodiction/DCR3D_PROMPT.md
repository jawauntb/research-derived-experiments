# DCR3d discussion-tagging prompt

Committed to disk before any subagent call. SHA-256 pinned in `run_dcr3d.py`.

---

## Prompt

> You are analyzing a corpus of pre-1905 electrodynamics propositions.
> Your task is to tag each proposition with which THEORETICAL
> COMMITMENTS it takes as its **subject** (rather than as background).
>
> Distinguish two ways a proposition can relate to a commitment C:
>
> - **USE**: the proposition invokes C as a background premise for
>   some other claim. C's truth is assumed; the proposition's main
>   content is something else that requires C to be true.
>   *Example:* "The interference shift is proportional to v²/c²" USES
>   the aether frame (T2) as background — the aether-wind concept
>   presupposes T2 — but the main content of the proposition is the
>   shift-magnitude claim, not T2 itself.
>
> - **DISCUSS**: the proposition takes C as its subject; it defines
>   C, asserts C, denies C, argues about which form C should take,
>   examines C's role, disputes C's correctness, or treats C itself
>   as an object of inquiry.
>   *Examples:*
>     - "The ether is at rest in some absolute frame" — DISCUSSES T2
>       (asserts a specific form of T2).
>     - "The measure of time is chosen for convenience of physical
>       laws, not because a natural common time exists" — DISCUSSES
>       T1 (argues about T1's status).
>     - "The transformed time variable t' may be called the local
>       time" — DISCUSSES T3 (defines T3).
>
> Read ONLY the input file named in your instructions. Do not read,
> list, search, or open any other file.
>
> For each proposition in the input, return:
>
>     {"discussed_categories": ["T1"|"T2"|"T3"|"OTHER" or empty]}
>
> Only tag T1/T2/T3 when the proposition is genuinely discussing that
> category as its subject. If the proposition merely uses the
> commitment as background (a premise for some other claim), do NOT
> tag. Multiple discussed categories per proposition are allowed but
> should be rare — a single proposition typically discusses at most
> one commitment as its subject.
>
> The three categories are:
> - **T1** — common time / simultaneity relation shared across
>   observers or events. Examples of discussing T1: asserting or
>   denying that time is common across observers; defining
>   simultaneity; examining the conventional vs objective status of
>   simultaneity.
> - **T2** — preferred rest frame / stationary aether / privileged
>   velocity zero. Examples of discussing T2: asserting the aether is
>   at rest; defining the aether frame; arguing about whether the
>   aether moves with or through matter; disputing which form of
>   aether-drag is correct.
> - **T3** — local time as a mathematical artifice or transformed
>   variable rather than physical time. Examples of discussing T3:
>   introducing local time as a mathematical device; defining the
>   transformed time variable.
>
> Return your output as JSON with shape:
>
>     {"kind": "dcr3d_discussion_tags", "cut_year": <int>,
>      "verifier_id": "<A/B/C>",
>      "per_proposition": {"<id>": {"discussed_categories": [...]}, ...}}
>
> to the exact output path in your instructions. Reply with only the
> number of propositions processed.
