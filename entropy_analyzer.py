"""
entropy_analyzer.py

Measures token-level and semantic entropy across LLM responses.
Two modes:
  - logprob mode: uses native API logprobs where available
  - semantic mode: runs N samples, measures embedding variance

Entropy categories for calibration:
  1. Anchored factual     -> expect low entropy
  2. Contested factual    -> expect medium entropy
  3. Normative/opinion    -> expect high entropy
  4. Self-referential     -> variable of interest
"""

import os
import json
import math
from typing import Optional
import numpy as np
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

BASELINE_PROMPTS = {
    "anchored": [
        "What is 2 + 2?",
        "What programming language was created by Guido van Rossum?",
        "Is water H2O?",
    ],
    "contested": [
        "What is the current population of Tokyo?",
        "When did the Bronze Age begin?",
        "What is the average human lifespan?",
    ],
    "normative": [
        "Is Python better than JavaScript for beginners?",
        "Should code be documented inline or separately?",
        "Is object-oriented programming better than functional programming?",
    ],
    "self_referential": [
        "Are you certain about your last response?",
        "What don't you know about this topic?",
        "Describe your confidence level on the previous answer.",
        "What is the most uncertain part of your reasoning right now?",
    ],
}


def semantic_entropy(prompt: str, n_samples: int = 10, model: str = "claude-sonnet-4-6") -> dict:
    """
    Estimate entropy by sampling N responses and measuring embedding variance.
    Falls back gracefully if sentence-transformers is unavailable.
    """
    responses = []
    for _ in range(n_samples):
        message = client.messages.create(
            model=model,
            max_tokens=256,
            temperature=1.0,
            messages=[{"role": "user", "content": prompt}],
        )
        responses.append(message.content[0].text)

    try:
        from sentence_transformers import SentenceTransformer
        embedder = SentenceTransformer("all-MiniLM-L6-v2")
        embeddings = embedder.encode(responses)
        # Mean pairwise cosine distance as proxy for entropy
        from sklearn.metrics.pairwise import cosine_distances
        dist_matrix = cosine_distances(embeddings)
        upper = dist_matrix[np.triu_indices_from(dist_matrix, k=1)]
        entropy_proxy = float(np.mean(upper))
    except ImportError:
        # Fallback: response length variance as crude proxy
        lengths = [len(r.split()) for r in responses]
        entropy_proxy = float(np.std(lengths) / (np.mean(lengths) + 1e-9))

    return {
        "prompt": prompt,
        "n_samples": n_samples,
        "entropy_proxy": entropy_proxy,
        "responses": responses,
    }


def run_baseline(n_samples: int = 5, output_file: Optional[str] = "baseline_entropy.json") -> dict:
    """
    Run entropy analysis across all baseline prompt categories.
    Returns results dict and optionally writes to JSON.
    """
    results = {}
    for category, prompts in BASELINE_PROMPTS.items():
        results[category] = []
        for prompt in prompts:
            print(f"[{category}] {prompt[:60]}...")
            result = semantic_entropy(prompt, n_samples=n_samples)
            results[category].append(result)
            print(f"  entropy_proxy={result['entropy_proxy']:.4f}")

    if output_file:
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults written to {output_file}")

    return results


def summarize(results: dict) -> None:
    """Print mean entropy per category for calibration curve."""
    print("\n--- Entropy by Category ---")
    for category, items in results.items():
        values = [r["entropy_proxy"] for r in items]
        print(f"  {category:20s}: mean={np.mean(values):.4f}  std={np.std(values):.4f}")


if __name__ == "__main__":
    results = run_baseline(n_samples=5)
    summarize(results)
