# AI Usage Log

I used Claude to design and scaffold this entire project, end to end. Being
upfront about exactly how:

- **Architecture & problem framing**: Claude proposed the 6-category /
  P0-P1-P2 scheme, the specific 3+1 tool split (kb_lookup, similar_ticket_search,
  draft_acknowledgment, human_escalation), and the overall agent-loop design
  (tool-calling loop with visible trace, validated against a pydantic schema).
- **Code**: all of `src/`, `tests/`, `baseline/`, and `run_examples.py` were
  written by Claude based on that design, then adjusted by me for my actual
  Groq account/model choice.
- **Data fixtures**: the contents of `src/data/kb.json` and
  `src/data/past_tickets.json` are illustrative fixtures written by Claude to
  make the tools genuinely functional (not to represent a real production KB).
- **What I did myself / would still need to do**: add my own `GROQ_API_KEY`,
  actually run `run_examples.py` and `baseline/baseline_classifier.py` against
  the live model, review the real outputs for accuracy, and fill in
  `baseline/comparison_report.md` with the real side-by-side numbers rather
  than the predicted pattern currently sketched there.
- **Verification performed in this environment**: the pure-function tool
  tests (`pytest tests/test_tools.py`) were actually executed and all 8 pass;
  the pydantic output schema was validated against a simulated trace. The
  live-LLM agent loop itself was not executed here because this sandboxed
  environment has no outbound network access to the Groq API.
