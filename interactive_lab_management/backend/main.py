import sys
import os
import requests
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware # Import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from datetime import datetime
import json
import numpy as np
import pandas as pd
import google.generativeai as genai
from statsmodels.tsa.seasonal import seasonal_decompose
import traceback # Import traceback

# Add the pyHaasAPI project directory to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from utils.auth.authenticator import authenticator
from pyHaasAPI import api
from pyHaasAPI.model import LabDetails, GetBacktestResultRequest, StartLabExecutionRequest
from models import Base, Script, Backtest, Parameter, ParameterHistory, ParameterTemplate

# Load the .env file from the root of the pyHaasAPI project
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
load_dotenv(dotenv_path=dotenv_path)

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("Warning: GEMINI_API environment variable not set. Gemini features will be disabled.")

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """Calculate Sharpe Ratio."""
    if returns.empty or returns.std() == 0:
        return 0.0
    excess_returns = returns - risk_free_rate
    return np.mean(excess_returns) / np.std(excess_returns)

def calculate_sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """Calculate Sortino Ratio."""
    if returns.empty:
        return 0.0
    downside_returns = returns[returns < risk_free_rate] - risk_free_rate
    if downside_returns.empty or np.std(downside_returns) == 0:
        return 0.0
    return np.mean(returns - risk_free_rate) / np.std(downside_returns)

def get_qualitative_assessment(roi: float, max_drawdown: float) -> str:
    """Provide a qualitative assessment based on ROI and Max Drawdown."""
    if roi > 20 and max_drawdown < 10:
        return "Excellent: High Profit, Low Risk"
    elif roi > 10 and max_drawdown < 15:
        return "Good: Solid Profit, Moderate Risk"
    elif roi > 5 and max_drawdown < 20:
        return "Fair: Decent Profit, Acceptable Risk"
    elif roi > 0 and max_drawdown < 25:
        return "Acceptable: Some Profit, Manageable Risk"
    else:
        return "Needs Improvement: Low Profit or High Risk"

@app.post("/login")
def login(email: str = None, password: str = None, host: str = None, port: int = None):
    # If credentials are provided, use them
    if email and password:
        # If host and port are also provided, update the .env file
        if host and port:
            with open(dotenv_path, "a") as f:
                f.write(f"\nAPI_HOST={host}")
                f.write(f"\nAPI_PORT={port}")
        
        # Update the .env file with the new credentials
        with open(dotenv_path, "a") as f:
            f.write(f"\nAPI_EMAIL={email}")
            f.write(f"\nAPI_PASSWORD={password}")
            
        # Reload the environment variables
        load_dotenv(dotenv_path=dotenv_path, override=True)

    # Authenticate with the Haas API
    success = authenticator.authenticate()
    if not success:
        raise HTTPException(status_code=401, detail="Authentication failed")
    return {"message": "Authentication successful"}

@app.get("/status")
def get_status():
    # Check if the .env file exists and contains credentials
    api_email = os.getenv("API_EMAIL")
    api_password = os.getenv("API_PASSWORD")
    
    if not api_email or not api_password:
        # If credentials are not found, check if the server is alive
        api_host = os.getenv("API_HOST", "127.0.0.1")
        api_port = os.getenv("API_PORT", 8090)
        
        try:
            response = requests.get(f"http://{api_host}:{api_port}")
            if response.status_code == 200:
                return {"status": "needs_creds"}
            else:
                return {"status": "needs_server"}
        except requests.exceptions.ConnectionError:
            return {"status": "needs_server"}
            
    return {"status": "ok"}

@app.get("/labs")
def get_labs():
    if not authenticator.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        executor = authenticator.get_executor()
        labs = api.get_all_labs(executor)
        return labs
    except Exception as e:
        # Log the full traceback for debugging
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch labs: {e}")

@app.get("/labs/{lab_id}")
def get_lab_details(lab_id: str):
    if not authenticator.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        executor = authenticator.get_executor()
        lab_details = api.get_lab_details(executor, lab_id)
        return lab_details
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/labs/{lab_id}")
def update_lab_details(lab_id: str, lab_details: LabDetails):
    if not authenticator.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        executor = authenticator.get_executor()
        updated_lab = api.update_lab_details(executor, lab_details)
        return updated_lab
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/labs/{lab_id}/start-backtest")
def start_lab_backtest(lab_id: str, start_unix: int, end_unix: int):
    if not authenticator.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        executor = authenticator.get_executor()
        request = StartLabExecutionRequest(
            lab_id=lab_id,
            start_unix=start_unix,
            end_unix=end_unix,
            send_email=False # We can make this configurable later
        )
        result = api.start_lab_execution(executor, request)
        return {"message": "Backtest started successfully", "result": result}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/labs/{lab_id}/status")
def get_lab_status(lab_id: str):
    if not authenticator.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        executor = authenticator.get_executor()
        status = api.get_lab_execution_update(executor, lab_id)
        return status
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/backtests/process")
def process_backtest_results(lab_id: str, backtest_id: str, db: Session = Depends(get_db)):
    if not authenticator.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        executor = authenticator.get_executor()

        # Get backtest results
        backtest_result_req = GetBacktestResultRequest(
            lab_id=lab_id,
            next_page_id=0,
            page_lenght=1000 # Fetch all results for now
        )
        backtest_results = api.get_backtest_result(executor, backtest_result_req)
        
        # Get backtest log
        backtest_log = api.get_backtest_log(executor, lab_id, backtest_id)

        # Get backtest chart (for trades)
        backtest_chart = api.get_backtest_chart(executor, lab_id, backtest_id)
        trades_data = backtest_chart.get("Trades", []) if backtest_chart else []

        # Find the specific backtest item by backtest_id
        target_backtest_item = None
        if backtest_results and backtest_results.items:
            for item in backtest_results.items:
                if item.backtest_id == backtest_id:
                    target_backtest_item = item
                    break
        
        if not target_backtest_item:
            raise HTTPException(status_code=404, detail="Backtest not found in results")

        # Get lab details to extract script_id and market
        lab_details = api.get_lab_details(executor, lab_id)
        script_id = lab_details.script_id
        market = lab_details.settings.market_tag

        # Calculate performance metrics
        sharpe_ratio = 0.0
        sortino_ratio = 0.0
        if trades_data:
            # Assuming trades_data has a 'Profit' key for individual trade profits
            # You might need to adjust this based on the actual structure of your trade data
            trade_profits = pd.Series([trade.get('Profit', 0) for trade in trades_data])
            sharpe_ratio = calculate_sharpe_ratio(trade_profits)
            sortino_ratio = calculate_sortino_ratio(trade_profits)

        qualitative_assessment = get_qualitative_assessment(
            target_backtest_item.summary.ReturnOnInvestment,
            target_backtest_item.summary.MaxDrawdown
        )

        # Store in database
        # First, ensure the script exists in our DB
        db_script = db.query(Script).filter(Script.id == script_id).first()
        if not db_script:
            db_script = Script(id=script_id, name=lab_details.script_name)
            db.add(db_script)
            db.commit()
            db.refresh(db_script)

        # Create Backtest entry
        new_backtest = Backtest(
            script_id=script_id,
            market=market,
            start_time=datetime.fromtimestamp(target_backtest_item.summary.BacktestStartUnix),
            end_time=datetime.fromtimestamp(target_backtest_item.summary.BacktestEndUnix),
            roi=target_backtest_item.summary.ReturnOnInvestment,
            max_drawdown=target_backtest_item.summary.MaxDrawdown,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            qualitative_assessment=qualitative_assessment,
            log=json.dumps(backtest_log),
            trades=json.dumps(trades_data)
        )
        db.add(new_backtest)
        db.commit()
        db.refresh(new_backtest)

        # Store parameter history (simplified for now, assuming current lab params are what was used)
        for param in lab_details.parameters:
            db_parameter = db.query(Parameter).filter_by(key=param.key, script_id=script_id).first()
            if not db_parameter:
                db_parameter = Parameter(key=param.key, script_id=script_id)
                db.add(db_parameter)
                db.commit()
                db.refresh(db_parameter)
            
            # Assuming 'options' contains the value or range. This needs refinement based on actual data structure.
            min_val = None
            max_val = None
            if param.options and len(param.options) > 0:
                if isinstance(param.options[0], (int, float)):
                    min_val = param.options[0]
                    max_val = param.options[0]
                elif isinstance(param.options[0], dict) and "Min" in param.options[0] and "Max" in param.options[0]:
                    min_val = param.options[0]["Min"]
                    max_val = param.options[0]["Max"]

            if min_val is not None and max_val is not None:
                new_param_history = ParameterHistory(
                    parameter_id=db_parameter.id,
                    backtest_id=new_backtest.id,
                    min_value=min_val,
                    max_value=max_val
                )
                db.add(new_param_history)
        db.commit()

        return {"message": "Backtest results processed and stored successfully", "backtest_id": new_backtest.id}
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/backtests")
def get_backtests(script_id: str = None, db: Session = Depends(get_db)):
    query = db.query(Backtest)
    if script_id:
        query = query.filter(Backtest.script_id == script_id)
    return query.all()

@app.get("/backtests/{backtest_id}")
def get_backtest_details(backtest_id: int, db: Session = Depends(get_db)):
    backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found.")
    return backtest

@app.post("/gemini/generate-params")
def generate_gemini_params(prompt: str, backtest_id: int, db: Session = Depends(get_db)):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key not configured.")

    # Retrieve backtest analysis from the database
    backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found.")

    script = db.query(Script).filter(Script.id == backtest.script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found for this backtest.")

    # Construct a detailed prompt for Gemini
    gemini_prompt = f"""You are an expert in trading strategy optimization. \nGiven the following backtest results and a user's request, suggest new parameter ranges for the script. \nProvide the output as a JSON object with parameter keys and their suggested min/max values. \nOnly include parameters that are relevant to the optimization based on the context. \n\nBacktest Details:\n  Script Name: {script.name}\n  Market: {backtest.market}\n  Backtest Period: {backtest.start_time} to {backtest.end_time}\n  ROI: {backtest.roi:.2f}%\n  Max Drawdown: {backtest.max_drawdown:.2f}%\n  Sharpe Ratio: {backtest.sharpe_ratio:.2f}\n  Sortino Ratio: {backtest.sortino_ratio:.2f}\n  Qualitative Assessment: {backtest.qualitative_assessment}\n\nUser Request: {prompt}\n\nConsider the script's existing parameters and their typical ranges. Focus on improving the strategy's performance based on the user's request and the backtest's weaknesses. If the user asks for something specific, prioritize that. Otherwise, aim for a better risk-adjusted return. \n\nExample JSON output:\n{{\n  \"Parameter1\": {{\"Min\": 10, \"Max\": 20}},\n  \"Parameter2\": {{\"Min\": 0.5, \"Max\": 1.5}}\n}}\n"""

    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(gemini_prompt)
        
        # Attempt to parse the response as JSON
        suggested_params = json.loads(response.text)
        return suggested_params
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/templates")
def create_template(template_name: str, script_id: str, parameters: dict, db: Session = Depends(get_db)):
    # Check if script exists
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found.")

    # Check if template name already exists for this script
    existing_template = db.query(ParameterTemplate).filter_by(name=template_name, script_id=script_id).first()
    if existing_template:
        raise HTTPException(status_code=409, detail="Template with this name already exists for this script.")

    new_template = ParameterTemplate(
        script_id=script_id,
        name=template_name,
        parameters_json=json.dumps(parameters)
    )
    db.add(new_template)
    db.commit()
    db.refresh(new_template)
    return new_template

@app.get("/templates")
def get_templates(script_id: str = None, db: Session = Depends(get_db)):
    query = db.query(ParameterTemplate)
    if script_id:
        query = query.filter(ParameterTemplate.script_id == script_id)
    templates = query.all()
    # Deserialize parameters_json before returning
    for template in templates:
        template.parameters_json = json.loads(template.parameters_json)
    return templates

@app.get("/templates/{template_id}")
def get_template(template_id: int, db: Session = Depends(get_db)):
    template = db.query(ParameterTemplate).filter(ParameterTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found.")
    template.parameters_json = json.loads(template.parameters_json)
    return template

@app.post("/backtests/correlation")
def get_correlation_matrix(backtest_ids: list[int], db: Session = Depends(get_db)):
    if not backtest_ids:
        raise HTTPException(status_code=400, detail="No backtest IDs provided.")

    all_returns = pd.DataFrame()
    for bt_id in backtest_ids:
        backtest = db.query(Backtest).filter(Backtest.id == bt_id).first()
        if not backtest:
            raise HTTPException(status_code=404, detail=f"Backtest with ID {bt_id} not found.")
        
        trades_data = json.loads(backtest.trades)
        if not trades_data:
            continue

        # Assuming each trade has a 'Timestamp' and 'Profit'
        # Convert to datetime and set as index
        df = pd.DataFrame(trades_data)
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='s') # Assuming Unix timestamp
        df = df.set_index('Timestamp')

        # Calculate daily returns (or per-trade returns, depending on granularity)
        # For simplicity, let's assume daily returns based on cumulative profit
        daily_profit = df['Profit'].resample('D').sum().fillna(0)
        daily_returns = daily_profit.pct_change().fillna(0)
        
        all_returns[f'Backtest_{bt_id}'] = daily_returns

    if all_returns.empty:
        return {"message": "No sufficient trade data to calculate correlation.", "correlation_matrix": {}}

    correlation_matrix = all_returns.corr().fillna(0).to_dict()
    return {"correlation_matrix": correlation_matrix}

@app.post("/backtests/{backtest_id}/monte-carlo")
def run_monte_carlo(backtest_id: int, num_simulations: int = 100, num_steps: int = 252, db: Session = Depends(get_db)):
    backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found.")

    trades_data = json.loads(backtest.trades)
    if not trades_data:
        raise HTTPException(status_code=400, detail="No trade data available for Monte Carlo simulation.")

    # Extract daily returns from trades (simplified, assuming daily profit for now)
    df = pd.DataFrame(trades_data)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='s')
    df = df.set_index('Timestamp')
    daily_profit = df['Profit'].resample('D').sum().fillna(0)
    daily_returns = daily_profit.pct_change().fillna(0)

    if daily_returns.empty or daily_returns.std() == 0:
        raise HTTPException(status_code=400, detail="Insufficient data for Monte Carlo simulation.")

    # Monte Carlo Simulation
    results = []
    last_return = daily_returns.iloc[-1] if not daily_returns.empty else 0
    for _ in range(num_simulations):
        # Generate random returns based on historical distribution
        simulated_returns = np.random.choice(daily_returns, num_steps)
        # Simulate equity path (starting from 1 for percentage change)
        simulated_equity = np.cumprod(1 + simulated_returns)
        results.append(simulated_equity[-1]) # Final equity value

    return {"monte_carlo_results": results}

@app.get("/backtests/{backtest_id}/time-series-decomposition")
def get_time_series_decomposition(backtest_id: int, db: Session = Depends(get_db)):
    backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found.")

    trades_data = json.loads(backtest.trades)
    if not trades_data:
        raise HTTPException(status_code=400, detail="No trade data available for time series decomposition.")

    df = pd.DataFrame(trades_data)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='s')
    df = df.set_index('Timestamp')
    
    # For time series decomposition, we need a series with a regular frequency
    # Let's use daily cumulative profit for simplicity
    daily_profit = df['Profit'].resample('D').sum().fillna(0)
    cumulative_profit = daily_profit.cumsum()

    if len(cumulative_profit) < 2: # Need at least 2 points for decomposition
        raise HTTPException(status_code=400, detail="Insufficient data for time series decomposition.")

    # Perform seasonal decomposition
    # Assuming additive model for now, and a period (e.g., 7 for weekly seasonality if data is daily)
    # The period might need to be adjusted based on the actual data and expected seasonality
    try:
        decomposition = seasonal_decompose(cumulative_profit, model='additive', period=7)
        return {
            "observed": decomposition.observed.tolist(),
            "trend": decomposition.trend.tolist(),
            "seasonal": decomposition.seasonal.tolist(),
            "resid": decomposition.resid.tolist()
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))