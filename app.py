import uuid
import streamlit as st
from langchain_core.messages import HumanMessage

from main import app as travel_app

# ─────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Wanderly · AI Travel Planner",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────
# THEME / CSS
# ─────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Poppins', sans-serif;
    }

    .stApp {
        background: linear-gradient(180deg, #eaf6fb 0%, #fdf6ec 55%, #fff 100%);
    }

    /* Hero banner */
    .hero {
        background: linear-gradient(120deg, #ff9966 0%, #ff5e62 35%, #2193b0 100%);
        border-radius: 22px;
        padding: 2.4rem 2.2rem;
        margin-bottom: 1.6rem;
        color: white;
        box-shadow: 0 10px 30px rgba(33, 147, 176, 0.25);
    }
    .hero h1 {
        font-family: 'Playfair Display', serif;
        font-size: 2.5rem;
        margin: 0 0 .3rem 0;
    }
    .hero p {
        font-size: 1.05rem;
        opacity: .95;
        margin: 0;
    }

    /* Section cards */
    .travel-card {
        background: #ffffff;
        border-radius: 18px;
        padding: 1.4rem 1.5rem;
        box-shadow: 0 6px 18px rgba(0,0,0,0.06);
        border: 1px solid #f0e9e0;
        margin-bottom: 1rem;
        height: 100%;
    }
    .travel-card h3 {
        margin-top: 0;
        font-family: 'Playfair Display', serif;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2193b0 0%, #1c6f86 100%);
    }
    section[data-testid="stSidebar"] * {
        color: #fdf6ec !important;
    }
    section[data-testid="stSidebar"] .stTextArea textarea,
    section[data-testid="stSidebar"] input {
        color: #1c1c1c !important;
        background-color: #ffffff !important;
        border-radius: 10px !important;
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(120deg, #ff9966, #ff5e62);
        color: white;
        border: none;
        border-radius: 999px;
        padding: .6rem 1.6rem;
        font-weight: 600;
        box-shadow: 0 6px 16px rgba(255,94,98,0.35);
        transition: transform .15s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        color: white;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
    }

    .footer-note {
        text-align: center;
        color: #8a8a8a;
        font-size: .85rem;
        margin-top: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "results" not in st.session_state:
    st.session_state.results = None
if "history" not in st.session_state:
    st.session_state.history = []  # list of (query, results) tuples

# ─────────────────────────────────────────────────────────────────────────
# HERO
# ─────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="hero">
        <h1>🧭 Wanderly — AI Travel Planner</h1>
        <p>Flights, stays, and a day-by-day itinerary — planned by a crew of AI agents in one shot.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────
# SIDEBAR — TRIP INPUT
# ─────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ✈️ Plan Your Trip")
    st.caption("Describe your trip in one go — dates, cities, budget, vibe.")

    example = "Round trip from Delhi to Bali, 10-15 Nov, 2 travelers, mid-range budget, beaches + culture"
    user_query = st.text_area(
        "Your travel request",
        placeholder=example,
        height=150,
    )

    with st.expander("💡 Need inspiration?"):
        st.write(f"*Example:* {example}")

    plan_clicked = st.button("🚀 Plan My Trip", use_container_width=True)

    st.markdown("---")
    st.markdown("### 🗂️ Trip History")
    if st.session_state.history:
        for i, (q, _) in enumerate(reversed(st.session_state.history)):
            st.caption(f"**{len(st.session_state.history) - i}.** {q[:50]}{'…' if len(q) > 50 else ''}")
    else:
        st.caption("No trips planned yet.")

    st.markdown("---")
    if st.button("🔄 New session", use_container_width=True):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.results = None
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────
# RUN THE GRAPH (STREAMED, SO WE CAN SHOW LIVE AGENT PROGRESS)
# ─────────────────────────────────────────────────────────────────────────
NODE_LABELS = {
    "flight_agent": "🛫 Searching flights",
    "hotel_agent": "🏨 Finding hotels",
    "itinerary_agent": "🗺️ Drafting itinerary",
    "final_agent": "📋 Finalizing your plan",
}

if plan_clicked:
    if not user_query.strip():
        st.warning("Please describe your trip first.")
    else:
        config = {"configurable": {"thread_id": st.session_state.thread_id}}
        inputs = {
            "messages": [HumanMessage(content=user_query)],
            "user_query": user_query,
            "flight_results": "",
            "hotel_results": "",
            "itinerary": "",
            "llm_calls": 0,
        }

        status = st.status("Assembling your travel crew…", expanded=True)
        collected_state = {}

        try:
            for step in travel_app.stream(inputs, config, stream_mode="updates"):
                for node_name, node_output in step.items():
                    label = NODE_LABELS.get(node_name, node_name)
                    status.write(f"{label} ✅")
                    collected_state.update(node_output)

            status.update(label="Trip planned!", state="complete", expanded=False)

            st.session_state.results = {
                "query": user_query,
                "flight_results": collected_state.get("flight_results", ""),
                "hotel_results": collected_state.get("hotel_results", ""),
                "itinerary": collected_state.get("itinerary", ""),
                "final": next(
                    (
                        m.content
                        for m in reversed(collected_state.get("messages", []))
                        if getattr(m, "type", "") == "ai"
                    ),
                    collected_state.get("itinerary", ""),
                ),
            }
            st.session_state.history.append((user_query, st.session_state.results))

        except Exception as e:
            status.update(label="Something went wrong", state="error", expanded=True)
            st.error(f"Planning failed: {e}")

# ─────────────────────────────────────────────────────────────────────────
# RESULTS
# ─────────────────────────────────────────────────────────────────────────
results = st.session_state.results

if results:
    st.markdown(f"### Results for: _{results['query']}_")

    tab_final, tab_flights, tab_hotels, tab_itinerary = st.tabs(
        ["📋 Final Plan", "🛫 Flights", "🏨 Hotels", "🗺️ Itinerary"]
    )

    with tab_final:
        st.markdown(
            f'<div class="travel-card"><h3>Your Trip, Ready to Go</h3>{results["final"]}</div>',
            unsafe_allow_html=True,
        )

    with tab_flights:
        st.markdown(
            f'<div class="travel-card"><h3>✈️ Flight Options</h3>{results["flight_results"] or "No flight data returned."}</div>',
            unsafe_allow_html=True,
        )

    with tab_hotels:
        st.markdown(
            f'<div class="travel-card"><h3>🏨 Stays</h3>{results["hotel_results"] or "No hotel data returned."}</div>',
            unsafe_allow_html=True,
        )

    with tab_itinerary:
        st.markdown(
            f'<div class="travel-card"><h3>🗺️ Day-by-Day Itinerary</h3>{results["itinerary"] or "No itinerary generated."}</div>',
            unsafe_allow_html=True,
        )
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            '<div class="travel-card"><h3>🛫 Flights</h3>Real-time flight search across your route.</div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            '<div class="travel-card"><h3>🏨 Hotels</h3>Curated stays matched to your budget and vibe.</div>',
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            '<div class="travel-card"><h3>🗺️ Itinerary</h3>A day-by-day plan stitched together by AI.</div>',
            unsafe_allow_html=True,
        )
    st.info("Fill in your trip details in the sidebar and hit **Plan My Trip** to get started.")

st.markdown(
    '<div class="footer-note">Built with LangGraph + Streamlit · Powered by ChatGroq</div>',
    unsafe_allow_html=True,
)