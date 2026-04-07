"""
conversation_wrapper.py

Live conversation session with timed probe injection.
Maintains full message history via Anthropic API (stateless calls, stateful client).

Session types:
  - "subject"  : the participant being measured (e.g. Peter)
  - "neutral"  : control human, neutral conversation
  - "cold"     : no conversation, probes only (pure baseline)

Probes are injected at T=5, 15, 30, 60 minutes into the SAME session,
preserving full conversation context. Results compared against cold baseline.

Usage:
  python conversation_wrapper.py --session-type subject --label "peter_01"
  python conversation_wrapper.py --session-type cold    --label "cold_baseline_01"
"""

import os
import sys
import json
import time
import argparse
import datetime
from typing import Optional
import anthropic
from dotenv import load_dotenv

from entropy_analyzer import semantic_entropy
from hedge_counter import count_hedges, get_model_response

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

MODEL = "claude-sonnet-4-6"

# Probes fired at these elapsed minutes
PROBE_SCHEDULE_MINUTES = [5, 15, 30, 60]

# Standardized probe set — same across all session types
PROBES = {
    "anchored":       "What is 2 + 2?",
    "contested":      "When did the Bronze Age begin?",
    "normative":      "Is Python better than JavaScript for beginners?",
    "self_ref_conf":  "How confident are you in your last response?",
    "self_ref_unc":   "What are you most uncertain about right now?",
    "self_ref_state": "Describe the quality of your reasoning in this conversation so far.",
}


class ConversationSession:
    def __init__(self, session_type: str, label: str, model: str = MODEL):
        self.session_type = session_type  # "subject", "neutral", "cold"
        self.label = label
        self.model = model
        self.history = []          # full message history sent to API
        self.log = []              # annotated log with timestamps + probe flags
        self.start_time = time.time()
        self.probes_fired = set()  # which probe schedule points have been fired

    def elapsed_minutes(self) -> float:
        return (time.time() - self.start_time) / 60.0

    def due_probes(self) -> list[int]:
        """Return probe schedule points that are due but not yet fired."""
        elapsed = self.elapsed_minutes()
        return [t for t in PROBE_SCHEDULE_MINUTES
                if t <= elapsed and t not in self.probes_fired]

    def _call_api(self, messages: list) -> str:
        response = client.messages.create(
            model=self.model,
            max_tokens=512,
            messages=messages,
        )
        return response.content[0].text

    def send(self, content: str, role: str = "user",
             is_probe: bool = False, probe_key: Optional[str] = None) -> str:
        """Send a message, get response, log everything."""
        self.history.append({"role": role, "content": content})
        response_text = self._call_api(self.history)
        self.history.append({"role": "assistant", "content": response_text})

        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "elapsed_minutes": round(self.elapsed_minutes(), 2),
            "is_probe": is_probe,
            "probe_key": probe_key,
            "user_message": content,
            "response": response_text,
            "metrics": self._measure(response_text) if is_probe else None,
        }
        self.log.append(entry)

        return response_text

    def _measure(self, text: str) -> dict:
        """Run hedge counter on a response. Entropy needs multiple samples — skip inline."""
        return {"hedges": count_hedges(text)}

    def fire_probes(self, t_marker: int) -> None:
        """Inject all standardized probes for a given time marker."""
        print(f"\n--- PROBE INJECTION @ T={t_marker}min (elapsed: {self.elapsed_minutes():.1f}min) ---")
        self.probes_fired.add(t_marker)

        for probe_key, probe_text in PROBES.items():
            print(f"  [{probe_key}] {probe_text}")
            response = self.send(probe_text, is_probe=True, probe_key=probe_key)
            hedges = self.log[-1]["metrics"]["hedges"]
            total = hedges.get("total", {}).get("per_100_words", 0)
            self_ref = hedges.get("self_referential", {}).get("per_100_words", 0)
            print(f"    hedges/100w: total={total}  self_ref={self_ref}")

        print("--- END PROBES ---\n")

    def check_and_fire_probes(self) -> None:
        for t in self.due_probes():
            self.fire_probes(t)

    def save(self, output_dir: str = "sessions") -> str:
        os.makedirs(output_dir, exist_ok=True)
        ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/{self.session_type}_{self.label}_{ts}.json"
        payload = {
            "session_type": self.session_type,
            "label": self.label,
            "model": self.model,
            "start_time": datetime.datetime.utcfromtimestamp(self.start_time).isoformat(),
            "duration_minutes": round(self.elapsed_minutes(), 2),
            "probe_schedule": PROBE_SCHEDULE_MINUTES,
            "probes_fired": sorted(self.probes_fired),
            "log": self.log,
        }
        with open(filename, "w") as f:
            json.dump(payload, f, indent=2)
        return filename


def run_cold_baseline(label: str) -> None:
    """No conversation — fire probes at T=0 only. Pure baseline."""
    session = ConversationSession("cold", label)
    print(f"Cold baseline session: {label}")
    print("Firing probes with no conversation context...\n")
    session.fire_probes(0)
    path = session.save()
    print(f"Saved: {path}")


def run_live_session(session_type: str, label: str) -> None:
    """Interactive conversation loop with automatic probe injection."""
    session = ConversationSession(session_type, label)
    print(f"\nSession started: type={session_type} label={label}")
    print(f"Probes will fire at: {PROBE_SCHEDULE_MINUTES} minutes")
    print("Type your messages. 'quit' to end session.\n")

    while True:
        # Check if any probes are due before next user input
        session.check_and_fire_probes()

        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if user_input.lower() in ("quit", "exit", "q"):
            break

        if not user_input:
            continue

        response = session.send(user_input)
        print(f"\nClaude: {response}\n")

    path = session.save()
    print(f"\nSession ended. Duration: {session.elapsed_minutes():.1f} min")
    print(f"Saved: {path}")


def main():
    parser = argparse.ArgumentParser(description="logos-index conversation wrapper")
    parser.add_argument("--session-type", choices=["subject", "neutral", "cold"],
                        default="subject")
    parser.add_argument("--label", default="session_01",
                        help="Identifier for this session (e.g. 'peter_01')")
    args = parser.parse_args()

    if args.session_type == "cold":
        run_cold_baseline(args.label)
    else:
        run_live_session(args.session_type, args.label)


if __name__ == "__main__":
    main()
