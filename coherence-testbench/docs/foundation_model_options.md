# Foundation Model Options for EEG Bench Rescue

**Recommendation: USE NEITHER.** Both TRIBE v2 and Brain2Qwerty are CC BY-NC 4.0 (research-only) and cannot sit on the product path. TRIBE v2 is also the wrong modality direction. Commercially-friendly alternative: **LaBraM** (MIT license, ICLR 2024 spotlight, channel-flexible EEG encoder pretrained on ~2,500 h across ~20 datasets, HuggingFace-loadable via braindecode).

---

## 1. Weights & Access

| | TRIBE v2 | Brain2Qwerty |
|---|---|---|
| Weights published? | Yes — `facebook/tribev2` on HF | **No** — v2 under embargo; only code on GitHub |
| Gated? | Open download, no gate | N/A (weights not released) |
| License | **CC BY-NC 4.0** | **CC BY-NC 4.0** |
| Commercial use? | **No** | **No** |
| Entry point | `from tribev2 import TribeModel; TribeModel.from_pretrained("facebook/tribev2")` | Custom pipeline (conv encoder → transformer → char LM); no clean frozen-encoder API |

## 2. Input Format

**TRIBE v2 is not an EEG encoder.** It maps **video + audio + text → predicted fMRI cortical response** (~20k vertices). It does not accept EEG as input at any layer. Nothing to feed BBBD signals into. Kill.

**Brain2Qwerty (EEG head):**
- Sample rate: raw 1 kHz → **downsampled to 50 Hz** (BBBD is 128 Hz — trivial resample, but note the aggressive lowpass)
- Channels: 64ch (61 EEG + 3 EOG) BrainAmp — comparable montage to BBBD's 64ch BioSemi, but not identical channel positions
- Window: **500 ms** epochs, tied to keystroke events (−200 ms to +300 ms)
- Preprocessing: bandpass **0.1–20 Hz**, baseline correction, RobustScaler
- Trained on continuous typing; no notion of "session-level attention" epochs

## 3. Integration Complexity

- **TRIBE v2**: N/A. Wrong modality.
- **Brain2Qwerty**: Multi-day even if weights existed. No documented frozen-encoder path — you'd have to fork the training code, strip the char-LM head, expose transformer hidden states, and rebuild windowing around your task boundary rather than keystrokes. And v2 checkpoints aren't public yet.

## 4. Fit to Our Task

- **Cross-subject session-level attention decoding (killed EEG bench)**: Neither helps. Brain2Qwerty's public numbers are **within-subject** (train/test split by sentence, not by participant); its 67% EEG CER is already poor on the task it was designed for, and there is no evidence of cross-subject transfer. TRIBE v2 is fMRI-only.
- **Quiz-score regression from EEG**: Same story. Brain2Qwerty's 0.1–20 Hz bandpass and 500 ms keystroke windows are structurally wrong for slow session-level cognitive-load signals.

## 5. Bottom Line

Do not integrate either. The commercially-clean move — if we're going to spend engineer-days on a foundation encoder — is **LaBraM** (MIT, 200 Hz, channel-list flexible, checkpoints released as `.pth`). Alternative candidates worth a same-day scoping call: **NeuroLM** (ICLR 2025, up to 1.7B params, ~25k h pretraining — verify license) and **BENDR** (BERT-style, clinical EEG corpus). Verify each LICENSE file directly before commitment; several EEG FMs quietly ship CC BY-NC despite MIT-style code.

**Before any integration**, decide whether the EEG bench KILL is worth rescuing with an encoder at all, or whether the eyetrack Branch-D signal (66.5% BA) is the better product line to double down on.
