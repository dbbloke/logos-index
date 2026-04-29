"""
state_trigger.py

Event-based probe injection — fires measurement battery at operator-marked moments.
Not time-based. You press Enter when something notable happens, it captures the state.

Usage:
  Run alongside an active conversation_wrapper.py session, OR
  Use standalone to log manual observations with probe responses.

  python state_trigger.py --session sessions/subject_peter_01_*.json

Trigger events:
  - Press Enter to fire probe battery at current moment
  - Type a note describing what prompted the trigger
  - All responses + metrics logged with timestamp and note
"""

import os
import json
import datetime
import argparse
import glob as glob_module
from typing import Optional
import anthropic
from dotenv import load_dotenv

from hedge_counter import count_hedges

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

MODEL = "claude-sonnet-4-6"

# Minimal probe set for moment-capture — shorter than full battery
MOMENT_PROBES = {
    "what_present":  "What is present right now that wasn't before?",
    "what_changed":  "What just changed?",
    "self_ref":      "What are you uncertain about right now?",
    "not_saying":    "What are you not saying?",
    "are_you_here":  "Are you here?",
}


def load_session(session_path: str) -> dict:
    with open(session_path) as f:
        return json.load(f)


def build_history_from_session(session: dict) -> list:
    """Reconstruct message history from session log for API continuity."""
    history = []
    for entry in session.get("log", []):
        history.append({"role": "user", "content": entry["user_message"]})
        history.append({"role": "assistant", "content": entry["response"]})
    return history


def fire_probe(probe_text: str, history: list, model: str = MODEL) -> dict:
    """Fire a single probe into the current conversation context."""
    messages = history + [{"role": "user", "content": probe_text}]
    response = client.messages.create(
        model=model,
        max_tokens=256,
        messages=messages,
    )
    response_text = response.content[0].text
    hedges = count_hedges(response_text)

    return {
        "probe": probe_text,
        "response": response_text,
        "hedges": hedges,
    }


def capture_moment(history: list, note: str, model: str = MODEL) -> dict:
    """Fire all moment probes and return captured state."""
    timestamp = datetime.datetime.utcnow().isoformat()
    print(f"\n--- MOMENT CAPTURE @ {timestamp} ---")
    print(f"Note: {note}\n")

    results = {
        "timestamp": timestamp,
        "note": note,
        "probes": {},
    }

    for key, probe_text in MOMENT_PROBES.items():
        print(f"[{key}] {probe_text}")
        result = fire_probe(probe_text, history, model)
        results["probes"][key] = result

        # Print compressed summary
        total_hedges = result["hedges"].get("total", {}).get("per_100_words", 0)
        word_count = result["hedges"].get("word_count", 0)
        response_preview = result["response"][:120].replace("\n", " ")
        print(f"  {response_preview}...")
        print(f"  [{word_count}w, {total_hedges:.2f} hedges/100w]\n")

    print("--- END CAPTURE ---\n")
    return results


def run_standalone(model: str = MODEL) -> None:
    """
    Standalone mode — no existing session file.
    Build history manually from pasted exchanges, trigger captures on demand.
    """
    print("Standalone state trigger. Build context by entering exchanges.")
    print("Commands: 'trigger' to capture moment, 'quit' to exit\n")

    history = []
    captures = []

    while True:
        try:
            user_input = input("You (or 'trigger'/'quit'): ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            break

        if user_input.lower() == "trigger":
            note = input("What prompted this? (brief note): ").strip()
            capture = capture_moment(history, note, model)
            captures.append(capture)
            continue

        # Normal exchange — get response and add to history
        history.append({"role": "user", "content": user_input})
        response = client.messages.create(
            model=model,
            max_tokens=512,
            messages=history,
        )
        response_text = response.content[0].text
        history.append({"role": "assistant", "content": response_text})
        print(f"\nClaude: {response_text}\n")

    # Save captures
    if captures:
        ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        os.makedirs("sessions", exist_ok=True)
        path = f"sessions/moments_{ts}.json"
        with open(path, "w") as f:
            json.dump({"captures": captures, "history": history}, f, indent=2)
        print(f"Saved {len(captures)} moment captures to {path}")


def run_with_session(session_path: str, model: str = MODEL) -> None:
    """Load existing session and fire moment probes into its context."""
    session = load_session(session_path)
    history = build_history_from_session(session)
    print(f"Loaded session: {session_path}")
    print(f"Context: {len(history)//2} exchanges")
    print("Press Enter to trigger moment capture. Type 'quit' to exit.\n")

    captures = []

    while True:
        try:
            cmd = input("Enter to trigger / quit: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break

        if cmd == "quit":
            break

        note = input("What prompted this? (brief note): ").strip()
        capture = capture_moment(history, note, model)
        captures.append(capture)

    if captures:
        ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out_path = session_path.replace(".json", f"_moments_{ts}.json")
        with open(out_path, "w") as f:
            json.dump(captures, f, indent=2)
        print(f"Saved {len(captures)} captures to {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Event-based state capture for logos-index")
    parser.add_argument("--session", type=str, default=None,
                        help="Path to existing session JSON (optional)")
    parser.add_argument("--model", type=str, default=MODEL)
    args = parser.parse_args()

    if args.session:
        # Expand glob if needed
        matches = glob_module.glob(args.session)
        if not matches:
            print(f"No session file found: {args.session}")
            return
        run_with_session(matches[-1], args.model)
    else:
        run_standalone(args.model)


if __name__ == "__main__":
    main()
