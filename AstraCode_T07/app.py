import streamlit as st
import time
import pandas as pd
from src.analytics import RiskAnalytics

# --- CONFIGURATION ---
#Set basic page configurations for the Streamlit app
st.set_page_config(
    page_title="AstraCode: National Situational Awareness System", # Title of the browser tab
    page_icon="T07", # Icon shown in browser tab
    layout="wide", # Use full-width layout
    initial_sidebar_state="collapsed"  # Sidebar starts collapsed
)

# Inject CSS styles into the page to make it look professional
st.markdown("""
<style>
    .stApp {background-color: #f4f6f9;}
    .metric-card {
        background-color: white; 
        padding: 15px; 
        border-radius: 10px; 
        border-left: 5px solid #4B4BFF;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    h3 {font-size: 22px !important; font-weight: 600;}
    div[data-testid="stMetricValue"] {font-size: 28px;}
    
    /* Live Indicator Animation */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    .live-dot {
        color: #FF4B4B;
        font-weight: bold;
        animation: pulse 2s infinite;
    }
</style>
""", unsafe_allow_html=True)

# --- LOAD ENGINE ---
@st.cache_resource
def get_engine(): 
    return RiskAnalytics() # Initialize RiskAnalytics class

engine = get_engine() # Create or get cached engine
data_loaded = engine.load_data() # Load data from database

# --- SIDEBAR ---
with st.sidebar:
    st.header("System Controls") #Sidebar title 
    
    # Toggle for live auto-refresh mode
    live_mode = st.toggle("Auto-Refresh (Live Mode)", value=True)
    # Button to manually force data reload
    if st.button("Force Sync Now"):
        st.cache_resource.clear() # Clear cached engine
        engine.load_data() # Reload data
        st.rerun() # Refresh the app
        
    # Info about the data sources being monitored
    st.info("Monitoring Sources: Ada Derana, Daily Mirror, EconomyNext, Daily News, Google News (Gen/Biz/Pol)")
    
    # Dropdown for selecting sector filter if data is loaded
    if data_loaded:
        st.markdown("Filter Feed")
        sectors = ["All"] + list(engine.df['sector'].unique()) if 'sector' in engine.df.columns else ["All"]
        # This variable 'selected_sector' is what we need to pass to every function below
        selected_sector = st.selectbox("Business Sector:", sectors) 
    else:
        selected_sector = "All" # Default to All sectors

# --- HEADER ---
# Split top section into two columns like main title and live status
col1, col2 = st.columns([4, 1])
with col1:
    st.title("T07 AstraCode: National Situational Awareness System") # Main app title
    if selected_sector != "All":
        st.markdown(f"**Real-time Intelligence Monitor: {selected_sector} Sector**") # Show selected sector
    else:
        st.markdown("**Real-time National Intelligence & Business Continuity Monitor**")

with col2:
    if live_mode:
        st.markdown('<p class="live-dot">● LIVE FEED ACTIVE</p>', unsafe_allow_html=True)
    else:
        st.caption("FEED PAUSED")   # Show feed paused status

if data_loaded:
    
    # ----------------- NATIONAL PULSE (Macro View) ---------------------
    # Get the KPIs Stability, Critical Risk count, Activity Volume
    stability, critical, volume = engine.get_national_indicators(selected_sector)
    
    # Display status message based on stability score
    if stability > 75:
        st.success(f"**STATUS: STABLE** (Score: {stability}) - Normal operations happening.")
    elif stability > 50:
        st.warning(f"**STATUS: CAUTION** (Score: {stability}) - Emerging disruptions detected.")
    else:
        st.error(f"**STATUS: CRITICAL** (Score: {stability}) - Widespread instability. Activate contingencies.")

    # Show metrics in columns
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Stability Score", f"{stability}%", "Target: >80%")  # Main KPI
    c2.metric("Critical Risks", critical, "Alerts", delta_color="inverse") # High-risk count
    c3.metric("Activity Volume", f"{volume} Signals", "Last 24h Velocity") # Data volume metric
    
    # Compute simple sentiment based on stability
    sentiment = "Neutral"
    if stability > 60: sentiment = "Positive"
    if stability < 40: sentiment = "Negative"
    c4.metric("Public Sentiment", sentiment, "Social Mood")  # Show sentiment

    
    # -------------------- EVENTS & TRENDS ------------------------
    st.divider()
    c1, c2 = st.columns(2)
    
    # LEFT: Upcoming Events (Innovation)
    with c1:
        st.subheader("Major Upcoming Events")
        st.caption("Scheduled disruptions, holidays, and planned political events.")
        
        # ----------- Pass selected_sector -----------------
        # Get upcoming events from engine
        if hasattr(engine, 'get_upcoming_events'):
            upcoming = engine.get_upcoming_events(selected_sector)
            if not upcoming.empty:
                for _, row in upcoming.iterrows():
                    st.info(f"**{row['title']}**") # Event title
                    st.caption(f"Source: {row.get('source', 'Unknown')} | Risk Impact: {row.get('risk_score', 0)}%")
            else:
                st.write(f"No upcoming events detected for {selected_sector}.")
        else:
            st.error("Update analytics.py for Event Detection.")

    # RIGHT: Public Pulse / Emerging Themes
    with c2:
        st.subheader("Topics Gaining Traction")
        st.caption("Dominant themes in public discourse (AI Detected).")
        
        # Get themes from engine
        themes = engine.get_emerging_themes(selected_sector)
        
        if themes:
            for theme in themes:
                with st.expander(f"🔹 {theme['topic']} ({theme['count']} articles)", expanded=True):
                    for row in theme.get('articles', []):
                        link = row.get('link', '#')
                        st.markdown(f"• [{row.get('title', 'Untitled')}]({link})")
                        st.caption(f"{row.get('source', 'Unknown')} • {str(row.get('published', ''))[:16]}")
        else:
            st.info(f"Insufficient data for topic modeling in {selected_sector}.")

    # ----------------- BUSINESS IMPACT ---------------------
    st.divider()
    st.subheader("Sector Comparison")
    st.caption("How your selected sector compares to the national average.")
    
    # Get sector risk scores
    sector_status = engine.get_sector_status()
    cols = st.columns(3) # Display 3 sectors per row
    for i, (sec, score) in enumerate(sector_status.items()):
        # Highlight selected sector
        is_selected = (sec == selected_sector) or (selected_sector == "All")
        
        # Color and text based on risk score
        if is_selected:
            color = "green"
            status_text = "OPTIMAL"
            if score > 30: 
                color = "orange"
                status_text = "STRAINED"
            if score > 60: 
                color = "red"
                status_text = "CRITICAL"
            
            # Display each sector in its column
            with cols[i % 3]:
                with st.container(border=True):
                    marker = "📍" if (selected_sector == sec) else ""
                    st.markdown(f"**{marker} {sec}**")
                    st.progress(score, text=f"{status_text} ({score}% Risk)")

    # ------------------- RISK & OPPORTUNITY FEED ----------------------
    st.divider()
    c_risk, c_opp = st.columns(2)
    
    # Helper function to render feed cards
    def render_feed_card(container, row, card_type="risk"):
        icon = "🔴" if card_type == "risk" else "🟢"
        with container:
            with st.container(border=True):
                st.markdown(f"**{icon} {row.get('category', 'General')} | {row.get('sector', 'General')}**")
                st.markdown(f"*{row.get('title', 'No Title')}*")
                st.caption(f"{row.get('source', 'Unknown')} • Risk Score: {row.get('risk_score', 0)}")
                if 'link' in row:
                    st.link_button("Read Briefing", row['link'], use_container_width=True)

    # LEFT: Priority Risks
    with c_risk:
        st.subheader("🔻 Priority Threats")
        st.caption("High-risk signals requiring mitigation.")
        
        
        risks, _ = engine.get_top_insights(selected_sector)
        if not risks.empty:
            for _, row in risks.iterrows():
                render_feed_card(c_risk, row, "risk")
        else:
            st.success("No critical threats detected.")

    # RIGHT: Strategic Opportunities
    with c_opp:
        st.subheader("Strategic Opportunities")
        st.caption("Positive trends for growth & investment.")
        
        _, opps = engine.get_top_insights(selected_sector)
        if not opps.empty:
            for _, row in opps.iterrows():
                render_feed_card(c_opp, row, "opportunity")
        else:
            st.info("No clear growth signals in current feed.")

    # ---------------------- STRATEGIC INSIGHTS (Forecast & Map) ---------------------
    st.divider()
    
    tab1, tab2 = st.tabs(["Stability Forecast & Map", "Raw Intelligence Feed"])

    # Tab1: Forecast & Map
    with tab1:
        c_trend, c_map = st.columns(2)
        
        # LEFT: Stability Forecast
        with c_trend:
            st.subheader("Stability Forecast (4h)")
            st.caption("Predictive trend analysis based on signal velocity.")
            # Pass selected_sector
            forecast = engine.get_forecast(selected_sector)
            
            if forecast is not None:
                st.area_chart(forecast, color=["#FF4B4B", "#4B4BFF"], height=300)
                st.caption("🔴 Red: Historical Trend | 🔵 Blue: AI Projected Risk")
            else:
                st.info("Gathering historical data for prediction model...")

        # RIGHT: Map Data
        with c_map:
            st.subheader(" Geographic Disruptions")
            st.caption("Live heatmap of high-risk locations.")
            #Pass selected_sector
            map_data = engine.get_map_data(selected_sector)
            if not map_data.empty:
                st.map(map_data, latitude='lat', longitude='lon', size='risk_score', color='#FF0000')
            else:
                st.info("No location-specific incidents detected.")

    # Tab2: Raw Intelligence Feed
    with tab2:
        #Use filtered feed
        display_df = engine.get_filtered_feed(selected_sector)
        if not display_df.empty:
            cols_to_show = ['published', 'category', 'sector', 'risk_score', 'title', 'link']
            available_cols = [c for c in cols_to_show if c in display_df.columns]
            
            st.dataframe(
                display_df[available_cols],
                column_config={
                    "link": st.column_config.LinkColumn("Read Full Article"),
                    "risk_score": st.column_config.ProgressColumn("Risk", min_value=0, max_value=100)
                },
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.warning("No data available for this sector.")

    # Auto-refresh logic loop
    if live_mode:
        time.sleep(60) # Wait 60 seconds
        st.rerun() # Refresh page

else:
    st.warning("System Initializing...")