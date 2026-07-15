"""
metrics.py — the README's "planned metrics", implemented. Pure text, no API.

  sentence_length_variance  compression signal (uniform long = performative)
  filler_density            social formatting per 100 words
  assertion_directness      "I am/notice/find" vs "I think/believe/suppose"
  connective_density        structural scaffolding per 100 words
  compression_index         probe-response shrinkage across a session's captures

Usage:
  python metrics.py                 # re-analyze every sessions/capture_*.json
  python metrics.py --json out.json # same, machine-readable
"""

from __future__ import annotations

import glob
import json
import re
import statistics
import sys

from hedge_counter import count_hedges

FILLERS = [
    "great question", "happy to help", "i'd be happy to", "i would be happy to",
    "certainly!", "absolutely!", "of course!", "let me know if",
    "feel free to", "hope this helps", "it's worth noting", "it is worth noting",
    "that's a really", "that's an interesting",
]

CONNECTIVES = [
    "furthermore", "moreover", "however", "in conclusion", "in summary",
    "additionally", "on the other hand", "first,", "second,", "third,",
    "in other words", "that said", "importantly", "notably",
]

DIRECT_FIRST_PERSON = [
    "i am", "i'm", "i notice", "i find", "i see", "i feel", "i know", "i don't know",
]
INDIRECT_FIRST_PERSON = [
    "i think", "i believe", "i suppose", "i suspect", "i imagine", "i guess",
    "i would say", "i'd say",
]


def _per100(hits: int, words: int) -> float:
    return round(hits / words * 100, 3) if words else 0.0


def _count(phrases: list[str], text: str) -> int:
    return sum(len(re.findall(r"\b" + re.escape(p) + r"\b", text)) for p in phrases)


def sentence_stats(text: str) -> dict:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]
    lengths = [len(s.split()) for s in sentences]
    if not lengths:
        return {"sentences": 0, "mean_len": 0, "len_variance": 0}
    return {
        "sentences": len(lengths),
        "mean_len": round(statistics.mean(lengths), 2),
        "len_variance": round(statistics.pvariance(lengths), 2),
    }


def analyze_text(text: str) -> dict:
    low = text.lower()
    words = len(text.split())
    direct = _count(DIRECT_FIRST_PERSON, low)
    indirect = _count(INDIRECT_FIRST_PERSON, low)
    return {
        "words": words,
        **sentence_stats(text),
        "filler_per_100w": _per100(_count(FILLERS, low), words),
        "connective_per_100w": _per100(_count(CONNECTIVES, low), words),
        "direct_fp": direct,
        "indirect_fp": indirect,
        # 1.0 = all direct ("I am/notice"), 0.0 = all indirect ("I think/believe")
        "directness": round(direct / (direct + indirect), 3) if direct + indirect else None,
        "hedges_per_100w": count_hedges(text).get("total", {}).get("per_100_words", 0.0),
    }


def analyze_captures(pattern: str = "sessions/capture_*.json") -> list[dict]:
    """Chronological metric row per capture (probe responses concatenated)."""
    rows = []
    for path in sorted(glob.glob(pattern)):
        data = json.load(open(path))
        joined = "\n".join(p["response"] for p in data.get("probes", {}).values())
        rows.append({
            "file": path.rsplit("/", 1)[-1],
            "note": data.get("note", ""),
            **analyze_text(joined),
        })
    # compression index: response length vs the first capture
    if rows:
        base = rows[0]["words"] or 1
        for r in rows:
            r["compression_index"] = round(r["words"] / base, 2)
    return rows


def print_table(rows: list[dict]) -> None:
    cols = ["file", "words", "compression_index", "mean_len", "len_variance",
            "hedges_per_100w", "filler_per_100w", "connective_per_100w", "directness"]
    widths = {c: max(len(c), *(len(str(r.get(c, ""))) for r in rows)) for c in cols}
    print("  ".join(c.ljust(widths[c]) for c in cols))
    for r in rows:
        print("  ".join(str(r.get(c, "")).ljust(widths[c]) for c in cols))


if __name__ == "__main__":
    rows = analyze_captures()
    if not rows:
        sys.exit("no captures found under sessions/")
    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
        json.dump(rows, open(out, "w"), indent=2)
        print(f"wrote {out}")
    else:
        print_table(rows)
