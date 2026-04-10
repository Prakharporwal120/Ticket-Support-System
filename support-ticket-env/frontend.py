"""Streamlit frontend for SupportTicketEnv."""

import streamlit as st
import httpx

API_URL = "http://localhost:8000"

# --- Page config ---
st.set_page_config(page_title="SupportTicketEnv", page_icon="STE", layout="centered")

# --- Custom CSS ---
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        color: #e0e0e0;
    }
    .main-header {
        text-align: center;
        padding: 1.5rem 0 0.5rem 0;
    }
    .main-header h1 {
        background: linear-gradient(90deg, #00d2ff, #7b2ff7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.4rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .main-header p {
        color: #9e9e9e;
        font-size: 1rem;
    }
    .ticket-card {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 1.8rem;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
    }
    .ticket-card h3 {
        color: #00d2ff;
        margin-bottom: 0.8rem;
        font-size: 1.1rem;
    }
    .ticket-text {
        color: #ffffff;
        font-size: 1.15rem;
        line-height: 1.6;
        padding: 1rem;
        background: rgba(0,210,255,0.05);
        border-left: 3px solid #00d2ff;
        border-radius: 0 8px 8px 0;
    }
    .result-card {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .metric-row {
        display: flex;
        gap: 1rem;
        margin-top: 0.5rem;
    }
    .metric-box {
        flex: 1;
        background: rgba(255,255,255,0.04);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }
    .metric-box .label {
        color: #9e9e9e;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .metric-box .value {
        font-size: 1.5rem;
        font-weight: 700;
        margin-top: 0.3rem;
    }
    .positive { color: #4caf50; }
    .negative { color: #f44336; }
    .neutral  { color: #ff9800; }
    .status-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-open       { background: rgba(255,152,0,0.2); color: #ff9800; }
    .badge-categorized { background: rgba(0,210,255,0.2); color: #00d2ff; }
    .badge-prioritized { background: rgba(123,47,247,0.2); color: #b388ff; }
    .badge-resolved    { background: rgba(76,175,80,0.2); color: #4caf50; }
    .badge-closed      { background: rgba(158,158,158,0.2); color: #9e9e9e; }
    .badge-done-true   { background: rgba(76,175,80,0.2); color: #4caf50; }
    .badge-done-false  { background: rgba(255,152,0,0.2); color: #ff9800; }
    .resolved-item {
        background: rgba(76,175,80,0.08);
        border: 1px solid rgba(76,175,80,0.2);
        border-radius: 10px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.5rem;
    }
    .resolved-item .rid {
        color: #4caf50;
        font-weight: 700;
        font-size: 0.9rem;
    }
    .resolved-item .rtext {
        color: #bbb;
        font-size: 0.85rem;
        margin-top: 0.3rem;
    }
    .resolved-item .rmeta {
        color: #777;
        font-size: 0.75rem;
        margin-top: 0.2rem;
    }
    div[data-testid="stHorizontalBlock"] button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s;
    }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div class="main-header">
    <h1>SupportTicketEnv</h1>
    <p>OpenEnv-Compatible Customer Support Simulation</p>
</div>
""", unsafe_allow_html=True)

# --- Session state init ---
if "observation" not in st.session_state:
    st.session_state.observation = None
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "history" not in st.session_state:
    st.session_state.history = []
if "all_resolved" not in st.session_state:
    st.session_state.all_resolved = False


# --- Helper functions ---
def call_reset(task):
    """Call POST /reset."""
    try:
        r = httpx.post(f"{API_URL}/reset", json={"task": task}, timeout=10.0)
        r.raise_for_status()
        data = r.json()
        if data.get("observation") is None:
            st.session_state.observation = None
            st.session_state.all_resolved = True
        else:
            st.session_state.observation = data["observation"]
            st.session_state.all_resolved = False
        st.session_state.last_result = None
        st.session_state.history = []
        return data
    except Exception as e:
        st.error(f"Reset failed: {e}")
        return None


def call_step(action_type, value):
    """Call POST /step."""
    try:
        r = httpx.post(f"{API_URL}/step", json={"action_type": action_type, "value": value}, timeout=10.0)
        r.raise_for_status()
        data = r.json()
        st.session_state.observation = data["observation"]
        st.session_state.last_result = data
        st.session_state.history.append(data)
        return data
    except Exception as e:
        st.error(f"Step failed: {e}")
        return None


def get_tickets_info():
    """Call GET /tickets."""
    try:
        r = httpx.get(f"{API_URL}/tickets", timeout=10.0)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def reward_color(reward):
    if reward > 0:
        return "positive"
    elif reward < 0:
        return "negative"
    return "neutral"


# --- Fetch ticket counts ---
tickets_info = get_tickets_info()
ticket_counts = tickets_info.get("ticket_counts", {}) if tickets_info else {}
resolved_list = tickets_info.get("resolved_tickets", []) if tickets_info else []

# --- Sidebar ---
with st.sidebar:
    st.markdown("### Controls")
    task = st.selectbox("Select Task", ["easy_task", "medium_task", "hard_task"])
    if st.button("Reset / Next Ticket", use_container_width=True, type="primary"):
        call_reset(task)
        st.rerun()

    st.markdown("---")

    # --- Progress indicators ---
    st.markdown("### Ticket Queue")
    total = ticket_counts.get("total_tickets", 0)
    resolved = ticket_counts.get("resolved_tickets", 0)
    pending = ticket_counts.get("pending_tickets", 0)
    open_count = ticket_counts.get("open_tickets", 0)

    if total > 0:
        progress = resolved / total
        st.progress(progress, text=f"{resolved}/{total} resolved ({progress:.0%})")
    st.markdown(f"**Total:** {total}  |  **Resolved:** {resolved}  |  **Open:** {open_count}")

    st.markdown("---")
    st.markdown("### Task Info")
    task_info = {
        "easy_task":   ("Categorize a ticket", "1 step"),
        "medium_task": ("Assign correct priority", "1 step"),
        "hard_task":   ("Full workflow", "4 steps"),
    }
    desc, steps = task_info[task]
    st.markdown(f"**Goal:** {desc}")
    st.markdown(f"**Steps:** {steps}")

    st.markdown("---")
    st.markdown("### Step History")
    if st.session_state.history:
        for i, h in enumerate(st.session_state.history, 1):
            reward = h["reward"]
            color = "green" if reward > 0 else ("red" if reward < 0 else "orange")
            reason = h.get("info", {}).get("reason", "")
            st.markdown(f"**Step {i}:** `{reason}` : :{color}[{reward:+.2f}]")
    else:
        st.caption("No steps yet. Click Reset / Next Ticket.")


# --- Main area ---
obs = st.session_state.observation

if st.session_state.all_resolved:
    st.markdown("""
    <div class="ticket-card" style="text-align:center; padding: 3rem;">
        <h3 style="font-size:1.3rem; color:#4caf50;">All Tickets Resolved!</h3>
        <p style="color:#9e9e9e;">Every ticket in the queue has been processed. Great work!</p>
    </div>
    """, unsafe_allow_html=True)

elif obs is None:
    st.markdown("""
    <div class="ticket-card" style="text-align:center; padding: 3rem;">
        <h3 style="font-size:1.3rem;">No Ticket Loaded</h3>
        <p style="color:#9e9e9e;">Select a task and click <strong>Reset / Next Ticket</strong> in the sidebar to begin.</p>
    </div>
    """, unsafe_allow_html=True)

else:
    # --- Ticket display ---
    status = obs.get("status", "open")
    badge_class = f"badge-{status}"

    st.markdown(f"""
    <div class="ticket-card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.8rem;">
            <h3 style="margin:0;">Ticket #{obs['ticket_id']}</h3>
            <span class="status-badge {badge_class}">{status.upper()}</span>
        </div>
        <div class="ticket-text">{obs['ticket_text'] if obs['ticket_text'] else '<em style="color:#9e9e9e;">(empty message)</em>'}</div>
    </div>
    """, unsafe_allow_html=True)

    # Current fields
    col1, col2 = st.columns(2)
    with col1:
        cat = obs.get("category") or "Not set"
        st.markdown(f"**Category:** `{cat}`")
    with col2:
        pri = obs.get("priority") or "Not set"
        st.markdown(f"**Priority:** `{pri}`")

    st.markdown("---")

    # --- Action buttons ---
    st.markdown("### Take Action")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Categorize Ticket**")
        category = st.selectbox("Category", ["billing", "technical", "account", "delivery", "refund", "security", "subscription", "order", "payment", "login"], key="cat_sel")
        if st.button("Categorize", use_container_width=True):
            call_step("categorize_ticket", category)
            st.rerun()

    with col_b:
        st.markdown("**Assign Priority**")
        priority = st.selectbox("Priority", ["high", "medium", "low"], key="pri_sel")
        if st.button("Assign Priority", use_container_width=True):
            call_step("assign_priority", priority)
            st.rerun()

    col_c, col_d = st.columns(2)

    with col_c:
        st.markdown("**Resolve Ticket**")
        resolution = st.text_input("Resolution text", value="Issue has been resolved.", key="res_input")
        if st.button("Resolve", use_container_width=True):
            call_step("resolve_ticket", resolution)
            st.rerun()

    with col_d:
        st.markdown("**Close Ticket**")
        close_reason = st.text_input("Close reason", value="Verified and closed.", key="close_input")
        if st.button("Close", use_container_width=True):
            call_step("close_ticket", close_reason)
            st.rerun()

    # --- Last step result ---
    result = st.session_state.last_result
    if result:
        st.markdown("---")

        reward = result["reward"]
        done = result["done"]
        info = result.get("info", {})
        reason = info.get("reason", "N/A")
        score = info.get("score")
        error = info.get("error")
        r_color = reward_color(reward)

        st.markdown(f"""
        <div class="result-card">
            <h3 style="color:#00d2ff; margin-bottom: 0.5rem;">Last Step Result</h3>
            <div class="metric-row">
                <div class="metric-box">
                    <div class="label">Reward</div>
                    <div class="value {r_color}">{reward:+.2f}</div>
                </div>
                <div class="metric-box">
                    <div class="label">Done</div>
                    <div class="value">
                        <span class="status-badge badge-done-{str(done).lower()}">{str(done).upper()}</span>
                    </div>
                </div>
                <div class="metric-box">
                    <div class="label">Reason</div>
                    <div class="value" style="font-size:1rem; color:#b388ff;">{reason}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if error:
            st.error(f"Error: {error}")

        if score is not None:
            if score >= 0.8:
                st.success(f"Task Complete! Final Score: {score:.2f}")
            elif score >= 0.5:
                st.warning(f"Task Complete. Score: {score:.2f}")
            else:
                st.error(f"Task Failed. Score: {score:.2f}")

        # Show next ticket hint
        next_id = info.get("next_ticket_id")
        if done and next_id:
            st.info(f"Next ticket available: #{next_id}. Click 'Reset / Next Ticket' to continue.")
        elif done and info.get("message") == "All tickets resolved":
            st.success("All tickets in the queue have been resolved!")


# --- Resolved Tickets Section ---
st.markdown("---")
st.markdown("### Resolved Tickets")

if resolved_list:
    for rt in resolved_list:
        cat_str = rt.get("category") or "N/A"
        pri_str = rt.get("priority") or "N/A"
        res_str = rt.get("resolution") or "N/A"
        text_preview = rt.get("text", "")[:100]
        st.markdown(f"""
        <div class="resolved-item">
            <div class="rid">Ticket #{rt['ticket_id']} - RESOLVED</div>
            <div class="rtext">{text_preview}{'...' if len(rt.get('text', '')) > 100 else ''}</div>
            <div class="rmeta">Category: {cat_str} | Priority: {pri_str} | Resolution: {res_str[:60]}</div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.caption("No tickets resolved yet. Process tickets to see them here.")
