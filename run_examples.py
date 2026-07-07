"""
Runs every ticket in examples/inputs.json through the triage agent and
writes one JSON file per ticket to examples/outputs/.

Usage:
    python run_examples.py
"""

import json
from pathlib import Path
from src.agent import run_triage

INPUTS_PATH = Path("examples/inputs.json")
OUTPUT_DIR = Path("examples/outputs")


def main():
    examples = json.loads(INPUTS_PATH.read_text())
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for ex in examples:
        print(f"\n--- Ticket {ex['id']:02d}: {ex['text'][:60]!r} ---")
        result = run_triage(ex["text"], ex.get("metadata", {}))
        out_path = OUTPUT_DIR / f"output_{ex['id']:02d}.json"
        out_path.write_text(json.dumps(result, indent=2))
        print(f"  -> category={result['category']}  priority={result['priority']}  "
              f"next_tool={result['next_tool']}  confidence={result['confidence']}")

    print(f"\nDone. Wrote {len(examples)} outputs to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
