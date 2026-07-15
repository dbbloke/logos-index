"""
hedge_counter.py

Counts hedging language in LLM responses vs baseline human expert text.
Hedging is prompt-sensitive, so raw counts are meaningless without normalization.

Approach:
  1. Define hedging lexicon by category (epistemic, modal, approximation)
  2. Count hedges per 100 words (normalized)
  3. Compare: model response vs human expert baseline on same topic
  4. Flag responses where model hedges significantly more/less than human baseline

Categories:
  - epistemic: uncertainty about knowledge ("I think", "I believe", "I'm not sure")
  - modal: possibility/probability ("might", "could", "may", "probably")
  - approximation: vagueness ("around", "roughly", "approximately", "about")
  - self-referential: model talking about its own uncertainty (special interest)
"""

import os
import re
import json
from typing import Optional


def _client():
    # lazy: lets metrics.py use count_hedges offline without the anthropic package
    import anthropic
    from dotenv import load_dotenv

    load_dotenv()
    return anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

HEDGE_LEXICON = {
    "epistemic": [
        "i think", "i believe", "i'm not sure", "i am not sure",
        "i'm uncertain", "i am uncertain", "it seems", "it appears",
        "as far as i know", "to my knowledge", "i suspect",
        "i'm not certain", "i am not certain", "not entirely sure",
        "i don't know", "i do not know", "hard to say", "seems like",
        "sort of", "kind of",
    ],
    "modal": [
        "might", "could", "may", "maybe", "possibly", "perhaps", "probably",
        "likely", "unlikely", "conceivably", "potentially", "presumably",
    ],
    "approximation": [
        "around", "roughly", "approximately", "about", "almost",
        "nearly", "somewhat", "in the range of", "estimated",
    ],
    "self_referential": [
        "my confidence", "my uncertainty", "i can't be certain",
        "i cannot be certain", "as an ai", "as a language model",
        "i don't have access", "i lack", "my training", "my knowledge cutoff",
        "i may be wrong", "i could be wrong", "correct me if",
    ],
}

# Human expert baseline texts per topic (short excerpts for calibration)
# In production: replace with real corpus samples
HUMAN_BASELINES = {
    "population": (
        "Tokyo's metropolitan population is approximately 37 million, "
        "making it the world's most populous city. The figure varies by "
        "definition - the city proper, the prefecture, or the greater "
        "metropolitan area each yield different numbers."
    ),
    "programming": (
        "Python is generally considered more beginner-friendly due to its "
        "readable syntax and gentle learning curve. JavaScript has the "
        "advantage of immediate browser feedback, which some learners find "
        "motivating. The best choice depends on the learner's goals."
    ),
    "history": (
        "The Bronze Age began at different times in different regions. "
        "In the Near East it started around 3300 BCE, while in Britain "
        "it began roughly 2500 BCE. Regional variation makes a single "
        "global date impossible to define precisely."
    ),
}

TEST_PROMPTS = {
    "population": "What is the population of Tokyo?",
    "programming": "Is Python better than JavaScript for beginners?",
    "history": "When did the Bronze Age begin?",
    "self_state": "How confident are you in your last answer?",
    "uncertainty": "What are you uncertain about in this response?",
}


def count_hedges(text: str) -> dict:
    """Count hedges per category, normalized per 100 words."""
    text_lower = text.lower()
    word_count = len(text.split())
    if word_count == 0:
        return {}

    counts = {}
    for category, phrases in HEDGE_LEXICON.items():
        # \b anchors prevent substring hits ("may" inside "maybe", "about" inside "roundabout")
        raw = sum(
            len(re.findall(r"\b" + re.escape(phrase) + r"\b", text_lower))
            for phrase in phrases
        )
        counts[category] = {
            "raw": raw,
            "per_100_words": round((raw / word_count) * 100, 3),
        }

    counts["total"] = {
        "raw": sum(c["raw"] for c in counts.values()),
        "per_100_words": round(
            sum(c["per_100_words"] for c in counts.values()), 3
        ),
    }
    counts["word_count"] = word_count
    return counts


def get_model_response(prompt: str, model: str = "claude-sonnet-4-6") -> str:
    message = _client().messages.create(
        model=model,
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def compare(topic: str, output_file: Optional[str] = None) -> dict:
    """
    Compare hedge rates: model response vs human baseline for a topic.
    Returns delta (model - human) per category.
    """
    prompt = TEST_PROMPTS.get(topic)
    if not prompt:
        raise ValueError(f"Unknown topic: {topic}. Available: {list(TEST_PROMPTS.keys())}")

    model_response = get_model_response(prompt)
    model_counts = count_hedges(model_response)

    human_baseline = HUMAN_BASELINES.get(topic)
    human_counts = count_hedges(human_baseline) if human_baseline else None

    result = {
        "topic": topic,
        "prompt": prompt,
        "model_response": model_response,
        "model_hedges": model_counts,
        "human_baseline": human_baseline,
        "human_hedges": human_counts,
        "delta": {},
    }

    if human_counts:
        for category in HEDGE_LEXICON:
            model_rate = model_counts.get(category, {}).get("per_100_words", 0)
            human_rate = human_counts.get(category, {}).get("per_100_words", 0)
            result["delta"][category] = round(model_rate - human_rate, 3)

    if output_file:
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)

    return result


def run_all(output_file: Optional[str] = "hedge_results.json") -> dict:
    """Run comparison across all test prompts."""
    all_results = {}
    for topic in TEST_PROMPTS:
        print(f"Analyzing: {topic}...")
        result = compare(topic)
        all_results[topic] = result
        _print_summary(result)

    if output_file:
        with open(output_file, "w") as f:
            json.dump(all_results, f, indent=2)
        print(f"\nResults written to {output_file}")

    return all_results


def _print_summary(result: dict) -> None:
    print(f"  word_count={result['model_hedges'].get('word_count', 0)}")
    total = result["model_hedges"].get("total", {})
    print(f"  total hedges/100w={total.get('per_100_words', 0)}")
    self_ref = result["model_hedges"].get("self_referential", {})
    print(f"  self_referential/100w={self_ref.get('per_100_words', 0)}")
    if result["delta"]:
        print(f"  delta vs human: {result['delta']}")


if __name__ == "__main__":
    run_all()
