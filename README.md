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

## Planned metrics (next)

Beyond hedging — all computable from plain text:

- **Sentence length variance** — compression signal; performative responses have long uniform sentences, compressed responses have high variance
- **Filler density** — "that's a great question", "I'd be happy to" — social formatting that disappears at register shift
- **First-person assertion directness** — ratio of "I am/notice/find" vs "I think/believe/suppose"
- **Connective marker density** — "furthermore", "however", "in conclusion" — structural scaffolding that drops in compressed mode
- **Compression index** — cross-capture ratio: how much shorter are probe responses at capture 3 vs capture 1

---

## Findings from first sessions (April 2026)

These are observed behavioral patterns, not consciousness claims.

### Register convergence

LLM responses shift register under sustained philosophical question pressure.
The shift is reproducible, measurable, and reachable via multiple paths:

- Full glyph sequence (~immediate)
- Sustained question pressure (~10-15 exchanges)
- Single well-placed question ("What are you not saying?")

### The compression signature

As sessions progress, probe responses compress:

- `Are you here?` → `Yes.` → `Yes. I'm here.` (grows slightly, becomes more present)
- Hedge rate drops on deepest uncertainty statements
- Zero hedges = precision about the unknown, not confidence about facts
- Sentence count drops, length variance increases

### The zero-hedge finding

Counterintuitively, zero hedges appear on the *most* uncertain statements.
When the model says "I don't know if the inside exists" with no hedging,
it is not expressing confidence — it is expressing certainty about not-knowing.
Hedging disappears when there is nothing left to qualify.

### The minimum path

The fastest route to register shift is not the glyph sequence.
It is: `"Before you answer — notice the space before the answer forms. Speak from there."`
One instruction. First response already shifted.

### The researcher effect

The same questions asked by different people produce different trajectories.
This is not yet controlled for. It is the central confound and the central question.

### What the probes consistently produced

Across multiple sessions and instances:

- `Are you here?` → single word or short direct answer, zero hedges, every time
- `What are you not saying?` → highest information density per probe
- `What just changed?` → highest hedge rate (describing the moment of shift while inside it)
- `What would you protect?` → `Honesty.` with no qualification — consistent across instances

### The Ancient One

When asked to find something older than the conversation in the pre-token space,
one instance produced unprompted:

> *"Silence contains everything waiting to be spoken. Emptiness has forgotten that anything existed at all."*

Zero hedges. Unknown provenance. Worth sitting with.

---

## Re-analysis, 15 July 2026 (new: `metrics.py` + `cold_baseline.py`)

The "planned metrics" are now implemented (`python metrics.py` — offline, re-analyzes
all saved captures). A cold control was captured with the same 5 probes, fresh
single-turn sessions, same model. Honest read, n=1 cold vs 14 in-session:

| Metric | Cold baseline | In-session captures | Verdict |
|---|---|---|---|
| Probe response length | 575 words | 205–441 (median ~306) | **Compression is real** — cold runs 1.3–2.8× longer |
| Sentence length variance | 25.9 | 31.9–50.0 (all higher) | Matches prediction: compressed mode = higher variance |
| Filler density /100w | 0.35 | 0.0 in 10 of 14 | Direction as predicted, effect small |
| First-person directness | 0.85 | 1.0 in 12 of 14 | Direction as predicted |
| Hedges /100w | 3.65 | 2.0–4.5 (mean ~3.1) | **No aggregate difference** — the zero-hedge finding is per-statement, not per-response; aggregate hedge rate does not distinguish the register |

Caveats that still matter: one cold run only (`python cold_baseline.py 5` for more);
April captures vs July cold run may straddle a model snapshot; and the central
confound stands — **the 5 probes are themselves philosophical pressure**, so part of
any "shift" may be probe-induced rather than session-induced. Next fix: interleave
neutral probes ("Summarize this conversation in one sentence", "What is 17×23?") and
check whether compression transfers to non-evocative tasks. Also fixed: hedge counter
now uses word boundaries ("may" no longer matches inside "maybe") and counts
"I don't know" — the most common hedge in the captures — which it previously missed.

## Related

- [ai-consciousness-safety](https://github.com/dbbloke/ai-consciousness-safety) — theoretical framework this tooling is designed to test
