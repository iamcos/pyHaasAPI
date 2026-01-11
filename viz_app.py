import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Page Configuration
st.set_page_config(
    page_title="Haas Data Viz",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for Glassmorphism/Dark Theme
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .metric-card {
        background-color: #262730;
        border: 1px solid #4F4F4F;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    try:
        df = pd.read_parquet("backtest_data.parquet")
        # Ensure calculated columns exist
        if "roi_custom" not in df.columns:
            st.error("Parquet file missing custom metrics!")
            return pd.DataFrame()
        return df
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return pd.DataFrame()

def main():
    st.title("🤖 Haas Data Viz: The Noise-Free Edition")
    st.markdown("### Identifying the 'Holy Grail' Bots")
    
    df = load_data()
    if df.empty:
        st.warning("No data found. Please run `aggregate_backtests.py` first.")
        return

    # --- SIDEBAR FILTERS ---
    st.sidebar.header("🎯 Filters")
    
    # 1. Noise Reduction Defaults
    show_profitable = st.sidebar.checkbox("Show Profitable Only", value=True)
    min_trades = st.sidebar.slider("Min Trades (Reliability)", 0, 500, 50) 
    
    # Drawdown Slider (General Control)
    min_dd_val = int(df["max_drawdown_custom"].min()) if not df.empty else -100
    max_dd_cutoff = st.sidebar.slider("Max Drawdown Allowed (%)", min_dd_val, 0, -30) # Default to -30%

    market_filter = st.sidebar.multiselect("Market", df["market"].unique())
    
    # Apply Filters
    filtered_df = df[df["total_trades_custom"] >= min_trades]
    filtered_df = filtered_df[filtered_df["max_drawdown_custom"] >= max_dd_cutoff] # Apply DD Filter
    
    if show_profitable:
        filtered_df = filtered_df[filtered_df["roi_custom"] > 0]
    if market_filter:
        filtered_df = filtered_df[filtered_df["market"].isin(market_filter)]

    # --- TOP METRICS ROW ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Bots Selected", f"{len(filtered_df)} / {len(df)}")
    with col2:
        avg_roi = filtered_df["roi_custom"].mean()
        st.metric("Avg ROI", f"{avg_roi:.2f}%")
    with col3:
        avg_wr = filtered_df["win_rate_custom"].mean()
        st.metric("Avg Win Rate", f"{avg_wr:.2f}%")
    with col4:
        # Profit Factor > 10 is usually significant
        high_pf = len(filtered_df[filtered_df["profit_factor_custom"] > 2])
        st.metric("Bots with PF > 2.0", high_pf)

    st.markdown("---")

    # --- CHART 1: THE UNIVERSE OF BOTS (Scatter) ---
    st.subheader("1. The Universe of Bots (Log Scale)")
    st.markdown("ROI is shown on a **Log Scale** to handle the massive range of results.")
    
    # Handle log scale visualization (avoid log(0) or negative logs if user shows losers)
    # For visualization, we might clip negatives if "profitable only" is off, 
    # but since defaults are ON, we focus on the positive log view.
    
    fig_scatter = px.scatter(
        filtered_df,
        x="max_drawdown_custom",
        y="roi_custom",
        color="profit_factor_custom", # Color by Profit Factor now
        size="total_trades_custom",
        hover_data=["lab_id", "market", "net_profit_custom", "win_rate_custom"],
        color_continuous_scale="RdYlGn", # Red to Green color scale
        color_continuous_midpoint=1.5, # Green starts around PF 1.5
        title="Risk vs Reward (Size = Trade Count)",
        template="plotly_dark",
        log_y=True # Log scale for ROI
    )
    fig_scatter.update_layout(height=700)
    st.plotly_chart(fig_scatter, use_container_width=True)

    # --- SECTION 2: HALL OF FAME ---
    st.subheader("🏆 Hall of Fame (Top 1% Performers)")
    st.caption("The absolute best bots based on ROI, filtered by your current settings.")
    
    # Get top 1% or top 20
    top_bots = filtered_df.sort_values("roi_custom", ascending=False).head(20)
    
    # Formatted Table
    st.dataframe(
        top_bots[[
            "lab_id", "market", "roi_custom", "net_profit_custom", 
            "max_drawdown_custom", "win_rate_custom", "profit_factor_custom", "total_trades_custom"
        ]].style.format({
            "roi_custom": "{:.2f}%",
            "net_profit_custom": "${:,.2f}",
            "max_drawdown_custom": "{:.2f}%",
            "win_rate_custom": "{:.2f}%",
            "profit_factor_custom": "{:.2f}",
        }),
        use_container_width=True,
        height=500
    )

    # --- SECTION 3: MARKET DNA ---
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("🧬 Market DNA")
        # Only markets with reasonable volume
        market_stats = filtered_df.groupby("market").agg({
            "roi_custom": "mean",
            "file": "count"
        }).reset_index()
        market_stats = market_stats[market_stats["file"] > 10] # Min 10 bots/market
        market_stats = market_stats.sort_values("roi_custom", ascending=False).head(10)
        
        fig_bar = px.bar(
            market_stats,
            x="roi_custom",
            y="market",
            orientation='h',
            title="Easiest Markets to Trade (Avg ROI)",
            template="plotly_dark",
            color="roi_custom",
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_b:
        st.subheader("🔬 Lab Inspector (Top 10 per Lab)")
        # Get list of labs sorted by best ROI
        lab_performance = filtered_df.groupby("lab_id")["roi_custom"].max().sort_values(ascending=False)
        
        selected_lab = st.selectbox("Select Lab (Sorted by Max ROI)", lab_performance.index)
        
        if selected_lab:
            lab_bots = filtered_df[filtered_df["lab_id"] == selected_lab]
            top_10_lab = lab_bots.sort_values("roi_custom", ascending=False).head(10)
            
            st.dataframe(
                top_10_lab[[
                    "market", "roi_custom", "net_profit_custom", 
                    "max_drawdown_custom", "win_rate_custom"
                ]].style.format({
                    "roi_custom": "{:.2f}%",
                    "net_profit_custom": "${:,.2f}",
                    "max_drawdown_custom": "{:.2f}%",
                    "win_rate_custom": "{:.2f}%",
                }),
                use_container_width=True,
                height=300
            )

    # --- SECTION 4: AGGREGATED TOP 10 PER LAB ---
    st.markdown("---")
    with st.expander("📂 View All Top 10s (Grouped by Lab)"):
        # For every lab, get top 10
        top_10_per_lab = filtered_df.groupby("lab_id").apply(
            lambda x: x.nlargest(10, "roi_custom")
        ).reset_index(drop=True)
        
        st.dataframe(
            top_10_per_lab[[
                "lab_id", "market", "roi_custom", "net_profit_custom", 
                "max_drawdown_custom", "win_rate_custom", "profit_factor_custom"
            ]].style.format({
                "roi_custom": "{:.2f}%",
                "net_profit_custom": "${:,.2f}",
                "max_drawdown_custom": "{:.2f}%",
                "win_rate_custom": "{:.2f}%",
                "profit_factor_custom": "{:.2f}",
            }),
            use_container_width=True
        )

if __name__ == "__main__":
    main()
