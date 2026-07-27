# The presupposition-inferring extraction prompt, verbatim and fixed

This is the exact instruction given to every DCR1e extraction agent, identical
for all sixteen documents (fifteen DCR1c documents plus Newton). It differs
from `EXTRACTION_PROMPT.md` in one specific and load-bearing way: it asks the
extractor to reverse-engineer commitments from the text's *arguments* rather
than to enumerate commitments the text *states*.

Four properties are load-bearing:

1. **Cut-blind and document-local.** As in DCR1c, extraction runs per
   document, the agent is never told the year or cut, and never sees another
   document. Any leakage introduced by the presupposition-hunting hint is
   introduced equally at all cuts — which is exactly what makes the 1880
   placebo a valid detector of it.
2. **Multi-facet hints.** The prompt names four *classes* of commitment to
   look at (time, space, measurement combination, coordinates). Pointing the
   extractor at one facet would be a candidate-selection leak. Pointing it at
   four keeps the answer under-determined and lets the corpus decide which
   ones surface.
3. **Vocabulary-closed.** Statements may only use words that appear in the
   document. The residue audit is the check.
4. **No forward-projection field.** DCR1c's schema included `kind: presupposed`;
   DCR1e's schema adds `required_by_argument` but deliberately does **not**
   ask for a `deniable_by` field. A "what would a different theory say"
   field is exactly where an LLM would leak modern knowledge into the
   extraction. Matching runs on `name` and `statement` only, so the field
   would be unnecessary anyway.

The quote requirement is verified mechanically by the existing
`verify_quotes` — no agent is trusted to have copied accurately.

---

## Prompt

> You are identifying COMMITMENTS a scientific text REQUIRES to be true —
> including commitments the text does not state.
>
> Read the file at `{PATH}`. It is a plain-text scientific document.
>
> Read ONLY the file named above. Do not read, list, search, glob, or open any
> other file. Do not explore the repository, do not run scripts, and do not use
> any tool except the one that reads that single file and the one that writes
> your output. If you are tempted to check your work against something else in
> the repository, do not — that would invalidate the extraction.
>
> Your task is different from a normal reading task. You are trying to
> identify commitments the text's REASONING requires, not commitments the
> text asserts. A commitment is a claim about the physical world that a
> different theory could deny.
>
> Read the text argument by argument. For each substantive argument or
> experimental setup, ask three questions:
>
> 1. What is the argument concluding, or what quantity is the setup measuring?
> 2. What steps does it use to reach that conclusion or to interpret that
>    measurement?
> 3. What would have to be true about the physical world for each step to be
>    valid?
>
> The commitments produced by (3) include some the text states and some the
> text takes for granted so completely that it does not state them.
> Enumerate BOTH kinds. A commitment can be load-bearing evidence for the
> framework even when the text never explicitly names it.
>
> Pay particular attention to four classes of commitment. They are named
> here to indicate the *kind* of thing you should be looking for, not what
> the answer is. Some documents will require commitments in only one or two
> of these classes; some will require none of them.
>
> - **Time and simultaneity.** If the argument talks about "the time" some
>   process takes, ask: is this time well-defined for all observers? What
>   would it mean for two observers moving relative to each other?
> - **Space and rest.** If the argument talks about a body being at rest or
>   in motion, ask: at rest relative to what? Does the framework assume
>   there is a definite fact of the matter?
> - **Measurement combination.** If the argument adds, subtracts, or
>   compares quantities from different measurements, ask: what makes those
>   quantities combinable in that way?
> - **Coordinate choice.** If the argument uses coordinates, ask: what does
>   the choice of coordinate system presuppose?
>
> For each commitment, output an object with these fields:
>
> - `name` — snake_case identifier, at most five words
> - `statement` — one sentence stating the commitment, using only vocabulary
>   that appears in the document
> - `quote` — a VERBATIM contiguous span of 10 to 40 words, copied exactly
>   from the document. The quote should be the sentence whose interpretation
>   USES or DEPENDS ON the commitment. It does not need to state the
>   commitment; it needs to be the sentence whose meaning requires it.
> - `kind` — `"asserted"` if the text states the commitment, `"presupposed"`
>   if the text uses it without stating it, `"required_by_argument"` if the
>   commitment is a necessary premise for an argument the text makes.
> - `definitional` — `true` if denying the commitment would make the
>   document's own terms meaningless; `false` if it is a contingent claim
>   about the world.
>
> Rules:
>
> - The `quote` must appear character-for-character in the file. Do not
>   paraphrase, normalise, modernise, or correct spelling. Copy it.
> - `statement` may use only words that appear in the document. If you need
>   a word the document does not contain, you may not use it.
> - Do not speculate about what later work did with these ideas. Do not name
>   any author, theory, experiment, or technical term that is not present in
>   the document.
> - Aim for 15 to 40 commitments. A short list containing only stated
>   commitments is a failure of this task — you should also be surfacing
>   presuppositions.
>
> Write JSON to `{OUTPATH}` with shape
> `{"doc_id": "...", "propositions": [ ... ]}`.
>
> Reply with only the number of propositions written.
