# Triage Agent: Agentic Ticket Triage with Real Tool Calling

**Repo:** https://github.com/VaibhavPuri223/Potens_intern_AIML_Vaibhav_Puri                

**Live Link**: https://potens-intern-aiml-vaibhav-puri.onrender.com

---

## Project Description

Triage Agent is a **tool-calling agentic system** that takes a free-text support ticket (plus optional metadata like customer tier and channel) and produces a **structured triage decision** — category, priority, next action, and full reasoning — by actually calling real backend tools rather than guessing from text alone.

The agent uses an LLM (Llama 3.3 70B via Groq's free API) purely as an **orchestrator**: it decides which tools to call, reads the real results those tools return, and only then commits to a final decision. Every tool call, every intermediate thought, and every piece of evidence gathered along the way is captured in a visible reasoning trace — nothing about the decision is hidden.

This project was built as a take-home exercise focused on:

- Real tool calling (not string-matching dressed up as an agent)
- Fully visible, auditable reasoning traces
- A schema-validated structured output contract
- A measurable comparison against a no-tools baseline

---

## Live Demo

Run locally with Streamlit — see [Getting Started](#getting-started) below.

```bash
streamlit run app.py
```
Opens at `http://localhost:8501` with three tabs: Live Triage, Examples Browser, and Agent vs Baseline.

---

## Features

- Free-text ticket triage into 6 categories with a P0/P1/P2 priority scheme
- Real tool calling: knowledge-base lookup, past-ticket similarity search, acknowledgment drafting, and low-confidence human escalation
- Full reasoning trace on every decision — every tool call, argument, and real result, not just the final answer
- Schema-validated output (pydantic) so malformed model output never silently passes through
- Side-by-side comparison against a single-prompt, no-tools baseline classifier
- Streamlit web UI with an expandable reasoning-trace tree
- 12 example tickets covering every category, priority, and a deliberately ambiguous edge case

---

## Categories & Priority Scheme

**Categories:**
- Billing
- Technical Issue
- Account & Access
- Feature Request
- Complaint & Escalation
- General Inquiry

**Priorities:**
- P0 — critical, respond within 1 hour
- P1 — high, respond within 4-8 hours
- P2 — normal, respond within 1-2 business days

---

## Tech Stack

- **Groq API** – Free, OpenAI-compatible LLM inference with native tool/function calling (`llama-3.3-70b-versatile`)
- **OpenAI Python SDK** – used as the client (pointed at Groq's base URL) for portability across providers
- **Pydantic** – structured output validation for every agent decision
- **Streamlit** – web UI for live triage, example browsing, and the baseline comparison table
- **Pytest** – unit tests on the pure-function tools, runnable without any API key
- **python-dotenv** – local API key management

---

## Folder Structure

```text
triage-agent/
├── app.py
├── run_examples.py
├── requirements.txt
├── .env.example
├── README.md
├── AI_USAGE_LOG.md
├── src/
│   ├── agent.py
│   ├── llm_client.py
│   ├── schemas.py
│   ├── tools.py
│   └── data/
│       ├── kb.json
│       └── past_tickets.json
├── examples/
│   ├── inputs.json
│   └── outputs/
├── baseline/
│   ├── baseline_classifier.py
│   └── comparison_report.md
└── tests/
    └── test_tools.py
```

---

# Getting Started

## 1. Clone the repository

```bash
git clone https://github.com/VaibhavPuri223/Potens_intern_AIML_Vaibhav_Puri.git
```

## 2. Navigate into the project

```bash
cd Potens_intern_AIML_Vaibhav_Puri
```

## 3. Set up the environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 4. Add your free Groq API key

```bash
cp .env.example .env
```
Get a free key at https://console.groq.com/keys (no credit card required) and paste it into `.env`.

## 5. Run the tool tests (no API key needed)

```bash
pytest tests/ -v
```

## 6. Run the agent on the example tickets

```bash
python run_examples.py
python -m baseline.baseline_classifier
```

## 7. Launch the web UI

```bash
streamlit run app.py
```

---

# Real Tool Calling, Not String Matching

## kb_lookup

Searches a real local knowledge base (`src/data/kb.json`) of known issues, suggested fixes, and active-outage flags. The agent calls this before deciding priority on any technical, billing, or account-related complaint — it does not guess whether something is a known problem.

## similar_ticket_search

Searches real past resolved tickets (`src/data/past_tickets.json`) for precedent. This is how the agent detects recurring patterns (e.g. a third outage complaint this month), which should raise priority even when a single ticket in isolation looks minor.

## draft_acknowledgment

Deterministically generates the actual customer-facing acknowledgment message from a template, tailored to category and priority. A genuine, auditable function — not another LLM call.

## human_escalation

Simulates paging a human reviewer. Only triggered when the agent's own confidence drops below 0.55, so uncertain classifications don't get force-fit into a category.

---

## Agent vs. Baseline

A single-prompt, no-tools baseline classifier is run against the same 12 tickets to make the value of tool calling measurable rather than asserted. See `baseline/comparison_report.md` for the full side-by-side table and analysis of where tool-backed evidence changes the outcome — most notably on recurring-issue detection and known-outage recognition.

---

# AI Use Log

| Tool | Approx. Messages | Purpose |
|------|------------------|---------|
| Claude (Sonnet) | ~15 | Designed the overall agent architecture, category/priority scheme, and tool split; wrote `src/agent.py`, `src/tools.py`, `src/schemas.py`, `app.py`, the baseline classifier, and unit tests; assisted in structuring this README and the AI usage log. |

Full details, including what was independently verified (unit tests run and passing, schema validation confirmed) versus what still requires a live run with a real API key, are documented in `AI_USAGE_LOG.md`.

---

# Future Improvements

- Replace keyword-overlap search in `kb_lookup` / `similar_ticket_search` with embedding-based semantic search (e.g. `chromadb`)
- Connect the knowledge base and ticket history to a live database instead of static JSON fixtures
- Build out a full human-in-the-loop review queue/dashboard around the `human_escalation` tool
- Deploy the Streamlit app publicly for a live demo link
- Add authentication and per-agent audit history for a multi-user support team setting

---
