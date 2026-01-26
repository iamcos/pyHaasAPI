import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
import json
import asyncio
from dotenv import load_dotenv
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.api.lab.lab_api import LabAPI
from pyHaasAPI.api.script.script_api import ScriptAPI
from pyHaasAPI.core.stage2_service import Stage2Service
from pyHaasAPI.core.data_science_service import DataScienceService

load_dotenv()

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

# --- LIVE API WRAPPERS ---
async def get_services():
    client = AsyncHaasClient(
        base_url=f"http://{os.getenv('API_HOST')}:{os.getenv('API_PORT')}"
    )
    auth = AuthenticationManager(
        client, 
        email=os.getenv("API_EMAIL"), 
        password=os.getenv("API_PASSWORD")
    )
    lab_api = LabAPI(client, auth)
    script_api = ScriptAPI(client, auth)
    stage2 = Stage2Service(lab_api, script_api)
    
    # Initialize DS Service with actual data
    df = load_data()
    ds_service = DataScienceService(df)
    
    return stage2, lab_api, ds_service

def run_async(coro):
    return asyncio.run(coro)

def main():
    st.title("🤖 Haas Data Viz: Final Frontier")
    
    df = load_data()
    if df.empty:
        st.warning("No data found. Please run `aggregate_backtests.py` first.")
        return

    # --- GLOBAL FILTERS (Main Body) ---
    with st.expander("🎯 Filter & Refine Strategy", expanded=True):
        f_col1, f_col2, f_col3 = st.columns(3)
        
        with f_col1:
            st.markdown("##### 📈 Performance")
            show_profitable = st.checkbox("Show Profitable Only", value=True)
            min_roi_possible = float(df["roi_custom"].min()) if not df.empty else 0.0
            max_roi_possible = float(df["roi_custom"].max()) if not df.empty else 100.0
            min_roi = st.slider("Min ROI %", min_roi_possible, max_roi_possible, 0.0)
            min_trades = st.slider("Min Trades (Reliability)", 0, 500, 50) 
            
        with f_col2:
            st.markdown("##### 🛡️ Risk")
            min_dd_val = float(df["max_drawdown_custom"].min()) if not df.empty else -100.0
            max_dd_cutoff = st.slider("Max Drawdown Allowed (%)", min_dd_val, 0.0, -30.0, step=0.1)
            debug_mode = st.checkbox("Debug Mode", value=False)

        with f_col3:
            st.markdown("##### 🧪 Dimensions")
            unique_labs = sorted(df["lab_id"].unique())
            lab_filter = st.multiselect("Select Labs", unique_labs)
            unique_markets = sorted(df["market"].unique())
            market_filter = st.multiselect("Select Markets", unique_markets)

    # Check if cache directory exists
    cache_dir = "unified_cache/backtests"
    if not os.path.exists(cache_dir) and debug_mode:
        st.error(f"Cache directory not found: {cache_dir}")
    
    # Apply Filters
    filtered_df = df[df["total_trades_custom"] >= min_trades]
    filtered_df = filtered_df[filtered_df["max_drawdown_custom"] >= max_dd_cutoff]
    filtered_df = filtered_df[filtered_df["roi_custom"] >= min_roi]
    
    if show_profitable:
        filtered_df = filtered_df[filtered_df["roi_custom"] > 0]
    if lab_filter:
        filtered_df = filtered_df[filtered_df["lab_id"].isin(lab_filter)]
    if market_filter:
        filtered_df = filtered_df[filtered_df["market"].isin(market_filter)]

    # --- TABS ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🌌 Dashboard", 
        "📉 Advanced Analytics", 
        "🏆 Hall of Fame", 
        "🎯 Stage 2: Finetune",
        "🔬 Stage 3: Data Science"
    ])

    with tab1:
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
            high_pf = len(filtered_df[filtered_df["profit_factor_custom"] > 2])
            st.metric("Bots with PF > 2.0", high_pf)

        st.markdown("---")

        # --- CHART 1: THE UNIVERSE OF BOTS (Scatter) ---
        st.subheader("The Universe of Bots (Risk vs Reward)")
        fig_scatter = px.scatter(
            filtered_df,
            x="max_drawdown_custom",
            y="roi_custom",
            color="profit_factor_custom",
            size="total_trades_custom",
            hover_data=["lab_id", "market", "net_profit_custom", "win_rate_custom"],
            color_continuous_scale="RdYlGn",
            color_continuous_midpoint=1.5,
            template="plotly_dark",
            log_y=True,
            title="Dots = Unique Bots | Color = Profit Factor | Size = Trades"
        )
        fig_scatter.update_layout(height=600)
        st.plotly_chart(fig_scatter, use_container_width=True)

        # --- MARKET DNA ---
        st.subheader("🧬 Market DNA")
        market_stats = filtered_df.groupby("market").agg({
            "roi_custom": "mean",
            "file": "count"
        }).reset_index()
        market_stats = market_stats[market_stats["file"] > 10].sort_values("roi_custom", ascending=False).head(10)
        
        fig_bar = px.bar(
            market_stats, x="roi_custom", y="market", orientation='h',
            template="plotly_dark", color="roi_custom", color_continuous_scale="Viridis",
            title="Easiest Markets to Trade (Avg ROI, Min 10 Bots)"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        st.header("📉 Advanced Strategic Insights")
        
        col_adv1, col_adv2 = st.columns(2)
        
        with col_adv1:
            st.subheader("🎯 Strategic Density Heatmap")
            st.caption("Where is the 'Sweet Spot' for bot performance?")
            fig_heat = px.density_heatmap(
                filtered_df,
                x="win_rate_custom",
                y="profit_factor_custom",
                z="roi_custom",
                histfunc="avg",
                template="plotly_dark",
                color_continuous_scale="Magma",
                title="Density: Win Rate vs Profit Factor (Z=Avg ROI)"
            )
            st.plotly_chart(fig_heat, use_container_width=True)

        with col_adv2:
            st.subheader("📦 Market ROI Distribution")
            st.caption("How volatile is each market for these bots?")
            top_markets_list = market_stats["market"].tolist()
            dist_df = filtered_df[filtered_df["market"].isin(top_markets_list)]
            
            fig_box = px.box(
                dist_df,
                x="market",
                y="roi_custom",
                color="market",
                template="plotly_dark",
                title="ROI spread per Top Market"
            )
            fig_box.update_layout(showlegend=False)
            st.plotly_chart(fig_box, use_container_width=True)

        st.markdown("---")
        st.subheader("📈 Aggregated Equity Index Simulation")
        st.markdown("What would a 'Fund' of the current top 10 bots look like over time?")
        
        if st.button("🚀 Run Simulation (Loading Raw Data...)"):
            top_10 = filtered_df.sort_values("roi_custom", ascending=False).head(10)
            
            all_trades = []
            with st.spinner("Parsing raw JSONs..."):
                for _, row in top_10.iterrows():
                    file_path = os.path.join(cache_dir, row["file"])
                    
                    if not os.path.exists(file_path):
                        if debug_mode:
                            st.warning(f"File not found: {file_path}")
                        continue
                        
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                        content = data.get("Data", data)
                        trades = content.get("FinishedPositions", [])
                        for t in trades:
                            all_trades.append({
                                "time": pd.to_datetime(t.get("ct", 0), unit='s'),
                                "profit": float(t.get("rp", 0.0))
                            })
                    except json.JSONDecodeError:
                        if debug_mode:
                            st.error(f"Invalid JSON in file: {file_path}")
                    except Exception as e:
                        if debug_mode:
                            st.error(f"Error reading {file_path}: {e}")
                        continue
            
            if all_trades:
                equity_df = pd.DataFrame(all_trades).sort_values("time")
                equity_df["cum_profit"] = equity_df["profit"].cumsum()
                
                fig_equity = px.line(
                    equity_df, x="time", y="cum_profit",
                    template="plotly_dark",
                    title="Combined Equity Growth (Top 10 Bots)",
                    color_discrete_sequence=["#00FFCC"]
                )
                fig_equity.update_layout(xaxis_title="Time", yaxis_title="Net Profit ($)")
                st.plotly_chart(fig_equity, use_container_width=True)
            else:
                st.error("Could not load trade data for simulation.")

    with tab3:
        st.header("🏆 Hall of Fame")
        st.markdown("The Top 1% of configurations, scrutinized by Lab and Market.")
        
        col_lab1, col_lab2 = st.columns([1, 2])
        with col_lab1:
            lab_performance = filtered_df.groupby("lab_id")["roi_custom"].max().sort_values(ascending=False)
            selected_lab = st.selectbox("Select Lab", lab_performance.index)
        
        if selected_lab:
            with col_lab2:
                lab_bots = filtered_df[filtered_df["lab_id"] == selected_lab].sort_values("roi_custom", ascending=False).head(10)
                st.dataframe(
                    lab_bots[["market", "roi_custom", "net_profit_custom", "max_drawdown_custom", "win_rate_custom"]]
                    .style.format({"roi_custom": "{:.2f}%", "net_profit_custom": "${:,.2f}", "max_drawdown_custom": "{:.2f}%", "win_rate_custom": "{:.2f}%"}),
                    use_container_width=True
                )

        st.markdown("---")
        st.subheader("Global Top 20 (All Labs)")
        top_20 = filtered_df.sort_values("roi_custom", ascending=False).head(20)
        st.dataframe(
            top_20[["lab_id", "market", "roi_custom", "net_profit_custom", "max_drawdown_custom", "win_rate_custom", "total_trades_custom"]]
            .style.format({"roi_custom": "{:.2f}%", "net_profit_custom": "${:,.2f}", "max_drawdown_custom": "{:.2f}%", "win_rate_custom": "{:.2f}%"}),
            use_container_width=True
        )

    with tab4:
        st.header("🎯 Stage 2: Actionable Finetuning")
        st.markdown("Bridge the gap between analysis and action. Clone winning configurations into new Labs.")

        # --- BOT PICKER ---
        st.subheader("1. Select a Candidate for Finetuning")
        
        # Sort by ROI and trades to suggest candidates
        candidates = filtered_df.sort_values("roi_custom", ascending=False).head(50)
        # Use simple string for selection
        bot_options = [f"{row['lab_id'][:8]} | {row['market']} | ROI: {row['roi_custom']:.1f}% | {row['file']}" for _, row in candidates.iterrows()]
        
        selected_bot_str = st.selectbox("Pick a bot from the 'Universe'", bot_options)
        
        if selected_bot_str:
            # Extract file name from the string
            fname = selected_bot_str.split(" | ")[-1]
            winning_bot = filtered_df[filtered_df["file"] == fname].iloc[0]
            
            st.info(f"Targeting: **{winning_bot['market']}** from Lab **{winning_bot['lab_id']}**")
            
            col_bt1, col_bt2 = st.columns(2)
            with col_bt1:
                st.write("**Winning Parameters:**")
                # In parquet, params are stored as a JSON string
                try:
                    params_json = winning_bot["parameters"]
                    params = json.loads(params_json) if isinstance(params_json, str) else params_json
                    st.json(params)
                except:
                    st.warning("Could not parse parameters for this bot.")
            
            with col_bt2:
                st.write("**Actions**")
                if st.button("🚀 Create Finetuning Lab"):
                    with st.spinner("Cloning Lab and applying presets..."):
                        try:
                            stage2, lab_api = run_async(get_services())
                            new_lab_id = run_async(stage2.clone_for_finetune(
                                winning_bot["lab_id"], 
                                f"{winning_bot['market']}_STG2", 
                                params
                            ))
                            st.success(f"Lab Created! ID: {new_lab_id}")
                            st.balloons()
                        except Exception as e:
                            st.error(f"Failed to clone lab: {e}")

        st.markdown("---")
        # --- LAB BROWSER ---
        st.subheader("📂 Server Lab Browser")
        if st.checkbox("Show Live Labs from Server"):
            try:
                _, lab_api = run_async(get_services())
                labs = run_async(lab_api.get_labs())
                
                lab_data = []
                for l in labs:
                    lab_data.append({
                        "Name": l.name,
                        "ID": l.lab_id,
                        "Status": l.status,
                        "Backtests": l.completed_backtests
                    })
                st.table(lab_data)
            except Exception as e:
                st.error(f"Failed to fetch labs: {e}")

        # --- SCRIPT DEBUGGER ---
        st.markdown("---")
        st.subheader("🐛 Script Lab (Debugger)")
        st.markdown("Identify and fix compilation or runtime errors for your scripts.")
        st.caption("Coming Soon: Interactive error parsing and automated fixing loops.")

    with tab5:
        st.header("🔬 Stage 3: Statistical Modeling & Data Science")
        st.markdown("Quantifying the influence of parameters on strategy performance.")
        
        try:
            # Need fresh service instance with current filters or full data?
            # Let's use filtered data for contextual analysis
            ds = DataScienceService(filtered_df)
            
            with st.spinner("Crunching numbers (Training Random Forest)..."):
                features_df = ds.prepare_features()
                importance = ds.get_feature_importance()
                correlations = ds.get_parameter_correlations()
            
            if importance.empty:
                st.warning("Not enough variance in parameters to build models. Try expanding your Lab/Market filter.")
            else:
                col_ds1, col_ds2 = st.columns([1, 1])
                
                with col_ds1:
                    st.subheader("🤖 Feature Importance")
                    st.info("Which parameters actually drive ROI?")
                    fig_imp = px.bar(
                        importance, 
                        orientation='h', 
                        labels={'value': 'Score', 'index': 'Parameter'},
                        title="Top Influencers (Random Forest)"
                    )
                    st.plotly_chart(fig_imp, use_container_width=True)

                with col_ds2:
                    st.subheader("🔗 Parameter Correlations")
                    st.write(correlations.head(10))
                
                st.markdown("---")
                # --- ADVANCED VISUALIZATIONS ---
                st.subheader("📊 Advanced Parameter Visuals")
                
                viz_choice = st.radio("Select Strategy Insight Map", [
                    "1. Parallel Coordinates (Success Corridors)",
                    "2. Pareto Frontier (Efficiency Map)",
                    "3. Tornado Sensitivity Analysis",
                    "4. Clustering (Strategy DNA Profiles)",
                    "5. Hexbin Joint Plot (Density of Success)",
                    "6. Parameter ROI Box Plots",
                    "7. 3D Surface Plot (TP vs SL vs ROI)"
                ], horizontal=True)

                if "Parallel Coordinates" in viz_choice:
                    top_params = importance.head(6).index.tolist()
                    fig_pc = px.parallel_coordinates(
                        features_df, 
                        color="roi_custom",
                        dimensions=top_params + ["roi_custom"],
                        title="Targeting Success Corridors"
                    )
                    st.plotly_chart(fig_pc, use_container_width=True)

                elif "Pareto Frontier" in viz_choice:
                    fig_pareto = px.scatter(
                        filtered_df, x="max_drawdown_custom", y="roi_custom",
                        color="profit_factor_custom", size="total_trades_custom",
                        title="Efficiency Frontier (Risk vs Reward)"
                    )
                    st.plotly_chart(fig_pareto, use_container_width=True)
                
                elif "Tornado" in viz_choice:
                    param_to_test = st.selectbox("Select Parameter to analyze sensitivity", importance.index.tolist())
                    sens_stats = ds.get_sensitivity_scores(param_to_test)
                    if not sens_stats.empty:
                        # Convert Index bins to strings for plotting
                        sens_stats.index = [str(x) for x in sens_stats.index]
                        fig_tornado = px.bar(sens_stats, y="mean", error_y="std", title=f"Sensitivity: {param_to_test} vs ROI")
                        st.plotly_chart(fig_tornado, use_container_width=True)

                elif "Clustering" in viz_choice:
                    n_c = st.slider("Number of Profile Clusters", 2, 8, 4)
                    clusters = ds.cluster_bots(n_clusters=n_c)
                    filtered_df["cluster"] = [str(c) for c in clusters] # Match length of filtered_df
                    fig_cluster = px.scatter(
                        filtered_df, x="win_rate_custom", y="profit_factor_custom",
                        color="cluster", title="Strategy DNA Clusters"
                    )
                    st.plotly_chart(fig_cluster, use_container_width=True)
                
                elif "Hexbin" in viz_choice:
                    p1 = st.selectbox("X Axis (Param)", importance.index.tolist(), index=0)
                    p2 = st.selectbox("Y Axis (Param)", importance.index.tolist(), index=1 if len(importance)>1 else 0)
                    fig_hex = px.density_heatmap(features_df, x=p1, y=p2, z="roi_custom", histfunc="avg", title="Density of Success Heatmap")
                    st.plotly_chart(fig_hex, use_container_width=True)

                elif "Box Plots" in viz_choice:
                    p_box = st.selectbox("Target Parameter for ROI Distribution", importance.index.tolist())
                    # Create bins for the parameter
                    features_df["bin"] = pd.qcut(features_df[p_box], q=8, duplicates="drop").astype(str)
                    fig_box = px.box(features_df, x="bin", y="roi_custom", points="all", title=f"ROI Distribution across {p_box}")
                    st.plotly_chart(fig_box, use_container_width=True)

                elif "3D Surface" in viz_choice:
                    p1_3d = st.selectbox("X (Param)", importance.index.tolist(), index=0)
                    p2_3d = st.selectbox("Y (Param)", importance.index.tolist(), index=1 if len(importance)>1 else 0)
                    fig_3d = px.scatter_3d(features_df, x=p1_3d, y=p2_3d, z="roi_custom", color="roi_custom", title="ROI Landscape")
                    st.plotly_chart(fig_3d, use_container_width=True)

        except Exception as e:
            st.error(f"Error generating Data Science insights: {e}")
            if "parameters" not in filtered_df.columns:
                st.info("💡 Data might be stale. Please wait for aggregation to finish or refresh.")

if __name__ == "__main__":
    main()
