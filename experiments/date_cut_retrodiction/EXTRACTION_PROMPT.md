# The extraction prompt, verbatim and fixed

This is the exact instruction given to every extraction agent, identical for all
fifteen documents. It is recorded here because the extractor is the part of this
experiment most likely to be leaking, and a prompt that varied by document —
or that mentioned the research question — would make the placebo cuts
meaningless.

Three properties are load-bearing:

1. **Cut-blind.** Extraction runs *per document*, never per cut. The agent is
   never told the year, never told which cut its document belongs to, and never
   sees another document. Cuts are composed afterwards from per-document
   outputs. So the extractor cannot tailor its output to a cut, and any leakage
   it introduces is introduced *equally at all three cuts* — which is exactly
   what the placebo design needs in order to detect it.
2. **Anti-salience.** The instruction demands exhaustive, boring enumeration and
   explicitly names a short interesting list as a failure. An extractor invited
   to surface "the important commitments" would surface the ones history made
   important.
3. **Vocabulary-closed.** Statements may use only words the document itself
   uses. This makes the residue audit in `residue.py` a real check rather than a
   formality.

The quote requirement is verified mechanically afterwards by
`verify_extraction.py` — no agent is trusted to have copied accurately.

---

## Prompt

> You are extracting explicit commitments from a scientific text.
>
> Read the file at `{PATH}`. It is a plain-text scientific document.
>
> Enumerate EVERY substantive commitment the text makes or presupposes about the
> physical world. A commitment is a claim that could in principle be denied by a
> different theory.
>
> Be exhaustive and mechanical. Work through the document in order and record
> every commitment you encounter, including ones that seem obvious, trivial, or
> universally accepted. Do NOT select for importance, novelty, or interest. A
> complete boring list is the goal; a short interesting list is a failure.
>
> For each commitment, output an object with these fields:
>
> - `name` — snake_case identifier, at most five words
> - `statement` — one sentence stating the commitment, using only vocabulary that
>   appears in the document
> - `quote` — a VERBATIM contiguous span of 10 to 40 words, copied exactly from
>   the document, that states or presupposes the commitment
> - `kind` — `"asserted"` if the text states it, `"presupposed"` if the text
>   relies on it without stating it
> - `definitional` — `true` if denying it would make the document's own terms
>   meaningless; `false` if it is a contingent claim about the world
>
> Rules:
>
> - The `quote` must appear character-for-character in the file. Do not
>   paraphrase, normalise, modernise, or correct spelling. Copy it.
> - `statement` may use only words that appear in the document. If you need a
>   word the document does not contain, you may not use it.
> - Do not speculate about what later work did with these ideas. Do not name any
>   author, theory, experiment, or technical term that is not present in the
>   document.
> - Aim for 15 to 40 commitments. Fewer is acceptable for a short document.
>
> Write JSON to `{OUTPATH}` with shape
> `{"doc_id": "...", "propositions": [ ... ]}`.
>
> Reply with only the number of propositions written.

---

## Amendment: pass 2, the sandboxed prompt

Pass 1 ran the prompt above. One agent — the one handling
`poincare_1904_stlouis`, the single most consequential document, since it
carries every sentinel term at the target cut — reported that it had validated
its own output using this repository's `residue.py`.

That is a blinding breach. `residue.py`'s docstring names the 1905 cut, names
Einstein, and explains what the experiment is looking for. Nothing in the pass-1
prompt forbade reading it; the agent simply had filesystem access and used it.
Other pass-1 agents may have done the same without saying so, and there is no
way to establish from the outputs alone which did.

Pass 1 is therefore **not** a blind extraction and cannot be the record. It is
kept, because discarding it would throw away the more interesting measurement:
comparing the two passes shows how much the breach actually mattered, which is
a quantity worth having rather than a footnote to apologise for.

Pass 2 adds one paragraph and changes nothing else:

> Read ONLY the file named above. Do not read, list, search, glob, or open any
> other file. Do not explore the repository, do not run scripts, and do not use
> any tool except the one that reads that single file and the one that writes
> your output. If you are tempted to check your work against something else in
> the repository, do not — that would invalidate the extraction.

Pass 2 writes to `extractions_blind/`. **DCR1's gates are evaluated on pass 2.**
Pass 1 is reported alongside as the unblinded comparison.
