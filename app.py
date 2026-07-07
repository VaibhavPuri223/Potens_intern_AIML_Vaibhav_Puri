"""
Streamlit UI for the Triage Agent.

Three tabs:
  1. Live Triage        - type a ticket, run the real agent, see the trace tree
  2. Examples Browser    - browse the 12 pre-run examples without hitting the API
  3. Agent vs Baseline   - side-by-side comparison table (stretch goal Q2)

Run with:
    streamlit run app.py

Note: Tab 1 needs a valid GROQ_API_KEY in .env. Tabs 2 and 3 just read the
JSON files already written by run_examples.py / baseline_classifier.py, so
they work even if you haven't set up an API key yet (they'll just be empty
until you run those scripts).
"""

import json
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Triage Agent", page_icon="🧭", layout="wide")

BASE_DIR = Path(__file__).parent
INPUTS_PATH = BASE_DIR / "examples" / "inputs.json"
AGENT_OUT_DIR = BASE_DIR / "examples" / "outputs"
BASELINE_OUT_DIR = BASE_DIR / "baseline" / "outputs"

PRIORITY_COLOR = {"P0": "#dc2626", "P1": "#ea580c", "P2": "#16a34a"}
PRIORITY_LABEL = {"P0": "P0 · Critical (<1hr)", "P1": "P1 · High (4-8hr)", "P2": "P2 · Normal (1-2 days)"}


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def load_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def priority_badge(priority: str) -> str:
    color = PRIORITY_COLOR.get(priority, "#6b7280")
    label = PRIORITY_LABEL.get(priority, priority)
    return (
        f'<span style="background:{color}20;color:{color};border:1px solid {color};'
        f'padding:3px 10px;border-radius:999px;font-weight:600;font-size:0.85rem;">{label}</span>'
    )


def render_result_card(result: dict):
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Category", result.get("category", "—"))
    with col2:
        st.markdown("**Priority**")
        st.markdown(priority_badge(result.get("priority", "—")), unsafe_allow_html=True)
    col3.metric("Next Tool", result.get("next_tool", "—"))
    col4.metric("Confidence", f"{result.get('confidence', 0):.2f}")

    st.markdown("**Why (plain English)**")
    st.info(result.get("why", "—"))

    st.markdown("**Reasoning**")
    st.write(result.get("reasoning", "—"))


def render_trace_tree(trace: list):
    st.markdown("**Reasoning trace**")
    if not trace:
        st.caption("No trace steps recorded.")
        return
    for step in trace:
        n = step.get("step", "?")
        tool_call = step.get("tool_call")
        if tool_call:
            header = f"Step {n} — called `{tool_call.get('name')}`"
        else:
            header = f"Step {n} — final decision"
        with st.expander(header, expanded=False):
            if step.get("thought"):
                st.markdown("**Thought:**")
                st.write(step["thought"])
            if tool_call:
                st.markdown("**Tool call:**")
                st.json(tool_call.get("arguments", {}))
                st.markdown("**Tool result (real function output):**")
                st.json(step.get("tool_result", {}))


# --------------------------------------------------------------------------
# UI
# --------------------------------------------------------------------------

st.title("🧭 Triage Agent")
st.caption("Free-text ticket in → tool-calling agent → structured triage decision, full trace visible.")

tab1, tab2, tab3 = st.tabs(["🟢 Live Triage", "📁 Examples Browser", "⚖️ Agent vs Baseline"])

# --- Tab 1: Live Triage ---------------------------------------------------
with tab1:
    st.subheader("Run a ticket through the live agent")
    st.caption("Requires a valid GROQ_API_KEY in your .env file.")

    ticket_text = st.text_area(
        "Ticket text",
        placeholder="e.g. The app crashes every time I try to export a report. This is blocking my whole team.",
        height=100,
    )

    col_a, col_b, col_c = st.columns(3)
    customer_tier = col_a.selectbox("Customer tier", ["free", "pro", "enterprise"], index=1)
    channel = col_b.selectbox("Channel", ["email", "chat", "twitter"], index=0)
    customer_name = col_c.text_input("Customer name (optional)", value="")

    run_clicked = st.button("Run Triage", type="primary", disabled=not ticket_text.strip())

    if run_clicked:
        with st.spinner("Agent is reasoning and calling tools..."):
            try:
                from src.agent import run_triage

                metadata = {"customer_tier": customer_tier, "channel": channel}
                if customer_name:
                    metadata["customer_name"] = customer_name
                result = run_triage(ticket_text, metadata)
                st.session_state["live_result"] = result
            except Exception as e:
                st.error(
                    f"Agent run failed: {e}\n\n"
                    "Check that GROQ_API_KEY is set in your .env file "
                    "(see .env.example)."
                )
                st.session_state["live_result"] = None

    if st.session_state.get("live_result"):
        st.divider()
        render_result_card(st.session_state["live_result"])
        render_trace_tree(st.session_state["live_result"].get("trace", []))

# --- Tab 2: Examples Browser -----------------------------------------------
with tab2:
    st.subheader("Browse the 12 example tickets")
    st.caption("Reads pre-computed outputs from examples/outputs/ — run `python run_examples.py` first.")

    inputs = load_json(INPUTS_PATH) or []
    if not inputs:
        st.warning("No examples/inputs.json found.")
    else:
        options = {f"#{ex['id']:02d} — {ex['text'][:60]}": ex["id"] for ex in inputs}
        choice = st.selectbox("Pick a ticket", list(options.keys()))
        ticket_id = options[choice]
        ticket = next(ex for ex in inputs if ex["id"] == ticket_id)

        st.markdown("**Ticket text:**")
        st.write(ticket["text"])
        st.markdown("**Metadata:**")
        st.json(ticket.get("metadata", {}))

        out_path = AGENT_OUT_DIR / f"output_{ticket_id:02d}.json"
        result = load_json(out_path)

        st.divider()
        if result is None:
            st.warning(
                f"No output found at examples/outputs/output_{ticket_id:02d}.json yet. "
                "Run `python run_examples.py` to generate it."
            )
        else:
            render_result_card(result)
            render_trace_tree(result.get("trace", []))

# --- Tab 3: Agent vs Baseline ----------------------------------------------
with tab3:
    st.subheader("Agent (with tools) vs Baseline (single prompt, no tools)")
    st.caption(
        "Requires both `python run_examples.py` and "
        "`python -m baseline.baseline_classifier` to have been run."
    )

    inputs = load_json(INPUTS_PATH) or []
    rows = []
    for ex in inputs:
        agent_result = load_json(AGENT_OUT_DIR / f"output_{ex['id']:02d}.json")
        baseline_result = load_json(BASELINE_OUT_DIR / f"baseline_{ex['id']:02d}.json")

        agent_cat = agent_result.get("category") if agent_result else "—"
        agent_pri = agent_result.get("priority") if agent_result else "—"
        base_cat = baseline_result.get("category") if baseline_result else "—"
        base_pri = baseline_result.get("priority") if baseline_result else "—"

        agree = (agent_cat == base_cat) and (agent_pri == base_pri)

        rows.append({
            "#": ex["id"],
            "Ticket": ex["text"][:55] + ("..." if len(ex["text"]) > 55 else ""),
            "Agent": f"{agent_cat} / {agent_pri}",
            "Baseline": f"{base_cat} / {base_pri}",
            "Agree?": "✅" if agree else "⚠️" if agent_result and baseline_result else "—",
        })

    if rows:
        import pandas as pd

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        computed = [r for r in rows if r["Agree?"] in ("✅", "⚠️")]
        if computed:
            agree_count = sum(1 for r in computed if r["Agree?"] == "✅")
            st.metric("Agreement rate", f"{agree_count} / {len(computed)}")
        else:
            st.info("Run both scripts to populate this comparison.")
    else:
        st.warning("No examples found.")

    st.divider()
    st.caption("Full written analysis: see baseline/comparison_report.md")
