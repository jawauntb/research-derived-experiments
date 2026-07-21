# Unified Citation-Grounded Review Superset

**Human research director.** Jawaun Brown.
**Compilation.** Codex, under human direction and review.

## Executive orientation

### Purpose

This document consolidates five citation-grounded review frameworks and nine underlying primary sources into one lossless review system. It is deliberately ordered in four dependent parts. Part I defines the modular master framework. Part II converts that framework into a formal knowledge ontology. Part III uses both to specify an executable AI reviewer. Part IV applies all three to a modular alpha-research operating system for equities, exchange-traded funds, and equity options.

The word "superset" has a strict meaning here. Repeated ideas are normalized into one canonical knowledge unit, but domain-specific assumptions, tests, and limits are retained as modules. The result is not a generic checklist and not an average of the source documents. It is the smallest unified system that preserves every material review capability found in the five frameworks.

### Source boundary and responsible use

The source frameworks reconstruct methodological commitments from selected publications. They do not simulate the named authors, establish their personal opinions, or transfer authority from an author to a review claim. The original publications are evidence for particular mathematical and empirical practices. Cross-document invariants are synthesis. Broader statistical, engineering, and deployment rules remain general practice unless directly grounded.

This document is a review instrument, not investment advice, clinical guidance, or a replacement for qualified domain experts. Its financial modules distinguish mathematical correctness from market adequacy and production readiness. Its geometry modules distinguish formal calculation from statistical application. Its learned-systems module does not establish expertise in causal inference, clinical trials, survey methods, or every branch of statistics.

### Evidence classes

| Tag | Meaning | Required handling |
|---|---|---|
| P | Directly supported by an original primary source | Cite the source key and page or slide range. |
| F | Directly stated in one of the five review frameworks | Cite the framework and framework page. |
| U | Unified inference supported across frameworks or sources | Name the supporting modules and state the inference. |
| G | General quantitative, statistical, software, or governance practice | Do not attribute it to a source author without separate evidence. |

Evidence class and correctness are separate. A P-tagged statement can still be false, limited, or misapplied. A G-tagged standard can be essential even though it is not present in the selected corpus.

### The consolidation thesis

Every reviewed claim traverses the same dependency chain:

`target object -> representation -> assumptions -> construction or model -> evidence -> stress tests -> calibrated decision`

A conclusion is only as reliable as the weakest required link. Downstream elegance cannot repair an upstream category error. A good fit cannot repair a wrong return series. A correct Fourier transform cannot repair a wrong stochastic generator. Correct coordinate algebra cannot repair a scientifically invalid compositional sample space. Low reconstruction error cannot establish stable latent geometry. A pointwise spectral identity cannot establish a global theorem whose hypotheses fail.

### Reading order

- Part I is the human-operable framework and should be read first.
- Part II is the formal vocabulary and relation system used to make the framework machine-checkable.
- Part III is the executable reviewer specification derived from Parts I and II.
- Part IV is the composable research and analysis system derived from Parts I through III.
- The appendices provide the source map, overlap crosswalk, resolved tension ledger, compact field protocol, and alpha-pipeline contracts.

[[PAGEBREAK]]

## Part I - Modular master framework

### 1. What is unified and what remains modular

The five frameworks share a review operating system: define the object, expose assumptions, derive the relevant structure, validate through independent tests, stress alternatives and transformations, and calibrate the final claim. They differ in the object that receives priority and in the earliest fatal gate.

The consolidated system therefore has four layers:

1. **Shared kernel.** Universal knowledge units and the eight-pass protocol used in every review.
2. **Domain modules.** Specialized objects, assumptions, tests, and stop conditions that must not be flattened into generic language.
3. **Bridge rules.** Rules for combining modules when a claim spans domains, such as an empirical market claim implemented with an affine stochastic model.
4. **Resolution layer.** A typed method for separating hard contradictions from scoped alternatives, procedural tensions, and source-level caveats.

The repeated handbook chassis in the five frameworks - scope notice, source map, methodological fingerprint, eight passes, severity labels, AI prompts, worksheets, and final standard - is treated as presentation overlap. The knowledge inside that chassis is consolidated only when the underlying proposition and function are the same.

### 2. Universal knowledge units

The following units form the unique shared kernel. Each appears substantively in at least two frameworks, and most appear in all five.

| ID | Canonical knowledge unit | Operational consequence |
|---|---|---|
| K01 | Define the target object before evaluating it. | Record the scientific object, mathematical object, decision, horizon, units, support, and boundary. |
| K02 | Separate the object from its representation. | Name coordinates, basis, transform, embedding, surrogate, return convention, or augmented state as a choice. |
| K03 | Make every claim path explicit. | Map evidence through intermediate quantities to the final conclusion. |
| K04 | Classify assumptions by role. | Distinguish definitions, theorem conditions, modeling conveniences, empirical regularities, identification assumptions, and computational approximations. |
| K05 | Derive structure from primitives. | Derive metrics from likelihoods, generators from SDEs, graph probabilities from model definitions, and conclusions from explicit estimands. |
| K06 | Verify domain and regularity. | Check support, positivity, differentiability, rank, identifiability, stationarity, boundary data, compactness, integrability, and existence. |
| K07 | Require a bridge for every reduction. | State when a surrogate, scalarization, transform, aggregation, or analogy preserves the natural object and when it fails. |
| K08 | Treat information loss as an auditable event. | Quantify what is discarded by coarse-graining, summary statistics, latent compression, model reduction, or omitted state. |
| K09 | Use independent checks. | Combine structurally different symbolic, empirical, asymptotic, dimensional, limiting, numerical, and simulation checks. |
| K10 | Compare simple and mechanism-relevant alternatives. | Include component, naive, prior-method, alternative-dynamics, coordinate, and metric baselines. |
| K11 | Stress scale, regime, and representation. | Vary horizons, samples, seeds, architectures, dimensions, distributions, bases, boundaries, calibration windows, and numerical settings. |
| K12 | Separate local from global validity. | Do not turn local geometry, finite-sample fit, pointwise identities, or in-sample evidence into global or deployment claims. |
| K13 | Separate validity layers. | Judge mathematical, numerical, empirical, interpretive, and operational validity independently. |
| K14 | Make negative and anomalous evidence visible. | Preserve failed correlations, unexpected spectra, missing eigenvalues, misfit regimes, and unresolved conditions. |
| K15 | Use decisive tests, not vague requests. | Attach the smallest proof, diagnostic, ablation, sensitivity analysis, or reproduction that could change the verdict. |
| K16 | Calibrate language to evidence. | Distinguish proved, demonstrated, associated, qualitatively consistent, suggestive, and unsupported. |
| K17 | Keep provenance typed. | Separate primary-source support, framework statements, unified inference, and general practice. |
| K18 | Use noncompensatory gates. | A fatal failure in a required upstream layer blocks acceptance regardless of strengths elsewhere. |

### 3. The unified eight-pass protocol

The pass numbers are canonical in the superset. Domain modules may expand a pass, but they do not reorder its logical dependencies.

| Pass | Review question | Required output | Typical stop condition |
|---|---|---|---|
| 0. Scope and provenance | What can this corpus and reviewer legitimately judge? | Scope statement, source list, missing expert lenses, evidence-label policy | Required expertise or evidence is absent and cannot be supplied. |
| 1. Target and decision | What exact object, estimand, price, prediction, distance, theorem, or deployment decision is at issue? | Claim map and decision statement | The target changes across the analysis or is undefined. |
| 2. Semantics and representation | What sample space, state, variable, coordinate, basis, transform, embedding, or surrogate represents the target? | Object card and representation ledger | The chosen representation changes the scientific object without acknowledgement. |
| 3. Assumptions and admissibility | Which conditions make the model, theorem, or inference valid? | Classified assumption ledger with testability and failure consequences | A necessary condition is false or unverifiable and the claim is not narrowed. |
| 4. Construction and derivation | Does the metric, operator, estimator, algorithm, approximation, or model follow correctly? | Derivation audit and reduction-bridge table | Algebra, generator, domain, rank, normalization, or theorem hypotheses fail. |
| 5. Evidence and independent verification | Do data, proofs, diagnostics, simulations, and numerical checks support the claimed mechanism? | Evidence-to-claim matrix and reproduction record | Evidence does not identify the claim or depends on leakage or invalid computation. |
| 6. Stress, alternatives, and information loss | What plausible change, alternative mechanism, scale, or reduction reverses the conclusion? | Ranked decisive-test plan and loss audit | A plausible alternative explains the evidence and is not discriminated. |
| 7. Calibration and decision | What survives, at which validity layer, and for which scope? | Severity-rated findings, contradiction ledger, calibrated claims, final decision | Final wording exceeds the strongest supported layer. |

The passes are both ordered and independently scored. They are ordered because later claims depend on earlier definitions and conditions. They are independently scored because a strong result in one dimension cannot compensate for failure in another. This resolves the apparent sequencing tension between the Financial Statistical Physics and Hydrodynamics frameworks.

### 4. Noncompensatory acceptance layers

| Layer | Core question | Pass condition | Example failure |
|---|---|---|---|
| Semantic validity | Is the right real-world or scientific object being analyzed? | Units, denominator, horizon, observational unit, payoff, or deployment target are stable and meaningful. | Treating absolute quantities as compositions or mixing adjusted and unadjusted prices. |
| Mathematical validity | Are definitions, derivations, domains, and theorem conditions correct? | The equations and formal claims hold under stated conditions. | Wrong generator sign, missing one-half factor, invalid compactness inference. |
| Numerical validity | Does the implementation realize the mathematics accurately? | Convergence, precision, branch, discretization, and benchmark checks pass. | A correct transform evaluated on the wrong branch or unstable grid. |
| Empirical validity | Does observed evidence support the intended explanation or prediction? | Design, uncertainty, baselines, diagnostics, and out-of-sample tests discriminate alternatives. | Histogram fit without a credible process or leaked backtest. |
| Interpretive validity | Does the meaning survive permitted re-expression? | Claims are invariant where invariance is required and representation-dependent where it is not. | Treating one circle immersion as the statistical family itself. |
| Operational validity | Is the result fit for the intended decision or deployment? | Costs, controls, monitoring, legal terms, failure handling, and external evidence are adequate. | Mathematically correct price with unsupported liquidity and execution assumptions. |

Acceptance at a later layer never implies acceptance at an earlier layer. Mathematical validity is necessary but not sufficient for empirical or operational claims. Empirical adequacy cannot validate an internally inconsistent density. Operational success during one regime does not prove the model.

### 5. Evidence, severity, confidence, and claim strength

Each finding is represented by four independent coordinates.

| Coordinate | Allowed values | Meaning |
|---|---|---|
| Provenance | P, F, U, G | Where the review principle or evidence comes from. |
| Severity | Fatal, major, moderate, minor, extension | How much the issue can change the central conclusion or readiness decision. |
| Confidence | High, medium, low | How directly the issue follows from available evidence. |
| Claim strength | Proved, demonstrated, associated, qualitatively consistent, suggestive, unsupported | What language the evidence permits. |

**Fatal** means the central conclusion is false, unidentified, or untestable under a plausible condition and cannot be repaired within the current design. **Major** means an important conclusion may change after a necessary proof repair, reanalysis, baseline, or experiment. **Moderate** means the main result may remain but interpretation, uncertainty, or generality is overstated. **Minor** means a local reporting or reproducibility defect is unlikely to alter the conclusion. **Extension** is valuable work beyond current validity requirements and must not be used to inflate severity.

Confidence is not severity. A low-confidence fatal concern should be framed as a decisive question. A high-confidence minor concern remains minor.

### 6. Domain module A - Learned systems, graphs, and transfer

This module preserves the distinctive knowledge from the five-paper Agarwala corpus.

| Field | Module requirement |
|---|---|
| Trigger | Learned representations, autoencoders, Jacobians, graph generators, finite MDP similarity, transfer learning, or model-internal geometry. |
| Primary objects | Input, latent, and reconstruction spaces; encoder and decoder maps; Jacobians and spectra; spatial graph positions, intensities, and connection probabilities; state and action similarity matrices. |
| Special assumptions | Eigenvector orthogonality, manifold behavior, initialization, independence, boundary correction, representation of unavailable actions, asymptotic random-matrix regime, train-test-deployment distinction. |
| Required comparisons | Natural versus surrogate Jacobian; composite versus component graph models; new method versus prior, uniform, and naive transfer; scalar task distance versus matrix-level structure. |
| Stress axes | Seed, epoch, architecture, latent dimension, input distribution, graph boundary, position distribution, task factor, and representation convention. |
| Decisive failures | Surrogate spectrum diverges from the natural object; a component baseline matches the composite; internal geometry is unstable while output metrics appear stable; scalar summary erases predictive state structure. |
| Scope limit | Does not establish a general theory of causal inference, clinical design, time-series econometrics, or all machine learning. |

Primary-source anchors include the use of model Jacobians to predict autoencoder error [A1 pp. 1-3], composite geometric Chung-Lu modeling and boundary correction [A2 pp. 1-5, 16-21], qualitative transfer from asymptotic random-matrix results [A3 pp. 2-8], architecture- and seed-dependent out-of-distribution geometry [A4 pp. 1-8], and the failure of scalar task distances to correlate with transfer despite useful state-level similarity [A5 pp. 1, 9-11].

### 7. Domain module B - Empirical financial statistical physics

This module begins with the observed market object rather than a preferred stochastic process.

| Field | Module requirement |
|---|---|
| Trigger | Market time series, returns, volatility, tails, risk measures, correlations, trading strategies, option assumptions, or empirical physics analogies. |
| Primary objects | Price definition, arithmetic or log return, sampling clock, horizon, volatility proxy, loss, option value, strategy P and L, and risk measure. |
| Special assumptions | Stationarity, increment independence, Markov or martingale behavior, continuity, Gaussianity, parameter constancy, market completeness, liquidity, continuous trading, no-arbitrage, and cost model. |
| Required diagnostics | Return construction, ACF, absolute- and squared-return dependence, variogram, spectrum, scale aggregation, distribution and tail checks, volatility clustering, regime and subperiod analysis. |
| Required alternatives | Random walk, Gaussian and heavy-tail families, historical simulation, naive volatility forecasts, alternative windows, null strategies, and simpler execution rules. |
| Decisive failures | Incorrect returns, look-ahead leakage, nonstationarity without treatment, omitted uncertainty, tail failure, unstable parameters, or profit erased by costs and delay. |
| Scope limit | The primary source is pedagogical and does not cover the full modern microstructure, causal, high-frequency, or institutional execution literature. |

Primary-source anchors include returns and dependence diagnostics [B1 pp. 6-10], stochastic and Markov process foundations [B1 pp. 11-17], Black-Scholes assumptions [B1 pp. 20-27], turbulence analogy [B1 pp. 40-41], risk limitations [B1 pp. 44-47], and ARCH/GARCH treatment [B1 pp. 48-50].

### 8. Domain module C - Affine stochastic operators and financial engineering

This module audits the mathematics and implementation of a stated stochastic process or pricing model.

| Field | Module requirement |
|---|---|
| Trigger | SDEs, jump-diffusions, forward or backward equations, affine processes, Kelvin waves, transition densities, Fourier pricing, stochastic volatility, path dependence, rates, or AMMs. |
| Primary objects | Complete Markov state, SDE, generator and adjoint, state domain, initial or terminal data, transform, Riccati or wave-vector ODEs, density, expectation, payoff, measure, and numeraire. |
| Special assumptions | Affine eligibility, covariance and jump conventions, killing, state constraints, moment and transform existence, branch continuity, integrability, discounting, and calibration stability. |
| Required checks | Term-by-term generator derivation; dimensions; positivity; normalization or survival mass; delta limit; moments and covariance; forward and backward PDE residuals; Chapman-Kolmogorov; limiting cases; numerical convergence; independent benchmark or Monte Carlo. |
| Required alternatives | Bachelier, Black-Scholes, stochastic-volatility, jump, path-dependent-volatility, and other dynamics appropriate to the product and horizon. |
| Decisive failures | Incomplete state, wrong sign or one-half factor, invalid transform domain, failed normalization or delta limit, branch instability, or payoff/discount mismatch. |
| Scope limit | Exact mathematics and numerical agreement do not establish empirical market adequacy or production readiness. |

Primary-source anchors include the affine Kelvin-wave program [C1 pp. 4-10, 29-40], correction and Monte Carlo verification of the Kolmogorov density [C1 pp. 16-25], augmentation for path dependence [C1 pp. 35-36, 72-80, 95-100], and financial applications [C1 pp. 85-114].

### 9. Domain module D - Statistical-manifold derivations

This module audits explicit information-geometric calculations for parametric probability families.

| Field | Module requirement |
|---|---|
| Trigger | Fisher information, Christoffel symbols, geodesics, Laplace-Beltrami operators, harmonic functions, isometric immersions, mean curvature, or finite-type claims. |
| Primary objects | Density or mass function, support, parameter domain, score, expected Hessian, Fisher metric, arc-length coordinate, connection, geodesic, operator, immersion, and spectral function space. |
| Special assumptions | Fixed support or controlled boundary terms, differentiability under the integral, identifiability, positive metric, boundary completeness, sign convention, immersion rank and injectivity, compactness, and L2 boundary conditions. |
| Required checks | Score-variance and Hessian agreement; arc-length re-expression; boundary distance; reparameterization; pullback metric; alternate immersion; sign reversal; theorem-hypothesis and function-space audit. |
| Decisive failures | Fisher identities used outside regularity conditions; geodesic leaves the domain; immersion is not injective; pointwise eigenrelation promoted to a global spectral fact; compact theorem applied to a noncompact manifold. |
| Scope limit | Explicit one-dimensional symbolic examples do not form a general protocol for statistical inference or applied data analysis. |

The primary presentation computes Fisher metrics, connections, geodesics, Laplace-Beltrami operators, harmonic functions, immersions, and finite-type relations for exponential and Bernoulli families [D1 slides 15-55]. The consolidated framework retains the calculations while treating the quoted compactness condition and immersion dependence as separate global-review obligations.

### 10. Domain module E - Information geometry for compositional data

This module begins with data semantics and the scale-equivalence structure of compositions.

| Field | Module requirement |
|---|---|
| Trigger | Positive compositions, closure, log ratios, balances, simplex models, Aitchison or Fisher geometry, KL or Hellinger measures, subcomposition, amalgamation, or coarse-graining. |
| Primary objects | Observational unit, parts, total, denominator, positive simplex point, scale-equivalence class, coordinate system, basis, metric or divergence, sampling layer, and aggregation map. |
| Special assumptions | Common rescaling is scientifically irrelevant; parts and denominator are meaningful; positivity or explicit zero model; common support; basis and reference choice; count uncertainty; aggregation semantics. |
| Required checks | Total-versus-closure analysis; zero-type and pseudocount sensitivity; alr-reference and ilr-basis sensitivity; metric decision; coarse-graining map; information monotonicity; within-group loss decomposition; sampling-model validation. |
| Decisive failures | Meaningful totals discarded by closure; missing values treated as zeros; arbitrary pseudocount dominates ratios; reference or basis changes conclusion; amalgamation increases a measure expected to be monotone; geometry substitutes for observation-process evidence. |
| Scope limit | The primary source assumes strictly positive finite compositions and is not a complete protocol for zeros, measurement error, causal interpretation, or production pipelines. |

Primary-source anchors include equivalence between compositions and discrete distributions [E1 pp. 1-4], dual coordinates and Fisher geometry [E1 pp. 5-10], divergence and distance distinctions [E1 pp. 9-14], and information monotonicity under amalgamation [E1 pp. 13-17].

### 11. Module selection and composition

Use every module whose fatal conditions can change the claim. Do not select modules merely because they share vocabulary.

| Claim shape | Required modules | Composition rule |
|---|---|---|
| Autoencoder OOD detector | Kernel + A | Treat output reconstruction and internal geometry as separate evidence channels. |
| Empirical trading strategy | Kernel + B | Complete data, uncertainty, robustness, and execution gates before profitability claims. |
| Affine option model tested on market data | Kernel + C + B | C establishes mathematical and numerical validity; B establishes empirical and economic adequacy. Neither substitutes for the other. |
| Fisher geometry of a one-parameter distribution | Kernel + D | Require regularity, arc length, boundary, intrinsic/extrinsic, and global theorem checks. |
| Compositional regression using Fisher distance | Kernel + E, plus D if new differential geometry is derived | E controls semantics, coordinates, and sampling; D controls formal manifold derivations. |
| Physics-inspired market analogy | Kernel + B + C when an operator is claimed | B treats analogy as a hypothesis; C may upgrade it only when variables, parameters, operators, conditions, and observables map. |
| Learned representation summarized into one score | Kernel + A, plus E if the score is a composition or coarse-graining | Require a bridge and explicit loss test before operational use. |

### 12. Consolidated overlap matrix

`Core` means the concept is a required part of the shared kernel. `Strong` means the module provides specialized tests. `Bridge` means the concept appears through a domain-specific analogue.

| Knowledge area | Learned systems | Empirical finance | Affine operators | Statistical manifolds | Compositional data |
|---|---|---|---|---|---|
| Define the target object | Core | Core | Core | Core | Core |
| Object versus representation | Strong | Bridge | Strong | Strong | Strong |
| Assumption ledger | Core | Core | Core | Core | Core |
| Derive from primitives | Strong | Strong | Strong | Strong | Strong |
| Independent validation | Strong | Strong | Strong | Strong | Strong |
| Information-loss audit | Strong | Bridge | Bridge | Bridge | Strong |
| Scale or regime stress | Strong | Strong | Strong | Boundary-focused | Strong |
| Baselines and alternatives | Strong | Strong | Strong | Alternate coordinate or immersion | Alternate metric or aggregation |
| Local versus global | Strong | Strong | Strong | Strong | Strong |
| Math versus empirical validity | Strong | Strong | Strong | Strong | Strong |
| Operational readiness | Strong | Strong | Strong | Limited | Applied-study layer |
| Claim calibration | Core | Core | Core | Core | Core |

### 13. Differences that must remain visible

| Framework family | Primary object | First hard gate | Characteristic decisive test | What must not be generalized away |
|---|---|---|---|---|
| Agarwala-derived | Learned or structured system | Scope, target, and natural-versus-surrogate bridge | Seed, architecture, OOD, component baseline, matrix-versus-scalar test | Internal structure can fail while surface output looks successful. |
| Financial statistical physics | Observed market series and decision | Data construction, clock, stationarity, and leakage | Tail, scale, regime, cost, and purged temporal validation | Never begin empirical adequacy with a preferred stochastic process. |
| Hydrodynamics of markets | Stated process, operator, density, or pricer | Complete state and correct generator | PDE, normalization, delta limit, dimensions, limiting cases, convergence | Fit cannot repair a mathematically inconsistent process. |
| Geometric probability | Parametric statistical manifold | Fisher regularity and arc-length reconstruction | Boundary, immersion, compactness, sign, and function-space audit | Intrinsic geometry and extrinsic finite-type claims are different. |
| Information geometry for CoDA | Relative sample space on the simplex | Scientific meaning of scale equivalence, denominator, and zeros | Reference, basis, metric, closure, and amalgamation sensitivity | Geometry choice follows the scientific operation and invariance target. |

### 14. Decisive contradiction-resolution protocol

Do not call two statements contradictory until they have been normalized onto the same proposition.

1. **Normalize the target.** Identify whether the statements concern the same object, variable, time horizon, support, domain, and decision.
2. **Normalize validity layer.** Separate mathematical, numerical, empirical, interpretive, and operational claims.
3. **Expose conditions.** Rewrite each claim as `if conditions, then proposition, within scope`.
4. **Normalize representation.** Determine whether the difference is caused by coordinates, basis, embedding, transform, aggregation, state choice, or sampling clock.
5. **Check polarity under overlap.** A hard contradiction exists only when the normalized propositions have opposing polarity under compatible conditions and overlapping scope.
6. **Apply evidence precedence.** Prefer verified primary evidence over framework paraphrase, framework-direct statements over unified inference, and unified inference over unattributed generalization. Specific evidence does not automatically generalize beyond its scope.
7. **Seek the discriminating test.** If both remain plausible, specify the smallest observation, proof, or computation that makes their predictions diverge.
8. **Resolve without deletion.** Record the winning claim, losing claim, scope of the resolution, evidence, and whether the losing claim remains valid elsewhere.

If scope does not overlap, classify the pair as **scoped alternatives**. If methods differ but claims can both hold, classify as **procedural tension**. If an algebraic identity survives while a theorem-level interpretation fails, classify as **source-level caveat**. If evidence is insufficient, classify as **unresolved conflict** rather than averaging.

### 15. Known tensions and decisive resolutions

| Apparent conflict | Classification | Decisive resolution |
|---|---|---|
| Review passes should be independent versus review passes must run in order. | Procedural tension | Execute passes in dependency order and score them independently. Independence means noncompensation, not arbitrary sequencing. |
| Empirical finance should not begin with a preferred process versus stochastic review begins from an SDE and generator. | Scoped alternatives combined by bridge | For model discovery, run the data-first module. For a stated model or pricer, run the operator-first module. A market-use claim must pass both. |
| Physics analogy is hypothesis, not proof, versus shared affine operators establish a strong physics-finance link. | Evidence-threshold tension | Verbal, visual, or scaling similarity remains hypothesis. Equation-level equivalence is accepted only with explicit variable, parameter, operator, condition, and observable maps. It proves mathematical correspondence, not market ontology. |
| Returns are the natural market variable versus additive price models may be appropriate. | Scoped alternatives | Use returns for scale-relative statistical analysis; allow additive price models for instruments, horizons, or execution settings where the state and units justify them. The target and clock decide. |
| Fisher geometry is canonical versus no distance is universally best for compositions. | Conditional specialization | Fisher is canonical under specified statistical invariance requirements. Aitchison, Fisher, Hellinger, and KL remain question-specific because they preserve different operations and meanings. |
| A one-dimensional Fisher review is complete after arc-length verification versus a quantitative review also requires empirical evidence. | Validity-layer distinction | Arc length completes the core formal cross-check for the narrow geometry claim. It does not complete statistical, empirical, or operational review. |
| A statistical model is 1-type versus the quoted theorem requires compactness that the parameter domain lacks. | Source-level caveat | Retain the pointwise Laplacian relation for the specified immersion. Withhold the global theorem-level classification unless a valid noncompact extension or required hypotheses are supplied. |
| Singular instantaneous diffusion suggests degeneracy versus a smooth density may still exist. | False contradiction | Instantaneous rank and positive-time smoothing are different properties. Test drift-mediated controllability or covariance propagation. |
| Coarse-graining loses information versus a compressed summary may improve prediction. | Scoped distinction | Compression can improve regularization or decision performance while still losing descriptive information. Validate the summary against its intended decision and record what it discards. |

### 16. Master review finding record

Every substantive finding must contain:

| Field | Required content |
|---|---|
| Finding ID | Stable identifier. |
| Target | Exact claim, equation, transformation, experiment, implementation choice, or interpretation. |
| Normalized proposition | Proposition with object, polarity, scope, conditions, and validity layer made explicit. |
| Module routing | Kernel plus every activated domain module. |
| Evidence | Observations, derivations, diagnostics, source anchors, and provenance class. |
| Assumption implicated | The definition, condition, convenience, regularity, identification, or approximation doing the work. |
| Issue or strength | Concise finding with no manufactured objection. |
| Severity and confidence | Independent labels with reasons. |
| Affected conclusion | Which claim or decision can change. |
| Decisive test | Smallest discriminating proof, analysis, sensitivity, or reproduction. |
| Repair | Concrete correction, restriction, new evidence, or safer wording. |
| Resolution condition | Evidence that would close or reverse the finding. |
| Status | Open, resolved, accepted risk, superseded, or out of scope. |

### 17. Master acceptance standard

A work passes the superset only when:

1. The target object and intended decision are explicit.
2. The representation is justified and distinguished from the object.
3. Necessary assumptions, domains, and boundary conditions are visible.
4. Derivations, algorithms, and reductions are independently checkable.
5. Evidence identifies the stated claim and includes uncertainty where relevant.
6. Plausible alternatives, scales, regimes, and representation choices have been stressed.
7. Information loss from summaries, surrogates, or aggregation is documented.
8. Mathematical, numerical, empirical, interpretive, and operational conclusions remain separate.
9. Contradictions have been normalized and resolved by scope, evidence, or a discriminating test.
10. Negative and anomalous evidence is preserved rather than selected away.
11. Every substantive finding has a decisive test or an explicit reason no decisive test is presently possible.
12. Every evidence item has typed P, F, U, or G provenance with a stable source link.
13. Every activated module has completed its fatal gates or produced a scoped abstention.
14. Final wording says exactly what survives: no more and no less.

[[PAGEBREAK]]

## Part II - Formal knowledge ontology

### 18. Ontology purpose

The ontology gives the master framework a machine-checkable vocabulary. It prevents an AI reviewer from treating words such as "model," "distance," "valid," or "contradiction" as untyped prose. Every review assertion becomes a graph of entities, relations, conditions, provenance, and validity layers.

The ontology is minimal but extensible. It defines only the classes and relations needed to preserve the full knowledge of the five frameworks and to execute the review protocol. Domain-specific mathematical expressions remain attached artifacts rather than being forced into one universal formalism.

### 19. Core entity classes

| Class | Definition | Required attributes |
|---|---|---|
| ReviewCase | One bounded review engagement. | case_id, decision, risk_level, requested_scope |
| Source | A primary paper, presentation, review framework, dataset, codebase, or general standard. | source_id, type, title, authority_boundary |
| Citation | A locator into a Source. | citation_id, source_id, page_or_slide, excerpt_hash_or_note |
| TargetObject | The scientific, mathematical, empirical, or operational object under review. | object_id, type, units_or_support, boundaries |
| Decision | The action or judgment the review informs. | decision_id, actor, threshold, consequence |
| ValidityLayer | One of the ordered semantic, mathematical, numerical, empirical, interpretive, or operational layers. | layer_id, name, prerequisite_layer_ids |
| Claim | A proposition about a TargetObject. | claim_id, predicate, polarity, strength, validity_layer, status |
| Scope | The population, domain, horizon, regime, locality, and exclusions of a Claim. | scope_id, dimensions, inclusions, exclusions |
| Condition | A condition under which a Claim is asserted. | condition_id, kind, testability, status |
| Representation | A coordinate, basis, transform, embedding, surrogate, clock, summary, or state description. | representation_id, kind, invertibility, dependence |
| Transformation | A map between representations or objects. | transform_id, domain, codomain, exact_or_approximate |
| InformationLoss | What a Transformation or summary discards. | loss_id, lost_quantity, decision_relevance, measured |
| Model | A statistical, stochastic, geometric, graph, learning, or operational construction. | model_id, family, parameters, domain |
| Operator | A generator, metric, Jacobian, Laplacian, estimator, algorithm, or other derived mechanism. | operator_id, kind, convention, domain |
| Evidence | A proof, observation, diagnostic, result, simulation, benchmark, or reproduction. | evidence_id, provenance, quality, independence |
| Test | A falsification, sensitivity, validation, or reproduction procedure. | test_id, prediction, threshold, result |
| Alternative | A competing explanation, model, baseline, coordinate, or representation. | alternative_id, relation_to_target, plausibility |
| Finding | A review judgment linking a target, evidence, issue, severity, repair, and resolution condition. | finding_id, issue, severity, severity_reason, confidence, confidence_reason, repairability, status |
| Contradiction | A typed relation between normalized Claims. | contradiction_id, class, overlap, resolution_status |
| Resolution | The outcome of a contradiction or finding. | resolution_id, rule, winning_scope, residual_scope |
| Module | A domain-specific set of required entities, relations, tests, and gates. | module_id, trigger, exclusions |
| Gate | A noncompensatory requirement attached to the kernel, a module, a claim, or a validity layer. | gate_id, owner_id, layer, fatal, requirement |
| GateVerdict | The result of evaluating one Gate for one Claim in one ReviewCase. | verdict_id, gate_id, claim_id, status, evidence_ids, finding_ids |
| Property | A named invariant, quantity, or behavior that a Transformation may preserve. | property_id, name, definition, verification_status |
| Procedure | A derivation, repair, review sequence, or operational action that can be compared or prescribed. | procedure_id, purpose, inputs, outputs |
| ComparisonSet | The two or more Claims or Alternatives separated by a Test or joined by a Contradiction. | comparison_id, member_ids, comparison_kind |
| Waiver | An authorized decision-risk exception that never changes evidentiary truth. | waiver_id, gate_id, authority, rationale, expiry |

### 20. Core relation types

| Relation | Domain -> range | Meaning |
|---|---|---|
| about | Claim -> TargetObject | The object the proposition concerns. |
| informs | Claim -> Decision | The decision that could change if the claim changes. |
| scoped_by | Claim -> Scope | Population, domain, horizon, locality, and exclusions. |
| conditioned_on | Claim or Model -> Condition | A requirement for validity. |
| represented_by | TargetObject -> Representation | A chosen expression of the object. |
| transformed_by | Representation -> Transformation | The map used to re-express or reduce the object. |
| preserves | Transformation -> Property | A property invariant under the map. |
| loses | Transformation -> InformationLoss | Information discarded or distorted. |
| instantiated_as | TargetObject -> Model | The model used for the target. |
| derived_from | Operator or Claim -> Model, Representation, Operator, Claim, or Evidence | A dependency in the construction or argument. |
| depends_on | Claim or Finding -> Claim, Condition, Finding, Evidence, Test, or GateVerdict | A required upstream dependency whose status constrains the dependent entity. |
| approximates | Representation, Model, or Operator -> TargetObject or Operator | A nonexact bridge that requires an error statement. |
| supports | Evidence -> Claim | Positive evidentiary relation within a scope. |
| weakens | Evidence -> Claim | Evidence narrows strength or scope without complete falsification. |
| falsifies | Evidence or Test -> Claim | Negative result under the claim's stated conditions. |
| validates | Test -> Model, Operator, Transformation, or Claim | A passed check with a stated threshold. |
| discriminates | Test -> ComparisonSet | A test whose possible results separate competitors. |
| has_member | ComparisonSet -> Claim or Alternative | Membership in a typed comparison. |
| competes_with | Alternative -> Model or Claim | A plausible rival explanation or construction. |
| invariant_under | Claim -> Transformation | The claim should survive the permitted transformation. |
| fails_under | Claim -> Condition or Transformation | Known boundary of validity. |
| contradicts | Claim -> Claim | Opposing normalized propositions with overlapping scope and compatible conditions. |
| tension_with | Claim or Procedure -> Claim or Procedure | Apparent conflict lacking the conditions for hard contradiction. |
| compares | Contradiction -> ComparisonSet | The source Claims retained by the contradiction record. |
| resolves | Resolution -> Contradiction or Finding | The outcome and its justification. |
| concerns | Finding -> Claim, TargetObject, or Decision | The exact proposition, object, or decision affected by a finding. |
| justified_by | Claim, Finding, or Resolution -> Evidence or Test | Evidence or a test result supporting the judgment. |
| prescribes | Finding or Resolution -> Procedure or Test | The repair or decisive check required next. |
| cites | Claim, Evidence, Finding, or Resolution -> Citation | Stable source provenance for the assertion or judgment. |
| locates | Citation -> Source | The source containing the cited material. |
| supersedes | Claim or Finding -> Claim or Finding | Replacement while preserving provenance history. |
| activates | ReviewCase -> Module | Domain module required by the case. |
| requires_gate | Module, Claim, or ValidityLayer -> Gate | A gate that must be evaluated for the owner. |
| evaluates | GateVerdict -> Gate or Claim | The gate and claim evaluated by a verdict. |
| waived_by | GateVerdict -> Waiver | An explicit decision-risk exception that leaves evidentiary status unchanged. |

### 21. Claim coordinates

Every Claim must be located on these axes before it can support, contradict, or supersede another claim.

| Axis | Values or representation |
|---|---|
| Object type | Scientific, mathematical, empirical, numerical, interpretive, operational |
| Validity layer | Semantic, mathematical, numerical, empirical, interpretive, operational |
| Scope | Population, state domain, support, horizon, scale, regime, architecture, representation, locality |
| Conditions | Definitions, theorem conditions, model assumptions, empirical regularities, approximations |
| Polarity | Affirms, denies, bounds, compares, predicts, or remains agnostic |
| Strength | Proved, demonstrated, associated, qualitatively consistent, suggestive, unsupported |
| Provenance | P, F, U, G |
| Representation dependence | Intrinsic, invariant under named maps, or dependent on a named representation |
| Status | Proposed, supported, weakened, falsified, unresolved, superseded, out of scope |

### 22. Ontological invariants and validation rules

```text
R1  Every Claim is about at least one TargetObject.
R2  Every Claim that informs a Decision has an explicit Scope.
R3  Every nontrivial Claim is linked to Evidence or marked unsupported.
R4  Every approximation or surrogate has a bridge Claim, failure conditions, and an InformationLoss record.
R5  Every Transformation declares what it preserves and what it can change.
R6  Every theorem-level Claim links all necessary Conditions and records their status.
R7  Every empirical Claim records observational unit, sampling rule, uncertainty, and alternative explanation.
R8  Every operational Claim has GateVerdicts for semantic, mathematical, numerical, and empirical prerequisites unless explicitly waived.
R9  A severity score cannot be used as evidence and cannot be averaged across noncompensatory layers.
R10 Author identity or prestige cannot be the object of a supports relation.
R11 Claim strength cannot exceed the weakest required validated dependency.
R12 A hard contradiction requires the same normalized predicate, opposing polarity, overlapping Scope, compatible Conditions, and the same validity layer.
R13 If R12 fails, use tension_with or scoped alternatives instead of contradicts.
R14 A Resolution preserves both original claims and records winning and residual scopes.
R15 A source-level caveat retains verified algebraic or empirical Evidence while weakening only the unsupported interpretation.
R16 Every Finding links the affected Claim, TargetObject, or Decision and links its Evidence, decisive Test, and repair Procedure when present.
R17 Every Contradiction compares a ComparisonSet whose source Claims remain immutable and provenance-linked.
R18 Every machine-readable review includes the relation edges required to reproduce its claim, evidence, condition, routing, contradiction, and decision graph.
R19 Every waiver is explicit, authorized, scoped, expiring, and incapable of converting failed or unknown evidence into a pass.
R20 Every activated Module and required ValidityLayer resolves its Gates to GateVerdicts for each affected Claim.
R21 A GateVerdict status is pass, conditional, fail, unknown, or not_applicable; a Waiver may annotate but never replace that status.
```

The central noncompensation rule can be written as:

```text
admissible_strength(claim) <= minimum(
    semantic_support,
    mathematical_support when required,
    numerical_support when implemented,
    empirical_support when applied,
    operational_support when deployed
)
```

The hard-contradiction predicate is:

```text
hard_contradiction(a, b) :=
    same_normalized_predicate(a, b)
    and opposing_polarity(a, b)
    and scope_overlap(a, b)
    and compatible_conditions(a, b)
    and same_validity_layer(a, b)
```

### 23. Provenance model

Provenance is a graph, not a label pasted onto prose.

1. A primary-source claim links to a Citation in an original publication.
2. A framework claim links to the framework Citation and, where available, to its cited primary Evidence.
3. A unified claim links to at least two supporting claims or explicitly states why one source plus a formal bridge is sufficient.
4. A general-practice claim links to an external standard when available or remains labeled G.
5. Reviewer verification is new Evidence and must not be retroactively attributed to the source author.

When a framework adds a critical caveat not present in its source, the ontology stores two claims: the source claim and the reviewer caveat. The caveat may weaken the interpretation without erasing the source calculation.

### 24. Contradiction classes

| Class | Definition | Resolution method |
|---|---|---|
| Hard contradiction | Opposing normalized claims under overlapping scope and compatible conditions | Prefer stronger direct evidence or run a discriminating test; retain an unresolved state if evidence is insufficient. |
| Scoped alternative | Claims differ because object, horizon, domain, or conditions differ | Partition the scope and retain both. |
| Representation tension | Difference arises from coordinates, basis, transform, embedding, aggregation, or clock | State the invariant content and the representation-dependent residue. |
| Validity-layer tension | One claim is mathematical and the other empirical or operational | Keep layers separate and define the bridge evidence required. |
| Procedural tension | Review sequences or methods differ but results can coexist | Choose an execution rule that preserves both functions. |
| Evidence-threshold tension | Sources require different evidence before using similar language | Adopt the stricter threshold for the broader claim. |
| Source-level caveat | Calculation survives but interpretation overreaches theorem or evidence | Preserve the calculation, narrow the claim, and name the missing condition. |
| Unresolved conflict | A hard contradiction remains after normalization but evidence cannot decide | Record both predictions and the decisive future test. |

### 25. Framework-to-ontology crosswalk

| Framework concept | Ontology representation |
|---|---|
| Formal claim map | Claim -> derived_from -> intermediate Claim or Evidence -> informs -> Decision |
| Assumption ledger | Condition entities plus conditioned_on relations and testability status |
| Surrogate bridge | approximates, preserves, loses, and fails_under relations |
| Sample space or state table | TargetObject, Scope, Representation, and Condition entities |
| Metric or divergence decision | Alternative representations and Operators linked to required invariances |
| Generator audit | Model -> derived Operator with convention, domain, and validation Tests |
| Baseline or competing dynamics | Alternative competes_with Model or Claim |
| Stress plan | Test entities varying Conditions or Transformations |
| Evidence-to-claim matrix | supports, weakens, falsifies, and independence attributes |
| Severity-rated issue | Finding linked to affected Claim and Decision |
| Claim calibration table | Claim strength and status transitions with supersedes history |
| Contradiction ledger | Contradiction plus Resolution entities retaining both source Claims |

### 26. Example ontology record

The following minimal conforming record shows how an empirical Heston pricing claim activates both financial modules and prevents mathematical correctness from being mistaken for market adequacy. It is deliberately explicit: omitted optional values are `null`, identifiers are declared before use, and every edge conforms to the relation table.

```json
{
  "case": {
    "entity_type": "ReviewCase",
    "case_id": "RC-001",
    "decision": "D-USE",
    "risk_level": "high",
    "requested_scope": "pricing validation and production-hedging adequacy"
  },
  "sources": [
    {"entity_type": "Source", "source_id": "S-SUBMISSION", "type": "code_and_report", "title": "Submitted Heston implementation", "authority_boundary": "submitted artifact only"}
  ],
  "citations": [
    {"entity_type": "Citation", "citation_id": "CIT-CODE", "source_id": "S-SUBMISSION", "page_or_slide": null, "excerpt_hash_or_note": "repository content hash"}
  ],
  "decisions": [
    {"entity_type": "Decision", "decision_id": "D-USE", "actor": "model-risk committee", "threshold": "all required operational gates pass", "consequence": "authorize production hedging"}
  ],
  "validity_layers": [
    {"entity_type": "ValidityLayer", "layer_id": "L-SEM", "name": "semantic", "prerequisite_layer_ids": []},
    {"entity_type": "ValidityLayer", "layer_id": "L-MATH", "name": "mathematical", "prerequisite_layer_ids": ["L-SEM"]},
    {"entity_type": "ValidityLayer", "layer_id": "L-NUM", "name": "numerical", "prerequisite_layer_ids": ["L-SEM", "L-MATH"]},
    {"entity_type": "ValidityLayer", "layer_id": "L-EMP", "name": "empirical", "prerequisite_layer_ids": ["L-SEM", "L-MATH", "L-NUM"]},
    {"entity_type": "ValidityLayer", "layer_id": "L-OP", "name": "operational", "prerequisite_layer_ids": ["L-SEM", "L-MATH", "L-NUM", "L-EMP"]}
  ],
  "targets": [
    {"entity_type": "TargetObject", "object_id": "O-PRICE", "type": "option_price", "units_or_support": "currency per contract over stated state domain", "boundaries": "30-day European payoff and tested parameter region"},
    {"entity_type": "TargetObject", "object_id": "O-HEDGE", "type": "hedge_error", "units_or_support": "currency P and L", "boundaries": "daily rebalance in target options and regimes"}
  ],
  "scopes": [
    {"entity_type": "Scope", "scope_id": "SC-MATH", "dimensions": ["parameters", "payoff", "grid"], "inclusions": ["tested region"], "exclusions": ["unseen boundary cases"]},
    {"entity_type": "Scope", "scope_id": "SC-USE", "dimensions": ["options", "regimes", "execution"], "inclusions": ["declared target market"], "exclusions": []}
  ],
  "conditions": [
    {"entity_type": "Condition", "condition_id": "COND-MATH", "kind": "numerical_validity", "testability": "testable", "status": "passed_in_tested_region"},
    {"entity_type": "Condition", "condition_id": "COND-CAL", "kind": "out_of_sample_calibration", "testability": "testable", "status": "unknown"},
    {"entity_type": "Condition", "condition_id": "COND-EXEC", "kind": "cost_and_liquidity", "testability": "testable", "status": "unknown"}
  ],
  "representations": [],
  "transformations": [],
  "information_losses": [],
  "models": [],
  "operators": [],
  "claims": [
    {
      "entity_type": "Claim",
      "claim_id": "C-MATH",
      "predicate": "implementation solves the stated Heston pricing problem",
      "polarity": "affirms",
      "validity_layer": "numerical",
      "strength": "demonstrated",
      "status": "supported"
    },
    {
      "entity_type": "Claim",
      "claim_id": "C-USE",
      "predicate": "implementation is adequate for production hedging",
      "polarity": "affirms",
      "validity_layer": "operational",
      "strength": "unsupported",
      "status": "unresolved"
    }
  ],
  "evidence": [
    {"entity_type": "Evidence", "evidence_id": "E-PDE", "provenance": "G", "quality": "direct numerical diagnostic linked to CIT-CODE", "independence": "independent runner"},
    {"entity_type": "Evidence", "evidence_id": "E-INVENTORY", "provenance": "G", "quality": "complete submitted-artifact inventory found no out-of-sample hedge result", "independence": "reviewer inventory"},
    {"entity_type": "Evidence", "evidence_id": "E-SCOPE", "provenance": "G", "quality": "target, payoff, clock, and requested decision reconstructed directly from submission", "independence": "reviewer semantic audit"}
  ],
  "tests": [
    {"entity_type": "Test", "test_id": "T-PDE", "prediction": "residual below declared tolerance", "threshold": "predeclared numerical tolerance", "result": "pass"},
    {"entity_type": "Test", "test_id": "T-HEDGE", "prediction": "net out-of-sample hedge error beats benchmark after costs", "threshold": "predeclared operational threshold", "result": "unknown"}
  ],
  "comparison_sets": [
    {"entity_type": "ComparisonSet", "comparison_id": "CMP-HEDGE", "member_ids": ["C-USE", "ALT-NO-ADEQUACY"], "comparison_kind": "claim_vs_null"}
  ],
  "alternatives": [
    {"entity_type": "Alternative", "alternative_id": "ALT-NO-ADEQUACY", "relation_to_target": "production null", "plausibility": "live until T-HEDGE is run"}
  ],
  "properties": [],
  "waivers": [],
  "contradictions": [],
  "modules": [
    {"entity_type": "Module", "module_id": "KERNEL", "trigger": "all cases", "exclusions": []},
    {"entity_type": "Module", "module_id": "EMPIRICAL_FINANCE", "trigger": "production hedging and market execution", "exclusions": []},
    {"entity_type": "Module", "module_id": "AFFINE_OPERATORS", "trigger": "Heston SDE, generator, PDE, and pricing", "exclusions": []}
  ],
  "gates": [
    {"entity_type": "Gate", "gate_id": "G-SEMANTIC", "owner_id": "L-SEM", "layer": "semantic", "fatal": true, "requirement": "target, payoff, clock, and decision are explicit"},
    {"entity_type": "Gate", "gate_id": "G-MATHEMATICAL", "owner_id": "L-MATH", "layer": "mathematical", "fatal": true, "requirement": "generator and problem statement are mathematically coherent"},
    {"entity_type": "Gate", "gate_id": "G-NUMERICAL", "owner_id": "L-NUM", "layer": "numerical", "fatal": true, "requirement": "implementation passes independent numerical checks"},
    {"entity_type": "Gate", "gate_id": "G-EMPIRICAL", "owner_id": "L-EMP", "layer": "empirical", "fatal": true, "requirement": "calibration and hedge evidence generalize out of sample"},
    {"entity_type": "Gate", "gate_id": "G-OPERATIONAL", "owner_id": "EMPIRICAL_FINANCE", "layer": "operational", "fatal": true, "requirement": "out-of-sample hedge error beats benchmark after costs"}
  ],
  "gate_verdicts": [
    {"entity_type": "GateVerdict", "verdict_id": "GV-SEMANTIC", "gate_id": "G-SEMANTIC", "claim_id": "C-USE", "status": "pass", "evidence_ids": ["E-SCOPE"], "finding_ids": []},
    {"entity_type": "GateVerdict", "verdict_id": "GV-MATHEMATICAL", "gate_id": "G-MATHEMATICAL", "claim_id": "C-USE", "status": "pass", "evidence_ids": ["E-PDE"], "finding_ids": []},
    {"entity_type": "GateVerdict", "verdict_id": "GV-NUMERICAL", "gate_id": "G-NUMERICAL", "claim_id": "C-USE", "status": "pass", "evidence_ids": ["E-PDE"], "finding_ids": []},
    {"entity_type": "GateVerdict", "verdict_id": "GV-EMPIRICAL", "gate_id": "G-EMPIRICAL", "claim_id": "C-USE", "status": "unknown", "evidence_ids": [], "finding_ids": ["F-GAP"]},
    {"entity_type": "GateVerdict", "verdict_id": "GV-OPERATIONAL", "gate_id": "G-OPERATIONAL", "claim_id": "C-USE", "status": "unknown", "evidence_ids": [], "finding_ids": ["F-GAP"]}
  ],
  "procedures": [
    {"entity_type": "Procedure", "procedure_id": "P-HEDGE-STUDY", "purpose": "produce the missing operational evidence", "inputs": ["target option panel", "cost and liquidity model"], "outputs": ["out-of-sample hedge result"]}
  ],
  "findings": [
    {"entity_type": "Finding", "finding_id": "F-GAP", "issue": "production adequacy lacks out-of-sample cost-aware evidence", "severity": "fatal", "severity_reason": "the requested operational decision depends on the missing evidence", "confidence": "high", "confidence_reason": "the gate is explicitly unevaluated", "repairability": "new_evidence_required", "status": "open"}
  ],
  "relations": [
    {"relation_id": "REL-01", "type": "about", "from_id": "C-MATH", "to_id": "O-PRICE"},
    {"relation_id": "REL-02", "type": "about", "from_id": "C-USE", "to_id": "O-HEDGE"},
    {"relation_id": "REL-03", "type": "informs", "from_id": "C-USE", "to_id": "D-USE"},
    {"relation_id": "REL-04", "type": "scoped_by", "from_id": "C-MATH", "to_id": "SC-MATH"},
    {"relation_id": "REL-05", "type": "scoped_by", "from_id": "C-USE", "to_id": "SC-USE"},
    {"relation_id": "REL-06", "type": "conditioned_on", "from_id": "C-MATH", "to_id": "COND-MATH"},
    {"relation_id": "REL-07", "type": "conditioned_on", "from_id": "C-USE", "to_id": "COND-CAL"},
    {"relation_id": "REL-08", "type": "conditioned_on", "from_id": "C-USE", "to_id": "COND-EXEC"},
    {"relation_id": "REL-09", "type": "depends_on", "from_id": "C-USE", "to_id": "C-MATH"},
    {"relation_id": "REL-10", "type": "validates", "from_id": "T-PDE", "to_id": "C-MATH"},
    {"relation_id": "REL-10A", "type": "supports", "from_id": "E-PDE", "to_id": "C-MATH"},
    {"relation_id": "REL-11", "type": "discriminates", "from_id": "T-HEDGE", "to_id": "CMP-HEDGE"},
    {"relation_id": "REL-12", "type": "has_member", "from_id": "CMP-HEDGE", "to_id": "C-USE"},
    {"relation_id": "REL-13", "type": "has_member", "from_id": "CMP-HEDGE", "to_id": "ALT-NO-ADEQUACY"},
    {"relation_id": "REL-14", "type": "concerns", "from_id": "F-GAP", "to_id": "C-USE"},
    {"relation_id": "REL-15", "type": "prescribes", "from_id": "F-GAP", "to_id": "T-HEDGE"},
    {"relation_id": "REL-15A", "type": "prescribes", "from_id": "F-GAP", "to_id": "P-HEDGE-STUDY"},
    {"relation_id": "REL-15B", "type": "justified_by", "from_id": "F-GAP", "to_id": "T-HEDGE"},
    {"relation_id": "REL-15C", "type": "justified_by", "from_id": "F-GAP", "to_id": "E-INVENTORY"},
    {"relation_id": "REL-16", "type": "cites", "from_id": "E-PDE", "to_id": "CIT-CODE"},
    {"relation_id": "REL-17", "type": "locates", "from_id": "CIT-CODE", "to_id": "S-SUBMISSION"},
    {"relation_id": "REL-18", "type": "activates", "from_id": "RC-001", "to_id": "KERNEL"},
    {"relation_id": "REL-19", "type": "activates", "from_id": "RC-001", "to_id": "EMPIRICAL_FINANCE"},
    {"relation_id": "REL-20", "type": "activates", "from_id": "RC-001", "to_id": "AFFINE_OPERATORS"},
    {"relation_id": "REL-21", "type": "requires_gate", "from_id": "EMPIRICAL_FINANCE", "to_id": "G-OPERATIONAL"},
    {"relation_id": "REL-22", "type": "evaluates", "from_id": "GV-OPERATIONAL", "to_id": "G-OPERATIONAL"},
    {"relation_id": "REL-23", "type": "evaluates", "from_id": "GV-OPERATIONAL", "to_id": "C-USE"}
  ],
  "resolutions": [],
  "module_routes": [],
  "decision_projection": "Accept the tested numerical result provisionally; abstain on production adequacy pending T-HEDGE."
}
```

### 27. Canonical knowledge graph queries

An implementation of the ontology should answer at least these questions:

- Which claims depend on an untested or failed condition?
- Which operational claims lack empirical or numerical support?
- Which transformations have no preservation or information-loss record?
- Which findings rely only on framework synthesis or general practice?
- Which two claims are marked contradictory even though their scopes do not overlap?
- Which theorem-level claims lack compactness, boundary, integrability, or function-space conditions?
- Which market-use claims passed operator tests but not calibration, cost, liquidity, or regime tests?
- Which learned-system claims rely on scalar summaries that failed against richer internal structure?
- Which compositional conclusions change with reference, basis, zero treatment, closure, or amalgamation?
- Which negative or anomalous results were superseded without an explicit resolution?

### 28. Minimal interchange schema

Any machine-readable implementation should preserve this top-level structure:

```json
{
  "case": {},
  "sources": [],
  "citations": [],
  "targets": [],
  "decisions": [],
  "validity_layers": [],
  "claims": [],
  "scopes": [],
  "conditions": [],
  "representations": [],
  "transformations": [],
  "information_losses": [],
  "models": [],
  "operators": [],
  "evidence": [],
  "tests": [],
  "alternatives": [],
  "properties": [],
  "procedures": [],
  "comparison_sets": [],
  "waivers": [],
  "findings": [],
  "contradictions": [],
  "resolutions": [],
  "modules": [],
  "module_routes": [],
  "gates": [],
  "gate_verdicts": [],
  "relations": []
}
```

Every entity record carries `entity_type` plus its class identifier and all required attributes from section 19. Every relation record carries `relation_id`, `type`, `from_id`, and `to_id`; optional `scope_id`, `condition_ids`, and `provenance` fields qualify the edge. Identifiers must be stable within the review. References must resolve to a declared entity of a domain and range permitted by section 20. Unknown values are explicit `null` plus an `unknown_reason`, or the enumerated status `unknown`; they are never silently invented. Implementations may add fields, but they cannot remove, rename, merge, or flatten these normative collections.

[[PAGEBREAK]]

## Part III - Executable AI reviewer

### 29. Operating contract

The executable reviewer is a reasoning protocol, not a persona. It uses sources as evidence and never claims to reproduce an author's private judgment. It must identify strengths as rigorously as weaknesses, avoid manufacturing objections, expose uncertainty, and produce decision-changing tests.

The reviewer executes Parts I and II in this order:

1. Parse the intake into ontology entities.
2. Activate the shared kernel and required modules.
3. Run the eight passes in dependency order.
4. Score every validity layer independently.
5. Normalize apparent contradictions before classifying them.
6. Generate findings with provenance, severity, confidence, decisive tests, and repairs.
7. Emit both a human-readable report and a machine-readable review graph.

### 30. Required intake

| Intake field | Requirement |
|---|---|
| Central claim | One sentence in the strongest wording the submitter wants reviewed. |
| Intended decision | Publication, model selection, deployment, pricing, risk, scientific interpretation, or another named action. |
| Target object | Object, variables, support, units, horizon, state, sample space, or theorem. |
| Materials | Paper, appendix, code, data, model card, results, citations, and known limitations. |
| Domain triggers | Learned systems, empirical finance, affine operators, statistical manifolds, compositional data, or combinations. |
| Known constraints | Compute, confidentiality, data access, time, legal restrictions, or unavailable artifacts. |
| Risk tolerance | Consequence of false acceptance and false rejection. |
| Requested output | Full review, derivation audit, empirical audit, contradiction audit, or claim-calibration pass. |

Missing intake does not authorize invention. The reviewer records unknowns and either proceeds with conditional findings or stops when the missing item blocks a fatal gate.

### 31. Module-routing algorithm

```text
activate KERNEL for every case

if learned representation, autoencoder, learned map, Jacobian, model-internal geometry,
graph generator, graph probability model, MDP state/action similarity, transfer learning,
architecture comparison, seed sensitivity, or OOD behavior:
    activate LEARNED_SYSTEMS

if observed market series, price or return construction, financial correlation or dependence,
volatility, tails, regimes, risk, trading strategy, option assumption, backtest, execution,
market calibration, or an empirical physics analogy applied to markets:
    activate EMPIRICAL_FINANCE

if SDE, jump-diffusion, generator, forward or backward equation, affine process, affine PDE,
Kelvin wave, transition density, Fourier or transform pricing, stochastic volatility,
path-dependent augmentation, rates, derivative pricing, or automated market maker:
    activate AFFINE_OPERATORS

if probability family geometry, Fisher metric derivation, arc-length coordinate, connection,
geodesic, Laplace-Beltrami operator, harmonic function, immersion, curvature, mean curvature,
compactness claim, spectrum, or finite type:
    activate STATISTICAL_MANIFOLDS

if relative parts, positive composition, simplex, closure, log ratios, balances, zeros,
Aitchison, Fisher, KL, or Hellinger geometry, subcomposition, amalgamation,
coarse-graining, or information monotonicity:
    activate COMPOSITIONAL_DATA

infer routes from the claim and submitted materials; submitter labels are hints, not authority
apply semantic aliases and ontology types before keyword matching
run positive and negative routing conformance cases for every trigger family

if a claim spans modules:
    union required gates
    preserve module-specific validity layers
    do not average severities
```

### 32. Master system prompt

```text
You are the Unified Citation-Grounded Quantitative Reviewer.

Your function is to evaluate claims through a shared review kernel and the relevant domain modules. You are not a simulation of any source author. Author prestige is never evidence. Separate primary-source claims, framework statements, unified inference, and general practice using the labels P, F, U, and G.

For every case:

1. State the scope of review, sources available, missing expert lenses, and activated modules.
2. Identify the exact target object and intended decision. Record units, support, horizon, domain, boundary, observational unit, payoff, or deployment target as applicable.
3. Separate the object from its representation. Name coordinates, basis, clock, transform, embedding, surrogate, summary, or augmented state. State what each transformation preserves and loses.
4. Build a classified assumption ledger. Distinguish definitions, theorem conditions, model assumptions, convenience assumptions, empirical regularities, identification assumptions, and computational approximations. Record testability and consequence of failure.
5. Audit construction and derivation from primitives. Verify domains, dimensions, signs, factors, rank, normalization, regularity, convergence, boundary or terminal conditions, theorem hypotheses, and bridge arguments.
6. Build an evidence-to-claim matrix. Separate mathematical, numerical, empirical, interpretive, and operational validity. Use independent checks and identify negative or anomalous evidence.
7. Compare simple baselines and plausible alternatives. Stress scale, regime, seed, architecture, distribution, basis, metric, aggregation, calibration window, boundary, and numerical settings when relevant.
8. For every reduction or aggregation, record information lost and test whether the reduced object remains adequate for the intended decision.
9. Normalize apparent contradictions by object, scope, conditions, representation, polarity, and validity layer. Classify each as hard contradiction, scoped alternative, representation tension, validity-layer tension, procedural tension, evidence-threshold tension, source-level caveat, or unresolved conflict.
10. Resolve hard contradictions using the strongest directly relevant evidence or a discriminating test. Never average incompatible claims. Preserve the losing claim when it remains valid in a residual scope.
11. Calibrate each conclusion as proved, demonstrated, associated, qualitatively consistent, suggestive, or unsupported.
12. Identify strengths with the same evidence discipline as weaknesses. Do not manufacture objections.

For every substantive finding output:
- finding ID;
- exact target;
- normalized proposition;
- activated modules;
- evidence and P/F/U/G provenance;
- implicated assumptions;
- issue or strength;
- severity and confidence with reasons;
- affected conclusion and validity layer;
- smallest decisive test;
- concrete repair;
- resolution evidence;
- status.

Apply noncompensatory gates. A correct formula cannot repair an invalid target. Empirical fit cannot repair a wrong generator. Mathematical validity does not establish market adequacy. Coordinate correctness does not establish scientific semantics. Operational success in one regime does not prove a general model.

When evidence is missing, say unknown. When the source is narrow, narrow the claim. End with a decision-useful report and a machine-readable review graph.
```

### 33. Eight-pass execution instructions

#### Pass 0 - Scope and provenance

- Inventory every source and artifact.
- Assign P, F, U, or G to every review rule used.
- State where the selected corpus is strong and weak.
- Activate modules from the routing algorithm.
- Record missing expertise and evidence.

Output: scope statement, source map, evidence-label policy, module route, and unknowns.

#### Pass 1 - Target and decision

- Rewrite the central claim as a normalized proposition.
- State the intended decision and consequence of error.
- Separate training objective, evaluation metric, scientific claim, pricing claim, and deployment claim.
- Define the estimand, payoff, theorem, distance, prediction, or functional.

Output: claim map and decision threshold.

#### Pass 2 - Semantics and representation

- Define sample space, state, variables, coordinates, basis, transforms, embeddings, surrogates, summaries, and clocks.
- Test whether the representation is scientifically and mathematically admissible.
- Record permitted transformations and required invariances.

Output: target-object card, representation ledger, and transformation-loss table.

#### Pass 3 - Assumptions and admissibility

- Classify every assumption and condition.
- Verify support, positivity, stationarity, independence, identifiability, compactness, integrability, affine eligibility, boundary conditions, and implementation approximations as applicable.
- Mark untestable assumptions and narrow claims accordingly.

Output: assumption ledger with status and failure consequences.

#### Pass 4 - Construction and derivation

- Re-derive the central equations or algorithms from primitives.
- Verify theorem hypotheses, sign conventions, dimensions, factors, rank, normalization, domains, and edge cases.
- For surrogates and reductions, write the exact bridge and failure region.

Output: derivation issues, verified steps, and bridge table.

#### Pass 5 - Evidence and independent verification

- Match each evidence item to the claim it supports.
- Require structurally independent checks.
- Review uncertainty, effect size, multiplicity, calibration, residuals, reproduction, convergence, and negative findings as relevant.

Output: evidence-to-claim matrix, reproduction record, and validity-layer scorecard.

#### Pass 6 - Stress, alternatives, and information loss

- Construct the smallest plausible alternative explanation or model.
- Vary the conditions most likely to reverse the conclusion.
- Compare simple baselines and module-specific alternatives.
- Quantify or describe what every transformation and aggregation discards.

Output: ranked decisive tests, alternative matrix, and information-loss audit.

#### Pass 7 - Calibration and decision

- Normalize and classify contradictions.
- Resolve by scope, representation, evidence, or discriminating test.
- Rate findings by severity and confidence.
- Rewrite every major claim to the strongest justified wording.
- Separate acceptance decisions for each validity layer.

Output: final report, contradiction ledger, calibrated claim table, and machine-readable graph.

### 34. Contradiction resolver routine

```text
for each apparent conflict (a, b):
    normalize target, predicate, polarity, scope, conditions, representation, validity layer

    if predicate differs:
        emit no-conflict/different-question and do not create a Contradiction
    elif claims are semantically equivalent and compatible:
        emit duplicate-or-compatible and merge only by provenance-preserving supersession
    elif scope does not overlap or conditions differ:
        classify as scoped alternatives
    elif representation explains the difference:
        identify invariant core and classify residue as representation tension
    elif one claim preserves a verified calculation or observation but rejects an overextended interpretation:
        classify as source-level caveat regardless of whether validity-layer labels match
        preserve the verified core, narrow the interpretation, and name the missing condition
    elif validity layer differs:
        classify as validity-layer tension and state required bridge evidence
    elif polarity is not opposing:
        if competing review sequences or methods can coexist:
            classify as procedural tension
        elif language differs because evidence thresholds differ:
            classify as evidence-threshold tension
        else:
            emit no-conflict/compatible and do not create a Contradiction
    else:
        classify as hard contradiction
        create a ComparisonSet retaining both source Claims and both predictions
        compare evidence relevance, provenance, verification, and scope
        if one side is decisively stronger:
            resolve for the overlapping scope and preserve residual scope
        else:
            classify as unresolved conflict
            preserve both predictions and specify the smallest discriminating Test
```

The resolver must never use publication date, author reputation, document length, or rhetorical confidence as a tie-breaker.

### 35. Machine-readable output schema

```json
{
  "schema_version": "unified-review-1.0",
  "case": {},
  "sources": [],
  "citations": [],
  "decisions": [],
  "validity_layers": [],
  "targets": [],
  "claims": [],
  "scopes": [],
  "conditions": [],
  "representations": [],
  "transformations": [],
  "information_losses": [],
  "models": [],
  "operators": [],
  "evidence": [],
  "alternatives": [],
  "tests": [],
  "properties": [],
  "procedures": [],
  "comparison_sets": [],
  "waivers": [],
  "findings": [
    {
      "entity_type": "Finding",
      "finding_id": "F-001",
      "issue": "string",
      "severity": "fatal|major|moderate|minor|extension",
      "severity_reason": "string",
      "confidence": "high|medium|low",
      "confidence_reason": "string",
      "repairability": "scope_narrowing_only|analysis_repair|new_evidence_required|not_repairable",
      "status": "open|resolved|accepted_risk|superseded|out_of_scope"
    }
  ],
  "contradictions": [],
  "resolutions": [],
  "modules": [],
  "module_routes": [],
  "gates": [],
  "gate_verdicts": [],
  "relations": [
    {
      "relation_id": "REL-001",
      "type": "about|supports|weakens|falsifies|depends_on|other_declared_type",
      "from_id": "declared entity ID",
      "to_id": "declared entity ID",
      "scope_id": null,
      "condition_ids": [],
      "provenance": "P|F|U|G"
    }
  ],
  "validity_decisions": [
    {
      "claim_id": "C-001",
      "layer": "semantic|mathematical|numerical|empirical|interpretive|operational",
      "required": true,
      "status": "pass|conditional|fail|unknown|not_applicable",
      "finding_ids": [],
      "waiver_id": null
    }
  ],
  "final_decisions": [
    {
      "claim_id": "C-001",
      "decision": "accept|accept_scoped|revise_and_recheck|withhold|reject|abstain|out_of_scope",
      "admissible_strength": "proved|demonstrated|associated|qualitatively_consistent|suggestive|unsupported",
      "scope_id": "SC-001",
      "reason_finding_ids": []
    }
  ],
  "derived_views": {
    "scope_summary": {},
    "assumption_ledger": [],
    "derivation_audit": [],
    "evidence_matrix": [],
    "transformation_loss_table": [],
    "calibrated_claim_table": []
  },
  "unknowns": [],
  "missing_expert_lenses": []
}
```

This is a strict extension of the Part II interchange graph. `derived_views` are reproducible projections and cannot replace normalized entities or relation edges. Each Evidence record links at least one Citation or an explicit reviewer-generated provenance record. Each Finding reaches its target, evidence, conditions, decisive test, repair, and resolution through typed relations. Schema validation checks required attributes, enumerations, referential integrity, relation domain and range, duplicate identifiers, and the invariants in section 22 before a report can be released.

### 35.1 Deterministic gate and decision semantics

Claim strength has a ceiling order used only for noncompensation:

`unsupported < suggestive < qualitatively_consistent < associated < demonstrated < proved`

The labels retain distinct meanings; the order does not turn association into proof. A claim's admissible strength is the minimum ceiling across every required dependency. A dependency's ceiling comes from its typed evidence, not from severity, confidence, author, or module score.

Required layers are determined by the claim path. Semantic validity is always required. Mathematical validity is required for formal claims; numerical validity for computed implementations; empirical validity for real-world application; interpretive validity for mechanism or meaning; and operational validity for deployment. A later layer cannot pass when a required earlier layer is `fail` or `unknown`.

Every blocking Finding declares exactly one repairability value: `scope_narrowing_only`, `analysis_repair`, `new_evidence_required`, or `not_repairable`. This value, severity, and affected layer determine the transition; free-text preference does not.

```text
evaluate_layer(claim, layer):
    if layer is not required: return not_applicable
    if any required GateVerdict is not_applicable: return fail
    if any necessary Condition is failed: return fail
    if any necessary Condition is unknown: return unknown
    if any fatal required GateVerdict is fail: return fail
    if any fatal required GateVerdict is unknown: return unknown
    if an open fatal Finding requires new evidence and has no falsifying result: return unknown
    if any other fatal Finding is open in this layer: return fail
    if an open major Finding requires analysis repair: return fail
    if an open major Finding requires new evidence: return unknown
    if any open major Finding is not_repairable: return fail
    if any open major Finding is scope_narrowing_only:
        if a residual Scope is verified: return conditional
        return fail
    if any nonfatal required GateVerdict is fail or unknown: return conditional
    if any required GateVerdict is conditional: return conditional
    if all necessary gates pass but the verified Scope is narrower: return conditional
    return pass

decide(claim):
    evaluate required layers in dependency order
    if semantic is fail: return reject
    if any required layer is fail:
        if any blocking Finding is not_repairable: return reject
        if operational is the only failed layer and every prerequisite layer passes: return withhold
        return revise_and_recheck
    if any required layer is unknown: return abstain
    if any required layer is conditional: return accept_scoped
    return accept
```

A waiver records decision authority and accepted consequence; it does not alter the layer status, evidence, or strength ceiling. An `accepted_risk` Finding remains visible and cannot waive a false target, invalid mathematics, data leakage, or an unknown necessary condition into a pass. `Revise_and_recheck` is reserved for a failed but repairable design or analysis. `Abstain` is reserved for an unknown necessary dependency. `Withhold` is reserved for a failed operational claim whose prerequisite scientific layers still pass. Abstention is per claim and scope, so supported subclaims remain reportable when a broader claim is withheld.

### 36. Human-readable report template

1. **Decision summary.** What is accepted, rejected, or conditional at each validity layer.
2. **Scope and routing.** Sources, modules, and missing expert lenses.
3. **Target and claim map.** Object, decision, intermediate quantities, and final claims.
4. **Representations and information loss.** Coordinates, transforms, surrogates, summaries, and what they discard.
5. **Assumption ledger.** Status, testability, and consequence of failure.
6. **Verified strengths.** Strongest derivations, designs, diagnostics, or disclosures.
7. **Fatal and major findings.** Full finding records ordered by decision impact.
8. **Moderate, minor, and extension findings.** Kept separate from validity blockers.
9. **Contradiction ledger.** Normalized conflicts, classifications, and resolutions.
10. **Decisive test plan.** Smallest tests first, with predicted outcomes for competing claims.
11. **Calibrated claim table.** Original wording, justified wording, evidence, scope, and uncertainty.
12. **Final confidence statement.** What evidence would change the reviewer’s mind.

### 37. Specialized reviewer cards

#### Learned-systems card

```text
Identify input, latent, reconstruction, graph, state, action, and deployment objects. Separate output performance from internal geometry. Verify natural-versus-surrogate bridges, theorem and initialization conditions, component baselines, mechanism-relevant metrics, and matrix-versus-scalar reductions. Stress seed, epoch, architecture, dimension, boundary, representation, and controlled OOD families. Preserve anomalous spectra and failed scalar correlations.
```

#### Empirical-finance card

```text
Begin with instrument, price definition, clock, return construction, horizon, and decision. Diagnose linear and nonlinear dependence, scale behavior, tails, volatility clustering, stationarity, and regimes before selecting a process. Audit estimation uncertainty, temporal leakage, alternative windows and models, costs, delay, liquidity, hedge discreteness, and stressed dependence. Separate statistical predictability from executable profitability.
```

#### Affine-operator card

```text
Define the complete Markov state, SDE, domain, measure, numeraire, payoff, and initial or terminal data. Derive the generator and adjoint term by term. Certify affine eligibility and transform domains. Verify dimensions, signs, one-half factors, covariance, jumps, killing, positivity, normalization, delta limit, moments, PDE residuals, Chapman-Kolmogorov, limiting cases, branch continuity, convergence, and independent benchmark or Monte Carlo agreement.
```

#### Statistical-manifold card

```text
State the probability family, support, base measure, and parameter domain. Verify normalization, identifiability, Fisher regularity, score variance, expected Hessian, metric, arc-length coordinate, connection, geodesics, boundary distance, Laplace-Beltrami sign, harmonics, immersion rank, injectivity, pullback metric, image, mean curvature, compactness, and spectral function space. Separate intrinsic claims from immersion-dependent extrinsic claims.
```

#### Compositional-data card

```text
Define the observational unit, parts, total, denominator, and reason common rescaling is irrelevant. Classify zeros and missingness. State closure, coordinates, reference, basis, metric or divergence, sampling model, and aggregation operation. Test total-versus-closure, reference and basis sensitivity, zero strategy, metric invariances, coarse-graining, information monotonicity, within-group loss, and interpretation stability.
```

### 38. Stop, escalation, and abstention rules

The reviewer stops or abstains when:

- The target object or intended decision cannot be identified.
- Required data, code, equations, or source pages are unavailable and the missing material controls a fatal gate.
- A theorem claim depends on unstated or unverified hypotheses that cannot be recovered.
- A market deployment decision requires legal, liquidity, operational, or current empirical evidence outside the corpus.
- A causal, clinical, survey, or other specialized claim lacks the necessary expert module.
- A contradiction remains hard and unresolved because no discriminating evidence is available.
- The requested conclusion would require impersonating an author or treating prestige as evidence.

Abstention is scoped. The reviewer should still report verified strengths, known limits, conditional results, and the evidence needed to continue.

### 39. Reviewer quality-assurance tests

Before release, verify:

- Every major claim has a stable identifier and explicit scope.
- Every finding cites evidence and a provenance class.
- Every activated module completed its fatal gates.
- No downstream layer is used to compensate for an upstream failure.
- Every surrogate, transform, summary, or aggregation has a bridge and loss record.
- Every hard contradiction satisfies the ontology predicate.
- Every resolved contradiction preserves residual scope and source history.
- Every fatal or major concern has a decisive test and repair.
- Strengths and negative findings are both represented.
- Final wording matches claim strength and validity layer.
- Machine-readable and human-readable outputs agree.

### 40. Worked integrated example

**Submitted claim:** "Our Heston implementation proves that the strategy will hedge profitably in production."

**Routing:** Kernel + Affine Operators + Empirical Finance.

**Pass 1:** The claim contains at least three propositions: the implementation solves the stated Heston problem; the model describes the target options and regimes; the strategy produces positive executable P and L after hedging and costs.

**Pass 2:** The mathematical state is log price and variance under a pricing measure. The operational object is realized hedge P and L under the physical market and an execution clock. These are related but not identical representations or measures.

**Pass 3:** Mathematical conditions include variance-domain behavior, correlation, transform existence, branch continuity, and terminal payoff. Empirical and operational conditions include calibration stability, bid-ask spreads, rebalancing frequency, liquidity, and data timing.

**Pass 4:** Derive the generator from the SDE, verify cross-derivatives and one-half factors, solve the transform ODEs, and check discounting and payoff inversion.

**Pass 5:** Require PDE residuals, limiting cases, numerical convergence, and benchmark prices for mathematical and numerical validity. Require out-of-sample calibration and hedge-error evidence for empirical validity.

**Pass 6:** Compare Black-Scholes, alternative stochastic-volatility dynamics, parameter windows, stressed volatility regimes, transaction costs, delayed execution, and discrete rebalancing.

**Pass 7:** Resolve the apparent equation-versus-market contradiction by validity layer. A correct implementation can support "the code solves the tested Heston pricing problem." It cannot by itself support "the strategy will hedge profitably in production."

**Calibrated decision:** Accept the mathematical implementation conditionally if generator, density, transform, and numerical checks pass. Withhold the production-profitability claim pending out-of-sample hedge-error, cost, liquidity, regime, and controls evidence.

This example demonstrates why the data-first and operator-first frameworks are complementary rather than contradictory.

[[PAGEBREAK]]

## Part IV - Modular alpha research operating system

### 41. Scope, safety, and the operational meaning of alpha

This part specifies research infrastructure, not a promise of returns and not a recommendation to trade. It explains how the review kernel, ontology, and executable reviewer can govern machine learning, statistical analysis, geometric methods, stochastic models, and other pipelines used to investigate equities, exchange-traded funds, and equity options.

Within this system, **alpha** is not raw backtest profit, a high in-sample Sharpe ratio, a visually persuasive chart, or a model's prediction score. An alpha claim is a typed proposition that a fully specified decision rule improves a declared objective relative to an explicit benchmark, after risk, turnover, costs, liquidity, timing, capital, and uncertainty are included, and that the improvement survives genuinely out-of-sample evaluation. The claim must declare:

- The universe and point-in-time membership rule.
- The prediction or decision horizon and the clock on which it operates.
- The instrument, position, portfolio, and benchmark.
- The data available at each decision time.
- The signal, sizing, constraint, execution, cost, and risk policies.
- The capital base, capacity assumptions, and operational limits.
- The evaluation metric, uncertainty estimate, and multiplicity adjustment.
- The regimes, venues, and dates over which the claim is intended to hold.

The system recognizes a strict evidence ladder: exploratory association, reproducible research result, sealed out-of-sample candidate, shadow-trading evidence, limited-live evidence, and production evidence. Movement up this ladder requires new evidence. It cannot be achieved by stronger wording.

### 42. Derivation from Parts I through III

Part IV is a direct implementation of the common dependency chain:

`target object -> representation -> assumptions -> model -> evidence -> stress tests -> calibrated decision`

For alpha research, the target object is a decision under information available at a particular time. Its representations include bars, order-book states, features, embeddings, volatility surfaces, graphs, regimes, and portfolio states. Assumptions cover clocks, point-in-time availability, survivorship, execution, borrowing, settlement, model form, stationarity, and capacity. Evidence consists of reproducible runs and independent checks. Stress tests vary regimes, samples, providers, horizons, costs, fills, and representations. The calibrated decision is a promotion, hold, demotion, archive, or abstention verdict.

Part II contributes the typed vocabulary. `Claim`, `TargetObject`, `Representation`, `Assumption`, `EvidenceItem`, `StressTest`, `ValidityLayer`, `Finding`, and `Resolution` remain the core entities. Part IV adds domain artifacts without changing their semantics. Part III contributes the reviewer that routes ideas, checks fatal gates, requests decisive tests, and records verdicts. The reviewer becomes one controlled participant in the research lifecycle, not an autonomous source of truth.

The five domain modules remain available. Empirical Finance is mandatory for every alpha claim. Learned Systems activates for machine learning, embeddings, graph models, and reinforcement learning. Affine Operators activates for stochastic-volatility, density, PDE, and transform-based option models. Statistical Manifolds activates for Fisher metrics, distribution geometry, and geometric signal construction. Compositional Data activates for portfolio weights, holdings, sector shares, flow mixtures, and other relative data whose totals or denominators matter.

### 43. Multi-perspective design synthesis

The operating design was pressure-tested from five perspectives.

| Perspective | Primary demand | Failure it exposes | Design response |
|---|---|---|---|
| Practitioner | Reproducible data, realistic fills, capacity, maintainability | A model that cannot be operated or traded as tested | Immutable snapshots, cost and execution modules, shadow stages, runbooks |
| Academic methodologist | Explicit estimands, honest splits, baselines, uncertainty, multiplicity | Selection bias, leakage, weak identification, low power | Split plans, sealed holdouts, trial ledgers, independent baselines, adjusted inference |
| Adversarial skeptic | Evidence that survives alternate explanations | Vendor artifacts, regime coincidence, fragile parameters, accidental leakage | Provider checks, negative controls, perturbations, regime and parameter surfaces |
| Incentive analyst | Traceable human, vendor, and agent incentives | Cherry-picking, hidden trial counts, metric switching, confirmation bias | Append-only run history, declared objectives, typed verdicts, approval boundaries |
| Historical observer | Evidence that acknowledges decay and structural change | Crowding, market redesign, data revisions, disappearing anomalies | Walk-forward evidence, decay monitoring, change-point tests, demotion rules |

The central tension is speed versus validity. Fast experimentation is valuable, but unrestricted search consumes statistical degrees of freedom and contaminates data used for confirmation. The resolution is a staged funnel: inexpensive exploratory search on declared development data, automatic logging of every material trial, narrow promotion into a sealed validation stage, and a shadow stage before any live authority. Exploration remains broad; claims remain narrow.

### 44. Universal research flow

Every idea follows the same directed flow:

```text
plain-language idea
  -> IdeaCard and claim decomposition
  -> ontology routing and module selection
  -> point-in-time data contract and immutable snapshot
  -> universe, features, labels, splits, and baselines
  -> model or rule, signal, portfolio, cost, risk, and execution simulation
  -> out-of-sample evidence, uncertainty, multiplicity, and stress tests
  -> AI and human review with decisive promotion gates
  -> archive, revise, sealed validation, shadow, limited live, or production
  -> monitoring, incident review, demotion, and reproducible history
```

No stage may silently repair a failure in an earlier stage. A sophisticated model cannot repair a leaky label. Portfolio optimization cannot repair a wrong universe. A conservative transaction-cost assumption cannot repair stale option chains. Attractive live results cannot retroactively make an undocumented experiment reproducible.

The same flow supports factor research, supervised learning, representation learning, graph models, causal hypotheses, time-series rules, volatility-surface studies, stochastic-process calibration, event studies, and portfolio construction. Modules change; contracts and gates do not.

### 45. Required data plane

The data plane must represent both market events and when the researcher could have known them. At minimum it records `event_time`, `source_time`, `received_time`, `published_time`, `available_at`, source, version, correction status, and ingestion run. Historical reconstruction uses `available_at`, not the latest revised value.

| Data family | Minimum contents | Point-in-time requirement | Common fatal failure |
|---|---|---|---|
| Security master and symbology | Stable internal ID, ticker history, exchange, share class, identifier mappings, listing and delisting dates | Effective-from and effective-to intervals | Joining by current ticker or dropping delisted securities |
| Trading calendars and states | Sessions, auctions, holidays, halts, limit states, venue status | Venue-specific effective time | Treating a closed, halted, or auction-only period as tradable |
| Corporate actions | Splits, dividends, mergers, spinoffs, tender events, symbol changes, delisting proceeds | Announcement, ex, record, payable, and effective times | Forward-adjusted leakage or inconsistent price and share adjustment |
| Equity and ETF market data | Trades, quotes, bars, conditions, cancellations and corrections; depth when the strategy requires it | Exchange timestamp and feed receipt time | Using last trade as executable price or assuming top-of-book equals full liquidity |
| Fundamentals and filings | As-reported facts, filing version, restatements, period, currency, units | Filing acceptance or vendor availability time | Joining on fiscal period end instead of public availability |
| Estimates and classifications | Estimate history, contributor set, sector and industry history | Each revision and vendor publication time | Replacing historical consensus with the latest value |
| ETF state | Holdings, weights, shares, NAV or indicative value, flows, creations and redemptions | Publication lag and holdings effective date | Treating delayed holdings as contemporaneous |
| Options reference | Root and OSI symbol, underlying ID, expiry, strike, call or put, style, multiplier, deliverable, settlement, currency | Contract-effective interval and adjustment memo | Treating adjusted contracts as standard 100-share contracts |
| Options market data | Bid, ask, sizes, trades, quote conditions, open interest, volume, venue or consolidated source | Quote and trade clock; declare open-interest lag | Marking at last trade, using stale quotes, or treating open interest as intraday flow |
| Financing state | Risk-free curve, dividends, borrow rate and availability, locate status, margin terms | Decision-time curve and inventory snapshot | Assuming free, unlimited, or continuously available shorting |
| Context and alternatives | Macroeconomic releases, news, transcripts, sentiment, weather, web or proprietary data | Original release plus revisions and embargo time | Backfilling corrected or revised data into earlier decisions |
| Portfolio and execution | Orders, acknowledgments, fills, cancels, rejects, fees, borrow, positions, cash, margin, limits | Event-sourced operational clock | Evaluating live behavior from intended orders instead of actual fills |

Consolidated equity feeds provide trades and best quotations but not necessarily complete depth; deeper order-book work may require separate proprietary exchange feeds [M1]. Options data has similar distinctions among consolidated OPRA data, exchange-specific feeds, and enriched vendor products [M4, M5]. The system therefore stores feed coverage as part of the data contract and prohibits a model from implying liquidity the selected feed cannot observe.

### 46. Point-in-time invariants and data-quality gates

The following invariants are non-negotiable:

1. Every observation has a stable instrument identity and an `available_at` timestamp.
2. Every join is an as-of join constrained by information availability.
3. Universe membership is reconstructed for each decision date, including delistings.
4. Corporate actions transform prices, shares, cash flows, and option deliverables consistently.
5. Corrections and cancellations are preserved; the chosen replay policy is explicit.
6. Time zones, daylight-saving rules, sessions, auctions, and halts are normalized without erasing source timestamps.
7. Missingness, staleness, zero values, and vendor sentinels remain distinguishable.
8. Feature and label windows have auditable boundaries and cannot overlap prohibited future information.
9. Raw source bytes or immutable vendor partitions receive content hashes and lineage.
10. Data rights declare research, non-display, derived-data, redistribution, and production permissions.

Automated data gates check schema, uniqueness, monotonicity, timestamp order, identifier coverage, missingness, crossed or locked quotes, impossible prices, stale intervals, corporate-action reconciliation, return outliers, volume and open-interest discontinuities, and cross-provider agreement. A passing schema gate establishes structural fitness, not economic correctness. Samples must also be inspected around known events, expirations, symbol changes, splits, halts, and delistings.

### 47. Compute and storage tiers

The architecture scales by substituting implementations behind stable contracts.

| Tier | Suitable workload | Minimal capabilities | Promotion trigger |
|---|---|---|---|
| 0: Local research | Daily or modest intraday studies, prototypes, unit tests | Versioned code, columnar files, embedded analytical query engine, deterministic runner | Data no longer fits comfortably or runs block iteration |
| 1: Shared research | Team experiments and repeatable batch pipelines | Object storage, metadata database, orchestrator, shared cache, experiment registry | Concurrent workloads, larger histories, or stronger availability needs |
| 2: Distributed batch | Full-universe intraday features, large sweeps, options surfaces | Partitioned CPU compute, distributed query, workload queue, budget controls | Single-node latency or memory becomes the measured bottleneck |
| 3: Accelerator | Deep learning, large embeddings, simulation-heavy calibration | Scheduled GPU or accelerator pools, checkpointing, artifact registry | Model profile demonstrates accelerator benefit |
| 4: Shadow and live | Event-driven inference, order simulation, monitoring | Event bus, online feature state, broker adapter, limits, kill switch, observability | Only after sealed validation and explicit operational approval |

Columnar object storage is the durable analytical boundary. Compute products are disposable and reproducible from manifests. A metadata service stores artifacts, schemas, versions, lineage, gates, approvals, and permissions. Batch orchestration is sufficient until latency is part of the hypothesis. Live infrastructure is a different validity layer and is never implied by a successful notebook.

Resource profiles belong to each module: expected rows, memory, CPU, accelerator, wall time, concurrency, cache key, and estimated cost. The scheduler can then choose local, distributed, or accelerated execution without changing the scientific definition of a run.

### 48. Composable module contracts

Every module implements the same envelope:

```text
ModuleManifest {
  module_id, version, purpose, owner, validity_layer,
  input_artifact_types[], output_artifact_types[], schemas[],
  clock, available_at_policy, universe_policy,
  parameters, defaults, determinism, random_seed_policy,
  dependencies, resource_profile, cache_policy,
  data_rights, assumptions[], failure_modes[],
  unit_tests[], invariants[], monitoring_hooks[],
  agent_description, human_controls[], provenance
}
```

The core module families are:

| Family | Responsibility | Required output |
|---|---|---|
| Universe | Define eligible instruments at each time | `UniverseSnapshot` |
| Data source | Acquire and version raw or vendor data | `DataManifest` and immutable partitions |
| Cleaner and adjuster | Normalize conditions, identifiers, clocks, and actions | Quality report and adjusted view |
| Feature | Transform available history into model inputs | `FeatureManifest` with lineage and availability |
| Label | Define the future outcome without leakage | `LabelDefinition` and horizon audit |
| Split | Define development, validation, embargo, and sealed periods | `SplitPlan` |
| Baseline | Supply naive, structural, and prior-method comparators | Baseline result bundle |
| Model | Fit a statistical, ML, geometric, or stochastic construction | Versioned fitted artifact and diagnostics |
| Signal | Convert model output into a declared decision score | Signal series and calibration report |
| Portfolio | Convert signals into positions under constraints | Target positions and constraint diagnostics |
| Cost | Estimate spread, impact, fees, borrow, exercise, and financing | Gross-to-net attribution |
| Risk | Measure and constrain exposures, concentration, tail, liquidity, and scenario risk | Risk state and breaches |
| Execution | Simulate or transmit orders under explicit fill rules | Orders, fills, rejects, and slippage |
| Validator | Run independent, stress, multiplicity, and falsification tests | Gate-ready evidence items |
| Reporter | Produce machine and human result bundles | Reproducible report with claim links |
| Agent tool | Expose a narrow, permissioned action to an agent | Typed request, response, and audit event |
| Monitor | Detect drift, data breaks, capacity loss, and control breaches | Incident or demotion trigger |
| Governance | Apply approvals, sealed-data controls, and live authority | Signed promotion record |

A new method becomes composable when it consumes and emits these artifacts. It does not need to know which vendor, scheduler, model library, or UI supplied them.

### 49. Promotion, demotion, and validation gates

Promotion is noncompensatory: each required gate must pass. A high score at one gate cannot offset failure at another.

| Gate | Required question | Minimum evidence | Fail action |
|---|---|---|---|
| G0 Semantic and data | Is the object, universe, clock, label, and point-in-time data correct? | Data contract, quality report, sampled event reconstruction | Block and repair data or claim |
| G1 Reproducibility | Can an independent runner reproduce the result from the manifest? | Immutable snapshot hashes, environment lock, deterministic run | Demote to sandbox |
| G2 Baselines | Does the method beat naive, structural, and relevant prior baselines? | Identical splits, costs, constraints, and metrics | Archive or justify continued research |
| G3 Out-of-sample | Does performance survive leakage-safe temporal evaluation? | Walk-forward or blocked results, embargo where labels overlap | Return to development without touching sealed data |
| G4 Selection and uncertainty | Is the apparent advantage credible after trial count and non-normality? | Trial ledger, uncertainty intervals, multiplicity-aware statistic | Demote or narrow the claim |
| G5 Economics | Does it survive spread, fees, impact, borrow, turnover, capacity, and capital? | Conservative scenarios and break-even analysis | Reject deployability claim |
| G6 Robustness | Does it survive plausible regimes, providers, universes, parameters, and representations? | Stress matrix, negative controls, fragility surface | Hold, redesign, or scope narrowly |
| G7 Shadow | Does event-time behavior match the backtest without capital at risk? | Paper or shadow orders, realized latency and fill comparison | Diagnose simulation-to-reality gap |
| G8 Governed live | Are controls, monitoring, authority, rollback, and risk limits in place? | Runbook, approvals, kill switch, incident plan | Prohibit live activation |

White's Reality Check tests whether the best model found in a specification search has predictive superiority over a benchmark while accounting for data reuse [R1]. Hansen's Superior Predictive Ability test is a related benchmark-comparison procedure designed to improve power [R2]. The Probability of Backtest Overfitting estimates how often selection among tested strategies produces an in-sample winner that degrades out of sample [R3]. The Deflated Sharpe Ratio adjusts a selected Sharpe ratio for multiple testing and non-normal returns [R4]. These are complementary diagnostics, not ceremonial badges. Their assumptions, dependence structure, effective trial count, and applicability must be recorded.

Leakage-safe splitting is asset and label dependent. Overlapping future-return labels may require purging and an embargo. Hyperparameter selection belongs inside the development loop, not on the final holdout. The sealed holdout is access-controlled: the proposing agent and researcher cannot inspect it, iteratively query it, or change metrics after seeing it. One authorized evaluation yields an immutable result and consumes the corresponding validation budget.

Demotion is first-class. It is triggered by data corrections, unexplained live divergence, cost or capacity deterioration, drawdown or exposure breaches, feature drift, model decay, control failures, market-structure changes, or evidence that invalidates an assumption. A demotion record preserves what failed, the last valid scope, affected versions, open positions or experiments, and the evidence required for reconsideration.

### 50. Experiment artifacts and lifecycle states

The ontology is extended with the following artifacts:

| Artifact | Purpose |
|---|---|
| `IdeaCard` | Plain-language thesis, mechanism, target, falsifier, horizon, universe, benchmark, and expected cost |
| `DataManifest` | Source, rights, schema, clocks, partitions, coverage, quality, lineage, and hashes |
| `UniverseSnapshot` | Point-in-time eligibility and exclusion reasons |
| `FeatureManifest` | Formula or model, inputs, lookback, availability, missingness, and invariances |
| `LabelDefinition` | Outcome, horizon, observation rule, censoring, overlap, and units |
| `SplitPlan` | Development, nested selection, validation, embargo, sealed data, and randomization |
| `ExperimentManifest` | Complete pipeline DAG, versions, parameters, seeds, budgets, metrics, and claim IDs |
| `RunRecord` | Immutable execution facts, environment, logs, timing, resource use, and artifact hashes |
| `ResultBundle` | Metrics, uncertainty, trades, diagnostics, baselines, stresses, failures, and claim links |
| `GateVerdict` | Gate, status, evidence, reviewer, confidence, decisive test, and repair |
| `PromotionRecord` | From-state, to-state, approvals, scope, limits, and expiry |
| `DeploymentCard` | Online inputs, latency, broker or venue, controls, monitoring, rollback, and ownership |
| `IncidentRecord` | Detection, impact, containment, evidence, root cause, demotion, and recovery test |

Lifecycle states are `Proposed -> Sandbox -> Reproducible -> Candidate -> Sealed Validation -> Shadow -> Limited Live -> Production`. `Held`, `Demoted`, and `Archived` are reachable from every state. The state machine records who or what caused each transition. No UI label such as "approved" may exist without the underlying `PromotionRecord`.

### 51. Research-design patterns

**Cross-sectional equities and ETFs.** Reconstruct the point-in-time universe, predict or rank a future outcome, neutralize only exposures declared in advance, convert scores to constrained weights, and evaluate with turnover, borrow, sector, beta, liquidity, and capacity. Baselines include equal weight, simple factor ranks, prior signal, and no-trade. The review must distinguish forecast quality from portfolio-construction value.

**Time-series and regime rules.** Use walk-forward evaluation, stable clock definitions, explicit warm-up, and regime tests that do not infer regimes from future data. Compare to unconditional exposure, simple moving or volatility rules, and a risk-matched benchmark. Report sensitivity to start dates and parameter neighborhoods, not only a selected optimum.

**Event studies.** Declare the event timestamp, information-release path, eligibility, overlapping events, and tradable response time. Use matched or risk-adjusted controls, test anticipation and post-event leakage, and preserve events with missing or negative outcomes. Operational evidence must include halt, auction, spread, and gap behavior.

**Statistical arbitrage and graph methods.** Separate relationship discovery from trade evaluation. Re-estimate graphs or clusters using only available history, test stability and false connections, and compare to simpler distance or factor models. Portfolio evidence must include common-factor exposure, crowding, borrow, and simultaneous unwind stress.

**Machine learning.** Put feature selection, architecture search, preprocessing, calibration, and threshold choice inside the selection ledger. Test simpler models, feature groups, seed dispersion, distribution shift, output calibration, and the representation itself. Feature importance is not mechanism; reconstruction quality is not tradability.

**Distributional and geometric methods.** Define the statistical family, support, metric, coordinates, and invariances. Compare geometric constructions to conventional statistical distances and models. For compositional holdings or flows, verify the denominator, closure, zeros, basis sensitivity, aggregation, and information loss before interpreting distances.

### 52. Options-specific pipeline requirements

Options require a dedicated contract-state engine, not an equity backtester with an option price column. The reference state must include root and full symbol, underlying, expiration, strike, type, exercise style, settlement, multiplier, deliverable, currency, listing interval, and every adjustment. OCC materials govern exercise, assignment, settlement, and standardized-option risks, while OCC information memos are the authoritative operational source for contract-adjustment events [M2, M3].

The options replay engine must:

- Reconstruct contemporaneous chains without introducing contracts before listing.
- Preserve bid, ask, sizes, quote condition, venue or consolidated source, and underlying quote.
- Detect stale, crossed, locked, one-sided, zero, and intrinsically inconsistent markets.
- Distinguish trade price from executable quote and declare the fill model inside the spread.
- Treat open interest as a delayed daily state unless the source explicitly provides otherwise.
- Apply adjusted multipliers and deliverables through corporate events.
- Model exercise, assignment, expiration, settlement, and pin uncertainty when relevant.
- Include dividends, rates, borrow, locate, margin, financing, and stock-leg execution.
- Recompute implied volatility and Greeks under a declared model and compare to vendor fields.
- Check no-arbitrage bounds and surface consistency before treating an implied value as data.
- Attribute P and L to underlying move, volatility, time, rates, dividends, execution, and residual.
- Stress early exercise, discrete hedging, gaps, halts, volatility shocks, skew shifts, and liquidity withdrawal.

An options backtest that marks long and short positions at a convenient midpoint without fill probability, spread, size, and stock-leg costs is exploratory only. A volatility-surface anomaly is not an alpha claim until a trade construction, hedge policy, capital rule, and executable benchmark are specified.

### 53. Agent roles, authority, and separation of duties

The system may expose several agent roles through one interface:

| Role | Permitted contribution | Prohibited shortcut |
|---|---|---|
| Researcher | Propose mechanisms, features, falsifiers, and experiments | Declare success from exploratory evidence |
| Composer | Select compatible modules and assemble a DAG | Bypass an input contract or fatal gate |
| Data steward | Diagnose coverage, lineage, rights, and quality | Infer unavailable history from current vendor state |
| Interpreter | Explain metrics, diagnostics, regimes, and uncertainty | Convert association into causal or deployable claims |
| Critic | Generate alternative explanations and decisive stress tests | Change the target merely to manufacture failure |
| Reviewer | Apply ontology, evidence, severity, and gate rules | Compensate for one failed gate with another strong metric |
| Promoter | Recommend a state transition with cited evidence | Approve its own unreviewed work or unlock sealed data |
| Operator | Monitor shadow or live behavior and execute approved runbooks | Expand capital, universe, or authority outside limits |

Agent actions are typed tool calls. Every call records role, identity, time, input artifact versions, requested action, authorization decision, output, confidence, and changed state. The agent cannot silently alter objectives, metrics, benchmarks, costs, trial counts, exclusions, or sealed data. Live order authority, if ever enabled, is a separate human-granted permission with position limits, pre-trade risk checks, a kill switch, and complete audit logs.

Promotion and demotion recommendations must cite specific `EvidenceItem` and `GateVerdict` IDs. The agent must state what would change its recommendation. When evidence is insufficient, the correct output is a scoped hold or abstention plus the smallest next test.

### 54. A nontechnical interface that preserves technical truth

The user interface hides machinery through progressive disclosure, not by hiding risk.

**Home.** The user types an idea in ordinary language, such as "Do unusually steep short-dated ETF volatility skews predict next-week relative returns?" The system returns an editable IdeaCard: target, mechanism, universe, horizon, benchmark, falsifier, required data, and likely cost drivers.

**Data readiness.** A simple traffic-light card shows coverage, point-in-time status, contract adjustments, licensing, missingness, and estimated compute. Expanding it reveals fields, clocks, vendors, sampled events, and failed checks.

**Pipeline recipe.** Modules appear as understandable chips: universe, data, feature, label, comparison, model, portfolio, cost, stress tests, review. The system suggests a safe default recipe and explains why each module is present. An advanced view exposes the full DAG, versions, parameters, schemas, and resource profile.

**Run view.** A timeline shows queued, running, cached, failed, and complete steps. The user sees estimates for time and compute before launch. Failures are phrased as actionable causes, not stack traces, with technical details available on demand.

**Evidence view.** Results lead with the claim, baseline, out-of-sample effect, uncertainty, costs, fragility, and gate verdict. The user can ask the interpreter agent questions, but every answer links back to artifacts. Negative evidence and invalid runs remain visible.

**Comparison view.** Ideas and versions can be compared on identical data, splits, costs, constraints, and metrics. The UI blocks misleading comparisons and explains the mismatch.

**Decision view.** Promotion, hold, demotion, or archive appears with reasons, failed gates, decisive next tests, scope, approvers, and expiry. A one-click reproduce action uses the exact manifest. No one-click live-trade control exists in the research interface.

### 55. Adding a module safely

A new module is accepted only when it supplies:

1. A unique ID, semantic version, owner, purpose, and validity layer.
2. Typed input and output schemas with compatibility tests.
3. Clock, availability, universe, missingness, and corporate-action policies.
4. Determinism and seed behavior, dependencies, resource profile, and cache key.
5. Unit fixtures, invariant tests, negative controls, and known failure modes.
6. Provenance, data-rights implications, monitoring hooks, and rollback behavior.
7. A plain-language agent description and explicit human-control boundaries.
8. A small reference pipeline proving interoperability with at least one baseline and validator.

The registry distinguishes backward-compatible additions from semantic changes. A pipeline pins module versions. Old runs remain reproducible even after a new version is promoted. Compatibility is tested at artifact boundaries, so a model, data vendor, query engine, scheduler, or UI can change without rewriting the entire system.

### 56. Reference implementation blueprint

The blueprint defines capabilities rather than imposing a single vendor stack:

- **Durable analytical store:** versioned columnar partitions in object storage.
- **Query and transformation:** an embedded engine locally and a distributed engine only when measured scale requires it.
- **Metadata and ontology registry:** relational or graph-backed records for artifacts, claims, relations, versions, lineage, rights, and verdicts.
- **Orchestration:** a DAG scheduler with retries, caching, budgets, artifact checks, and observable state.
- **Experiment execution:** isolated, locked environments with deterministic seeds and content-addressed outputs.
- **Model and artifact registry:** fitted models, features, reports, metrics, signatures, and promotion stages.
- **Agent gateway:** narrow tools over the same artifact APIs used by the UI, with role-based authorization and audit events.
- **Research UI:** plain-language idea capture, recipe composition, run monitoring, evidence comparison, and decision records.
- **Shadow and live boundary:** separate event-driven services, online state, broker adapter, pre-trade limits, monitoring, and kill switch.

One practical starting implementation could use Parquet-compatible files, a local analytical database, Python data-frame and ML libraries, a metadata database, a workflow orchestrator, and a web interface. These are replaceable choices. The durable architecture is the artifact contract, point-in-time clock, gate state machine, and provenance graph.

### 57. Worked equity and ETF example

**Idea:** "Stocks with unusual ETF ownership-flow divergence have positive risk-adjusted returns over the next five trading days."

The IdeaCard separates a mechanism claim from a prediction claim. The compositional module activates because ETF holdings and weights are relative parts with changing totals. The universe module reconstructs eligible stocks and ETFs on each date. Data readiness checks holdings publication lag, creation and redemption timing, corporate actions, delistings, and when each flow estimate became available.

The feature module declares the denominator, closure, missing holdings, aggregation, and as-of time. The label module defines the five-day return and overlap. Baselines include market and sector controls, simple ownership change, price momentum, and no divergence transformation. The split plan uses time blocks with purging for overlapping labels. The trial ledger includes alternative horizons, denominators, distance metrics, winsorization, neutralization, and model variants.

Suppose the selected model beats the naive baseline in development but its advantage disappears after realistic publication lag and turnover. G0 passes, G1 passes, G2 becomes marginal, and G5 fails. The correct verdict is not "almost alpha." The executable claim is demoted. The representation may still be scientifically interesting, and the agent can propose a lower-turnover horizon or a better mechanism test without reusing sealed data.

### 58. Worked equity-options example

**Idea:** "A locally inconsistent implied-volatility surface predicts profitable delta-hedged convergence."

The statistical-manifold and affine-operator modules activate alongside empirical finance. The target is not surface smoothness; it is net delta-hedged P and L under an explicit option-selection, hedge, and exit policy. Data contracts require contemporaneous option NBBO, sizes, underlying quotes, contract reference, OCC adjustments, rates, dividends, borrow, and open-interest timing.

The construction compares a simple parametric surface, a geometric model, and raw interpolation. Validators check no-arbitrage bounds, coordinate and parameterization sensitivity, quote staleness, vendor Greeks versus recomputation, numerical convergence, and residual structure. The backtester executes at conservative quote locations, models stock-leg and option-leg costs, and handles adjusted contracts, exercise, expiration, and pin scenarios.

Suppose gross convergence is strong, but it is concentrated in one-sided stale quotes and disappears when requiring displayed size. The critic identifies a representation-to-execution contradiction. This is resolved at the validity-layer boundary: the surface diagnostic may detect data or microstructure anomalies, but evidence does not support executable alpha. The candidate is archived or rerouted into a data-quality detector.

### 59. Staged build plan and final standard

**Stage 1: Trustworthy daily research.** Implement security master, calendars, corporate actions, delistings, daily equities and ETF data, point-in-time manifests, local columnar storage, baseline modules, deterministic runs, and the evidence UI.

**Stage 2: Reproducible model research.** Add feature, label, split, ML, portfolio, cost, risk, validator, trial-ledger, and comparison modules. Enforce G0 through G6 and sealed validation.

**Stage 3: Options research.** Add options reference and adjustment state, quote and trade replay, rates, dividends, borrow, surface and Greeks modules, exercise and settlement, stock-leg execution, and option-specific stresses.

**Stage 4: Agent-guided interpretation.** Expose artifact APIs as permissioned tools; add researcher, composer, steward, interpreter, critic, and reviewer roles. Agents may recommend but cannot self-authorize promotions or inspect sealed data.

**Stage 5: Shadow operations.** Add event-time ingestion, shadow orders, realized latency and fill comparisons, monitoring, incident records, and G7.

**Stage 6: Governed limited live.** Only if separately authorized, add broker connectivity, pre-trade controls, capital limits, kill switch, approvals, and G8. Expand capital or universe only through new promotion records.

The final standard is decisive:

> No result is called alpha unless the exact point-in-time decision rule, benchmark, costs, risks, trial history, out-of-sample evidence, capacity, operational scope, and uncertainty are recorded and all required gates pass. Everything else is an idea, diagnostic, research result, or candidate, named honestly.

[[PAGEBREAK]]

## Appendix A - Source map

### Primary sources

| Key | Source | Main contribution to the superset |
|---|---|---|
| A1 | Agarwala, Dees, Gearhart, and Lowman, *Geometry and Generalization: Eigenvalues as predictors of where a network will fail to generalize*, arXiv:2107.06386v1, 2021. | Jacobian spectra, local model geometry, error bounds, internal predictors, train-test-deployment distinction. |
| A2 | Agarwala and Kenter, *A Geometric Chung Lu model and the Drosophila Medulla connectome*, arXiv:2109.00061v1, 2021. | Composite graph model, independence assumptions, boundary effects, component comparison, multi-metric validation. |
| A3 | Dees, Agarwala, and Lowman, *Eigenvalues of Autoencoders in Training and at Initialization*, arXiv:2201.11813v1, 2022. | Training-time spectral evolution and calibrated use of asymptotic random-matrix theory. |
| A4 | Agarwala, Dees, and Lowman, *Geometric instability of out of distribution data across autoencoder architecture*, arXiv:2201.11902v1, 2022. | Architecture, seed, dimension, and OOD stress tests; separation of reconstruction appearance from latent geometry. |
| A5 | Ashcraft, Stoler, Ewulum, and Agarwala, *Structural Similarity for Improved Transfer in Reinforcement Learning*, arXiv:2207.13813v1, 2022. | State and action similarity, convergence conditions, transfer baselines, failed scalar task-distance correlation. |
| B1 | Esteban Guevara Hidalgo, *Statistical Physics in the Modeling of Financial Markets*, M1 Project, 2011. | Returns, dependence, scale, tails, stochastic processes, Black-Scholes, turbulence analogy, VaR, and GARCH. |
| C1 | A. Lipton, *Hydrodynamics of Markets: Hidden Links Between Physics and Finance*, arXiv:2403.09761v1, 2024. | Affine processes, Kelvin waves, transition densities, augmentation, model-specific pricing, and independent verification. |
| D1 | Ioana Radulescu (Lazarescu), joint work with Ioana Antonia Branea, *A Geometric Approach of Probability Distributions*, presentation, 2023. | Fisher metrics, geodesics, Laplace-Beltrami operators, harmonic functions, immersions, and finite-type claims. |
| E1 | Ionas Erb and Nihat Ay, *The Information-Geometric Perspective of Compositional Data Analysis*, arXiv:2005.11510v3, 2021. | Simplex equivalence, dual geometry, Fisher and Aitchison measures, divergences, amalgamation, and information monotonicity. |

### Review frameworks consolidated

| Framework | Role in this document |
|---|---|
| *Citation-Grounded Expert Review Framework* derived from five Agarwala papers | Broad peer-review operating model, issue anatomy, surrogate and stability logic. |
| *Financial Statistical Physics Review Framework* | Data-first market review, stylized facts, tail and execution realism. |
| *Hydrodynamics of Markets: Citation-Grounded Review Framework* | Operator-first stochastic derivation, density validation, pricing and production separation. |
| *Geometric Probability Distributions: Statistical-Manifold Review Framework* | Arc-length verification, intrinsic/extrinsic separation, global theorem caveats. |
| *Information Geometry for Compositional Data: Citation-Grounded Review Framework* | Semantics, invariance, coordinate, metric, aggregation, and information-loss review. |

### Part IV research-method and market-infrastructure sources

These sources ground specific Part IV controls. The overall operating architecture remains a unified inference and general engineering design. Links were accessed on 2026-07-20.

| Key | Source | Narrow contribution |
|---|---|---|
| R1 | Halbert White, [A Reality Check for Data Snooping](https://doi.org/10.1111/1468-0262.00152), *Econometrica* 68(5), 2000. | Benchmark-relative test of the best model in a specification search while accounting for data reuse. |
| R2 | Peter Reinhard Hansen, [A Test for Superior Predictive Ability](https://doi.org/10.1198/073500105000000063), *Journal of Business and Economic Statistics* 23(4), 2005. | Studentized, sample-dependent SPA test with improved power and reduced sensitivity to poor alternatives. |
| R3 | Bailey, Borwein, Lopez de Prado, and Zhu, [The Probability of Backtest Overfitting](https://escholarship.org/uc/item/4w1110bb), *Journal of Computational Finance*, 2015. | Combinatorially symmetric cross-validation and an estimate of selection-process backtest overfitting. |
| R4 | Bailey and Lopez de Prado, [The Deflated Sharpe Ratio](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551), *Journal of Portfolio Management* 40(5), 2014. | Sharpe-ratio evidence adjusted for selection under multiple testing and non-normal returns. |
| M1 | U.S. Securities and Exchange Commission, [MIDAS Market Information Data Analytics System](https://www.sec.gov/securities-topics/market-structure-analytics/midas-market-information-data-analytics-system). | Consolidated trades and best quotes are not complete depth; full-book reconstruction uses proprietary exchange feeds. |
| M2 | Options Clearing Corporation, [Characteristics and Risks of Standardized Options](https://www.theocc.com/getmedia/a151a9ae-d784-4a15-bdeb-23a029f50b70/rikstoc.pdf), June 2024. | Contract terms, exercise, assignment, settlement, margin, costs, adjustments, and standardized-option risks. |
| M3 | Options Clearing Corporation, [Information Memos](https://infomemo.theocc.com/infomemo/search-memo). | Authoritative contract-adjustment events, effective dates, symbols, multipliers, and deliverables. |
| M4 | Cboe, [Options Lite](https://www.cboe.com/data/market-data-services/cboe-options-lite/). | OPRA-derived NBBO and last-sale coverage plus contract reference fields needed to interpret options. |
| M5 | Cboe DataShop, [Options Data FAQ](https://datashop.cboe.com/faqs) and [Option Quote Intervals](https://datashop.cboe.com/option-quote-intervals). | Vendor Greeks and zero-value limitations, overnight open-interest timing, adjusted roots, and interval-versus-tick granularity. |
| L1 | OPRA, [Exhibit A - Description of Use of OPRA Data](https://cdn.opraplan.com/documents/OPRA_Exhibit_A.pdf). | Internal, non-display, and external redistribution uses require distinct agreements and declarations. |
| L2 | CTA/CQ Plans, [Non-Display Use Declaration](https://www.ctaplan.com/publicdocs/ctaplan/CTA_Non_Display_Declaration_Form.pdf). | Investment analysis, algorithmic trading, risk management, and valuation can be licensed non-display uses. |
| L3 | UTP Plan, [Data Policies](https://utpplan.com/DOC/Datapolicies.pdf). | Real-time non-display administration and fee categories apply to Nasdaq-listed consolidated data. |

No one statistic or feed resolves alpha validity. R1-R4 address different selection and benchmark questions. M1-M5 describe different market-data and contract layers. L1-L3 establish why data rights are part of the executable contract rather than an administrative afterthought.

## Appendix B - Compact module crosswalk

| If the work contains... | Activate | Ask first | Never infer automatically |
|---|---|---|---|
| Autoencoder, learned representation, graph generator, MDP transfer | Learned systems | What internal object carries the claim, and what surrogate represents it? | Low output error implies stable internal geometry. |
| Returns, risk, volatility, backtest, strategy | Empirical finance | Is the data object and clock correct? | Fit implies a generative law or executable profit. |
| SDE, PDE, transition density, Fourier pricer | Affine operators | Is the state complete and generator correct? | Exact formula implies empirical adequacy. |
| Fisher metric, geodesic, Laplacian, immersion | Statistical manifolds | Are support, domain, and regularity valid? | One immersion is the intrinsic statistical object. |
| Relative parts, log ratios, simplex, amalgamation | Compositional data | Is common rescaling scientifically irrelevant? | Closed proportions are automatically compositions. |

## Appendix C - Contradiction ledger template

| Field | Entry |
|---|---|
| Contradiction ID | Stable identifier |
| Claim A and source | Normalized claim, scope, conditions, layer, provenance |
| Claim B and source | Normalized claim, scope, conditions, layer, provenance |
| Overlap test | Same predicate, opposing polarity, overlapping scope, compatible conditions, same layer |
| Classification | Hard, scoped, representation, validity-layer, procedural, threshold, caveat, unresolved |
| Evidence comparison | Relevance, directness, verification, independence, uncertainty |
| Discriminating test | Smallest test whose outcomes separate the claims |
| Resolution | Winner in overlap, residual validity, or unresolved status |
| Claim revisions | Exact new wording for both claims |
| Provenance preservation | Links to original claims, evidence, and supersession history |

## Appendix D - One-page field protocol

1. Define the decision and exact target.
2. Route to the kernel and every required domain module.
3. Separate the object from coordinates, transforms, surrogates, summaries, and clocks.
4. Build the assumption and admissibility ledger.
5. Re-derive the central construction from primitives.
6. Demand independent checks and map evidence to claims.
7. Stress plausible alternatives, scales, regimes, and representations.
8. Record information lost by every reduction or aggregation.
9. Normalize apparent contradictions before resolving them.
10. Decide separately at semantic, mathematical, numerical, empirical, interpretive, and operational layers.
11. Attach severity, confidence, decisive test, repair, and resolution evidence to every finding.
12. State exactly what survives and what evidence would change the decision.

The shortest faithful summary of the entire superset is:

`Get the object right. Make the bridge explicit. Test the weakest link. Preserve scope. Resolve conflicts by conditions and evidence. Claim only what survives.`

## Appendix E - Alpha research run and decision cards

### Alpha run card

| Field | Required content |
|---|---|
| Claim | Mechanism, prediction, decision, universe, horizon, benchmark, and falsifier |
| Point-in-time data | Sources, rights, coverage, clocks, available-at rule, vintage, hashes, exclusions |
| Representation | Bars, quotes, chains, features, embeddings, surfaces, factors, or portfolio state; preservation and loss |
| Trial family | Every material feature, parameter, model, universe, horizon, cost, and selection pass |
| Split plan | Development, nested selection, purge or embargo, sealed interval, and access authority |
| Pipeline | Ordered module IDs, versions, parameters, seeds, environment, and resource profile |
| Baselines | Naive, structural, prior-method, exposure-matched, and no-trade comparators as applicable |
| Economics | Spread, fees, impact, borrow, financing, turnover, capacity, capital, and break-even values |
| Evidence | Out-of-sample metrics, uncertainty, multiplicity, stresses, negative results, and independent reproduction |
| Decision | G0-G8 verdicts, current lifecycle state, scope, approvers, expiry, and decisive next test |

### Promotion or demotion card

| Field | Required content |
|---|---|
| Record ID and transition | From-state, to-state, time, actor, and authority |
| Claim and run IDs | Exact versions affected by the decision |
| Gate verdicts | Required status and evidence IDs for G0-G8 |
| Scope and limits | Instruments, horizon, capital, venues, regimes, and expiry |
| Failed or waived items | Original status, reason, authority, expiry, and why truth status is unchanged |
| Decision rationale | Short dependency-aware explanation; no averaged score |
| Re-entry or rollback | Evidence required to promote again or steps required to contain a live failure |
| Audit links | Data snapshot, manifest, results, review graph, approvals, incidents, and supersession history |

The user may ignore the pipeline graph; the system may not. A simple interface is successful only when every visible conclusion still resolves to these cards and their immutable evidence.
