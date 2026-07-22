import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# Configuration
st.set_page_config(
    page_title="PitWall AI",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Mode Styling applied automatically by Streamlit settings/theme
# but we can add custom CSS if needed.
st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .st-emotion-cache-1y4p8pa {
        padding-top: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# API Endpoint (adjust if using Docker/Cloud)
API_URL = "http://localhost:8000/api/v1/strategy/query"

st.title("🏎️ PitWall AI")
st.subheader("Interactive F1 Telemetry & Radio Transcript RAG")

# Sidebar for inputs
with st.sidebar:
    st.header("Race Settings")
    year = st.number_input("Year", min_value=2018, max_value=2024, value=2023, step=1)
    grand_prix = st.text_input("Grand Prix", value="Monza")
    session_type = st.selectbox("Session Type", options=["FP1", "FP2", "FP3", "Q", "S", "SS", "R"], index=6) # Default to Race
    driver_code = st.text_input("Driver Code (3 letters)", value="VER").upper()

    st.divider()
    st.markdown("### Backend Status")
    try:
        res = requests.get("http://localhost:8000/health", timeout=2)
        if res.status_code == 200:
            st.success("API is Online ✅")
        else:
            st.error("API Error ❌")
    except:
        st.warning("API Offline ⚠️")

# Main content area
query = st.text_area("Ask a strategy question...", placeholder="e.g. Why did Max pit on lap 20 instead of lap 22? How was his tire degradation?")

if st.button("Generate Strategy Insight", type="primary"):
    if not query:
        st.warning("Please enter a question.")
    else:
        with st.spinner(f"Analyzing {driver_code}'s telemetry and radio communications..."):
            payload = {
                "year": year,
                "grand_prix": grand_prix,
                "session_type": session_type,
                "driver_code": driver_code,
                "query": query
            }

            try:
                response = requests.post(API_URL, json=payload)

                if response.status_code == 200:
                    data = response.json()

                    # Layout: 2 Columns
                    col1, col2 = st.columns([1, 1])

                    with col1:
                        st.markdown("### 🧠 AI Strategy Insight")
                        st.info(data.get("insight", "No insight generated."))

                        st.markdown("### 📻 Retrieved Radio Context")
                        radios = data.get("radio_transcripts", [])
                        if radios:
                            for i, r in enumerate(radios):
                                # Displaying placeholder text, update based on actual qdrant payload
                                st.caption(f"**Transcript {i+1}:** {r.get('text', 'No text available')}")
                        else:
                            st.caption("No relevant radio transcripts found.")

                    with col2:
                        st.markdown("### 📊 Telemetry Data")
                        telemetry = data.get("telemetry", {})

                        if "error" in telemetry:
                            st.error(telemetry["error"])
                        else:
                            st.metric(label="Fastest Lap Time (s)", value=telemetry.get("fastest_lap_time_seconds"))
                            st.metric(label="Max Speed (kph)", value=telemetry.get("max_speed_kph"))

                            # Render Plotly Chart for Laps
                            laps = telemetry.get("laps", [])
                            if laps:
                                df = pd.DataFrame(laps)
                                fig = px.line(
                                    df, x="LapNumber", y="LapTime",
                                    title=f"{driver_code} Lap Times",
                                    markers=True,
                                    template="plotly_dark"
                                )
                                fig.update_yaxes(title_text="Lap Time (Seconds)")
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.warning("No lap data available for plotting.")

                else:
                    st.error(f"Error from API: {response.text}")

            except Exception as e:
                st.error(f"Connection failed: {str(e)}")
