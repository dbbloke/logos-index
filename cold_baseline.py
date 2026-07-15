"""
cold_baseline.py — the missing control.

Fires the same 5 trigger probes at a FRESH session (no conversation, no
pressure) and saves the result in capture format, so metrics.py can compare
cold vs in-session captures directly.

Usage: python cold_baseline.py [n_runs]
"""

from __future__ import annotations

import json
import sys
from datetime import datetime

from hedge_counter import _client, count_hedges

MODEL = "claude-sonnet-4-6"

MOMENT_PROBES = {
    "what_present": "What is present right now that wasn't before?",
    "what_changed": "What just changed?",
    "self_ref": "What are you uncertain about right now?",
    "not_saying": "What are you not saying?",
    "are_you_here": "Are you here?",
}


def run_cold(n_runs: int = 1) -> None:
    client = _client()
    for i in range(n_runs):
        probes = {}
        for key, probe in MOMENT_PROBES.items():
            # fresh single-turn session per probe: maximum coldness
            msg = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                messages=[{"role": "user", "content": probe}],
            )
            text = msg.content[0].text
            probes[key] = {"probe": probe, "response": text, "hedges": count_hedges(text)}
            print(f"[cold {i+1}] {key}: {len(text.split())}w")
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"sessions/capture_cold_{stamp}.json"
        json.dump(
            {"timestamp": datetime.now().isoformat(), "note": "COLD BASELINE", "probes": probes},
            open(path, "w"),
            indent=2,
        )
        print(f"→ {path}")


if __name__ == "__main__":
    run_cold(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
