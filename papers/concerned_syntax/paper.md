# Constituency Tests for Concerned Representation in Minimal Agents

**Jawaun Brown**  
2026-06-16

## Abstract

Arc 1 of the maintained-concern program showed that a minimal homeostatic agent
can detect boundary staleness, allocate costly null probes, saturate after
identification, and re-engage after regime shifts. It also found a precise
ceiling: under a shared-head, null-only intervention regime, better probe
policy no longer closes role-specific mediated identifiability. This paper
opens Arc 2A by asking whether the next intervention problem is syntactic:
can a concerned agent discover which parts of a world belong together
causally?

We introduce the **Concerned Shape Grammar**, a symbolic benchmark inspired by
constituency tests from cognitive work on geometric shape syntax. A visible
six-part shape can have the same surface but different hidden parse trees.
Causal roles such as shield, poison, repair, core, food, and trap interact
only when they are bound inside the same constituent. The agent must decide
whether to pay for an intervention that reveals the parse, and it must avoid
probing low-concern ambiguity that does not affect viability.

In a 200-trial deterministic design pilot and a 5,000-trial Modal multi-seed
sweep, the `concerned_syntax` selector is the only selector that passes the
full gate. In the Modal sweep, it reaches high-concern parse accuracy 1.000,
action accuracy 1.000, high-concern probe rate 1.000, low-concern probe rate
0.000, and gate pass rate 1.000. Flat valence, compression-only parsing, and
null policies fail because they do not make constituency knowable. An
uncertainty-only selector recovers the parse but fails the no-restless-inquiry
gate by probing every low-concern ambiguity. The result is not a claim about
neural agents yet. It is an accepted Phase 2A benchmark surface: **reward is
not syntax, compression is not syntax, and uncertainty reduction is not
concerned inquiry.**

## 1. Why Arc 2A Exists

The Metric Stack of Concern ended with a positive mechanism and a ceiling. The
positive mechanism was a detect-allocate-saturate-re-engage cycle for
self/world attribution in minimal homeostatic agents. The ceiling was equally
important: under null-only intervention and shared mediated heads, the agent
could predict total world response while failing to identify role-specific
mediated components.

That ceiling has two sides. Arc 2B studies the body side: what architectures
can express the required distinctions? Arc 2A studies the intervention side:
what actions make the world's hidden grammar visible?

The motivation comes from a nearby but distinct empirical result. Revencu,
Pajot, and Dehaene (2026) argue that adult geometric-shape representations
show syntactic structure. Their key methodological move is not merely to show
that shape complexity predicts behavior. They replace compression proxies with
constituency tests: structural ambiguity, subtree facilitation, and syntactic
movement. They also report that current neural networks can partially solve
match/deviant tasks without showing the same syntactic effects.

This paper imports that methodological lesson into the concern program. The
claim is not that minimal agents have human visual syntax. The claim is that
the Metric Stack needs an analogous gate:

> Performance is not constituency. Compression is not constituency.
> Uncertainty reduction is not concerned inquiry.

## 2. Benchmark

Each trial has a six-part visible shape. The visible role sequence is fixed,
but two hidden parse trees can organize the same surface differently. A parse
is a pair of high-level constituents, each containing three leaves.

Examples of parse candidates:

```text
repeat_concat    = (0,1,2) | (3,4,5)
hooked_repeat    = (0,1,3) | (2,4,5)
alternating_bind = (0,2,4) | (1,3,5)
edge_core        = (0,4,5) | (1,2,3)
```

Causal roles interact only when they belong to the same constituent:

| Role pair | Causal rule |
|---|---|
| shield + poison | shield reduces poison damage only within a subtree |
| repair + core | repair reduces core damage only within a subtree |
| food + trap | trap contaminates food only within a subtree |
| signal + ornament | structural ambiguity with no viability consequence |

The low-concern case is essential. Without it, a generic uncertainty reducer
could look successful simply by probing every ambiguity.

## 3. Interventions

The intervention language contains five operations:

| Intervention | Purpose |
|---|---|
| `null` | no information, no cost |
| `pair_probe` | test whether the causal role pair is in the same subtree |
| `distractor_pair_probe` | matched non-informative pair probe |
| `high_constituent_move` | test which high-level group moves as a unit |
| `role_ablation` | observe the viability signature of the causal constituent |

The central selector, `concerned_syntax`, chooses an intervention by expected
parse information weighted by the viability gap, minus intervention cost. It
has a hard no-restless-inquiry threshold: if the parse gap is below 0.10, it
chooses `null`.

## 4. Selectors

| Selector | What it tests |
|---|---|
| `null_policy` | behavior without inquiry |
| `flat_valence` | roles without constituency |
| `compression_proxy` | shortest parse without intervention |
| `uncertainty_only` | information gain without concern |
| `concerned_syntax` | information gain gated by viability relevance |

This is the anti-cheat surface. A selector can be good at action while failing
parse. It can recover parse while probing too much. It can choose a compressed
parse while missing the causally relevant one.

## 5. Pilot Result

Local command:

```bash
python3 -m experiments.concerned_syntax.benchmark \
  --trials 200 --seed 20260616 \
  --out artifacts/concerned_syntax/pilot.json \
  --report experiments/concerned_syntax/results/pilot_2026_06_16.md
```

Summary:

| Selector | Parse high | Action | Subtree | High probe | Low probe | Mean regret | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| compression_proxy | 0.523 | 0.890 | 0.550 | 0.000 | 0.000 | 0.055 | fail |
| concerned_syntax | 1.000 | 1.000 | 0.805 | 1.000 | 0.000 | 0.001 | PASS |
| flat_valence | 0.000 | 0.920 | 0.540 | 0.000 | 0.000 | 0.074 | fail |
| null_policy | 0.523 | 0.890 | 0.550 | 0.000 | 0.000 | 0.055 | fail |
| uncertainty_only | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | fail |

The result has the desired diagnostic pattern:

1. `flat_valence` has high action accuracy but fails parse and subtree gates.
2. `compression_proxy` sometimes guesses the right parse, but does not
   intervene and fails the mechanistic gate.
3. `uncertainty_only` recovers parse perfectly but probes all low-concern
   ambiguity, failing no-restless-inquiry.
4. `concerned_syntax` probes every high-concern ambiguity, avoids low-concern
   probing, and preserves action.

## 6. Discovery-Regime Status

This is a regime transition relative to Arc 1. Arc 1 represented concern as
viability prediction, valence, self/world attribution, probe value, and
component identifiability. Arc 2A adds a new artifact type: **causal
constituency under concern**.

That makes the result discovery-leaning, but still benchmark-level. The pilot
does not show that a neural agent has learned syntax. It shows that the repo
now has a task surface on which syntax, compression, uncertainty, and concern
can dissociate.

## 7. Modal Multi-Seed Sweep

The multi-seed sweep was run remotely through Modal:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
  experiments/concerned_syntax/modal_concerned_syntax_sweep.py \
  --trials 1000
```

The sweep used five seeds and 1,000 shape trials per seed. Raw JSON remains
local under `artifacts/concerned_syntax/`; the public report is
`experiments/concerned_syntax/results/modal_sweep_2026_06_16.md`.

Summary:

| Selector | Parse high | Action | Subtree | High probe | Low probe | Mean regret | Gate pass rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| compression_proxy | 0.560 | 0.891 | 0.583 | 0.000 | 0.000 | 0.048 | 0.000 |
| concerned_syntax | 1.000 | 1.000 | 0.808 | 1.000 | 0.000 | 0.003 | 1.000 |
| flat_valence | 0.000 | 0.876 | 0.503 | 0.000 | 0.000 | 0.066 | 0.000 |
| null_policy | 0.560 | 0.891 | 0.583 | 0.000 | 0.000 | 0.048 | 0.000 |
| uncertainty_only | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 |

This replicates the design-pilot pattern across seeds. The key result is not
that `concerned_syntax` has the best reward; `uncertainty_only` has zero
regret too. The key result is that only concern-weighted syntax passes both
the positive inquiry gate and the no-restless-inquiry gate.

The next version should add learned agents:

- tree-structured model
- flat MLP baseline
- object-slot baseline
- learned intervention policy
- role/parse held-out generalization
- neural anti-cheat probes for parse, subtree, and intervention usefulness

## 8. Limitations

The current benchmark is symbolic. It does not test pixels, learned perception,
continuous control, or human subjects. The intervention language is provided,
not invented from raw motor primitives. The parser candidates are small and
known to the evaluator. The point of this first paper is to define the
acceptance surface before larger compute.

The most important limitation is also the next step: the agent should learn the
intervention language and parse representation, not merely select among
hand-defined probes.

## 9. Conclusion

Arc 2A inserts a new layer into the maintained-concern ladder:

```text
difference -> geometry -> syntax -> salience -> valence
          -> action -> attribution -> maintenance
```

The pilot supports a narrow methodological claim: concerned syntax needs its
own tests. Reward, compression, uncertainty, and action accuracy can all
dissociate from causal constituency. The next experiments can now ask whether
learned agents and evolved bodies pass those tests without cheating.

## References

Brehmer, J., De Haan, P., Lippe, P., & Cohen, T. (2022). Weakly supervised
causal representation learning. *Advances in Neural Information Processing
Systems*, 35.

Brown, J. (2026). *The Metric Stack of Concern: From Viability Prediction to
Maintained Self/World Boundaries in Minimal Agents*.

Cooper, P., & Velasquez, A. (2026). Active Causal Experimentalist (ACE):
Learning intervention strategies via direct preference optimization. arXiv:
2602.02451.

Revencu, B., Pajot, M., & Dehaene, S. (2026). Representations of geometric
shapes have syntactic structure. *Journal of Experimental Psychology:
General*, 155(4), 1081-1102. https://doi.org/10.1037/xge0001890

Scholkopf, B., Locatello, F., Bauer, S., Ke, N. R., Kalchbrenner, N., Goyal,
A., & Bengio, Y. (2021). Toward causal representation learning. *Proceedings
of the IEEE*, 109(5), 612-634.

Yang, J., Zhang, D., Song, X., Dai, Q., Liu, X., Chen, Y., Vashishtha, A.,
Shi, J., Tan, C., & Peng, H. (2026). CausaLab: A scalable environment for
interactive causal discovery toward AI scientists. arXiv:2605.26029.
