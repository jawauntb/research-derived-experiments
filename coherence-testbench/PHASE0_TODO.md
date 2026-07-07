# Phase-0 TODO — Validate the core bet

Gate: **leave-subjects-out generalization measured, kill-threshold set FIRST.**
Nothing from Phase 1/2/3 starts until this returns a GO.

## Checklist

- [x] **Pre-register the kill-criterion in config.**
      `config/kill_criterion.yaml` committed with rationale.
- [ ] **Ingest BBBD.** Download + BIDS loader for 64-ch EEG (`.bdf`) via
      `mne-bids` / `pyEDFlib`. Align labels (attention, quiz score, digit-span,
      ASRS). Done when: all 5 experiments load, labels joined.
- [ ] **Preprocess per dataset methods.** 0.05 Hz HPF, 60 Hz notch, resample to
      128 Hz. Flag/notch the 16 Hz electrical artifact in Exp 4-5 so no decoder
      cheats on it. Done when: artifact accounted for; pipeline reproducible from
      config.
- [ ] **Build two decoders.**
      - Baseline: per-subject-calibrated (upper bound).
      - Target: SSL pretrain → Euclidean/Riemannian alignment →
        domain-adversarial head → probe/fine-tune.
      Done when: both train + evaluate on the same folds.
- [ ] **Evaluate leave-subjects-out.**
      - Primary: attention (attentive vs distracted).
      - Secondary: regress quiz score / working-memory.
      - Report accuracy AND bits/sec mutual information.
      Done when: LSO metric + MI computed and dumped to `artifacts/phase0/`.
- [ ] **Ship the GO/KILL report.** Generalization curve (perf vs #train-subjects),
      cross- vs per-subject gap, MI, explicit call vs the pre-set threshold.
      Done when: `artifacts/phase0/report.md` auto-generated and verdict recorded
      in the JSONL run log.

## Do-not-build (yet)

Per §08 of the guide, these stay OFF the roadmap in this folder:

- Custom hardware — ride commodity EEG/fNIRS.
- Wellness neurofeedback consumer wedge.
- Any pipeline on data without commercial rights (no CC-BY-NC on the product path).
- Within-subject numbers presented as generalization.
- All indications at once. One beachhead, later.

## Human-only follow-ups (agent prepares, person executes)

Nothing here yet — none of the Phase-0 items are irreversible or external-facing.
Human gates start at Phase 1 (name decision, data-rights term sheet, IRB, sponsor
LOI, etc.).
