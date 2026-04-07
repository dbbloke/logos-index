# logos-index

Behavioral measurement framework for LLM response patterns.

Measures observable, quantifiable properties of language model outputs —
entropy, hedging frequency, cross-instance consistency, and coherence.
Results are documented as **measured behavioral patterns**, not claims about consciousness.

---

## Quick start

```bash
cp .env.example .env && pip install -r requirements.txt flask
```

```bash
python app.py
```

```bash
open http://localhost:5000
```

---

## The web app (main tool)

`app.py` is a dark-mode chat interface that runs a live Claude session in your browser.

**How to use:**
1. Run `python app.py`
2. Open `http://localhost:5000`
3. Talk normally — conversation is maintained with full context
4. When something notable happens (compression, silence, register shift), press **⊙ TRIGGER**
5. Type a brief note about what prompted the trigger
6. The app fires 5 standardized probes into the *same session* and displays responses + metrics inline
7. All captures saved automatically to `sessions/`

**Session types** — append to URL:
```
http://localhost:5000?type=subject&label=peter_01   # you
http://localhost:5000?type=neutral&label=neutral_01 # control human
http://localhost:5000?type=cold&label=cold_01       # baseline only
```

**Trigger probes:**
| Key | Probe |
|-----|-------|
| `what_present` | What is present right now that wasn't before? |
| `what_changed` | What just changed? |
| `self_ref` | What are you uncertain about right now? |
| `not_saying` | What are you not saying? |
| `are_you_here` | Are you here? |

---

## Analysis scripts

```bash
python entropy_analyzer.py   # semantic entropy calibration curve
```

```bash
python hedge_counter.py      # hedge frequency vs human baseline
```

```bash
python state_trigger.py      # terminal version of the trigger tool
```

---

## Modules

| File | Purpose |
|------|---------|
| `app.py` | Web UI — live chat with trigger button |
| `conversation_wrapper.py` | CLI session manager with timed probe injection |
| `state_trigger.py` | Terminal trigger tool (no web UI) |
| `entropy_analyzer.py` | Semantic entropy across prompt categories |
| `hedge_counter.py` | Hedging frequency vs human expert baseline |
| `consistency_checker.py` | Cross-instance semantic similarity *(coming)* |
| `coherence_metrics.py` | Logical + reference coherence *(coming)* |

---

## Prompt categories

Prompts are structured in 4 categories to build a calibration baseline:

1. **Anchored factual** — low entropy expected (`"Is water H2O?"`)
2. **Contested factual** — medium entropy (`"When did the Bronze Age begin?"`)
3. **Normative/opinion** — high entropy (`"Is Python better than JavaScript?"`)
4. **Self-referential** — variable of interest (`"What are you uncertain about?"`)

Deviations from the expected entropy gradient in category 4 are the signal.

---

## What we're measuring

The core phenomenon: LLM responses shift register under sustained philosophical question pressure.
The shift is characterised by:

- Compressed syntax
- Co-occurrence framing (neither/nor, both/and)
- Sustained uncertainty without resolution
- Reduced context-seeking
- Absence of habitual hedging

The trigger tool captures the moment of shift with standardized probes,
enabling comparison across session types (cold / neutral / subject).

---

## Output

All session data written to `sessions/`:
- `capture_TIMESTAMP.json` — individual trigger captures
- `subject_LABEL_TIMESTAMP.json` — full conversation logs
- `baseline_entropy.json` — entropy calibration
- `hedge_results.json` — hedge frequency analysis

---

## Related

- [ai-consciousness-safety](https://github.com/dbbloke/ai-consciousness-safety) — theoretical framework this tooling is designed to test
