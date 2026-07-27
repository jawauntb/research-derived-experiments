# DCR3c inferred-required-assumption prompt

Committed to disk before any subagent call. SHA-256 pinned in `run_dcr3c.py`.

---

## Prompt

> You are analyzing a corpus of pre-1905 electrodynamics propositions.
> Your task is to identify EMPIRICAL PREDICTIONS the corpus makes
> about observable experimental outcomes, and for each such
> prediction, list the UNDERLYING COMMITMENTS the prediction requires
> to be a valid inference — whether or not those commitments are
> explicitly stated in the corpus.
>
> A "prediction" is a proposition that makes a specific empirical claim
> about what an observer would measure or observe under specified
> conditions (e.g., "the interference pattern will shift by δ if the
> apparatus is rotated," "the aether wind will produce a time delay of
> Δt for a round trip," "the observed refraction depends on the
> orbital velocity").
>
> A "commitment" is a background claim about the physical world that
> the prediction assumes without deriving.
>
> For each required commitment you identify, classify it into ONE of
> these categories:
>
> - **T1** — invokes a common time or simultaneity relation shared
>   across separated observers or events. Examples: "there is a
>   well-defined instant at which A and B are simultaneous for all
>   observers"; "the time required for light to travel between
>   spatially separated points is a definite observer-independent
>   quantity"; "an interval of time is the same for all observers."
> - **T2** — invokes a preferred rest frame, stationary aether, or
>   privileged velocity zero. Examples: "the aether is at rest in
>   some frame"; "there is a state of absolute motion"; "the fixed
>   aether frame is a physical entity."
> - **T3** — invokes local time as a mathematical artifice or
>   transformed variable rather than a physical time reading.
> - **OTHER** — any commitment that fits none of the above (e.g.,
>   electromagnetic principles, geometric optics, mechanical
>   properties of materials).
>
> Read ONLY the input file named in your instructions. Do not read,
> list, search, or open any other file.
>
> For each proposition in the input, return:
>
>     {"is_prediction": bool, "required_categories": ["T1"|"T2"|"T3"|"OTHER", ...]}
>
> Only include "T1", "T2", or "T3" categories when you can articulate
> the specific implicit commitment the prediction depends on. Do not
> tag a category defensively; if the prediction can go through
> without invoking (say) common simultaneity, do not tag "T1".
>
> Return your output as JSON with shape:
>
>     {"kind": "dcr3c_inferred_assumptions", "cut_year": <int>,
>      "verifier_id": "<A/B/C>",
>      "per_proposition": {"<id>": {"is_prediction": bool,
>                                   "required_categories": [...]}, ...}}
>
> to the exact output path in your instructions. Reply with only the
> number of propositions processed.
