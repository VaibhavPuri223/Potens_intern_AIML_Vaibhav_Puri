# Agent vs Baseline — Comparison Report

Run both of these first, then fill in the table below:

```
python run_examples.py                  # writes examples/outputs/output_XX.json
python -m baseline.baseline_classifier  # writes baseline/outputs/baseline_XX.json
```

## Results table

| # | Ticket (truncated) | Agent category / priority | Baseline category / priority | Agreement? | Notes |
|---|---|---|---|---|---|
| 1 | Charged twice this month... | | | | |
| 2 | App crashes on export... | | | | |
| 3 | Can't log in after reset... | | | | |
| 4 | Add dark mode... | | | | |
| 5 | Third outage this month... | | | | |
| 6 | Change billing address... | | | | |
| 7 | Production data disappeared... | | | | |
| 8 | Dashboard looks great... | | | | |
| 9 | 500 error on checkout... | | | | |
| 10 | Account locked, need demo... | | | | |
| 11 | asdf thing broken idk... | | | | |
| 12 | Bulk export for compliance... | | | | |

## Where they disagree, and why

Expected pattern (verify against your actual run):

- **Ticket 5 (recurring outage complaint):** the agent should call
  `similar_ticket_search`, find the recurring-outage precedent (T-1003/T-1004),
  and bump this to `Complaint & Escalation / P0`. The baseline has no access to
  ticket history, so it likely under-prioritizes this as a one-off `Technical
  Issue / P1`.
- **Ticket 7 (data "disappeared"):** the agent should call `kb_lookup`, find
  KB-006 (data isn't actually lost, it's a filter defaulting issue), and can
  therefore give a more accurate `why` explanation and potentially avoid an
  unnecessary P0 panic-escalation. The baseline, working from text alone, has
  to take "our production data disappeared" at face value and will likely
  over-escalate to P0 without the nuance.
- **Ticket 11 (ambiguous/garbled):** the agent's tool results come back empty
  (no KB match, no similar tickets), which should push its confidence below
  the 0.55 threshold and trigger `human_escalation`. The baseline has no
  escalation mechanism at all -- it will force a guess into one of the six
  categories regardless of confidence.

## Summary

Fill in after running:
- Agreement rate: __ / 12
- Cases where tool-backed evidence changed the outcome: __
- Cases where the baseline's guess was arguably wrong due to lack of context: __
