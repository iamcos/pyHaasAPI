import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables from the project root's .env file
load_dotenv(dotenv_path=os.path.abspath(os.path.join(os.path.dirname(__file__), '.env')))

NODE_SERVER_HOST = os.getenv("NODE_SERVER_HOST", "http://localhost")
NODE_SERVER_PORT = os.getenv("NODE_SERVER_PORT", "3000")
MCP_ENDPOINT = f"{NODE_SERVER_HOST}:{NODE_SERVER_PORT}/mcp"

def generate_haasscript_request(prompt: str, context_keywords: list = None, strategy_type: str = None):
    payload = {
        "jsonrpc": "2.0",
        "method": "tool_call",
        "params": {
            "tool_name": "generate_haasscript",
            "args": {
                "prompt": prompt,
                "context_keywords": context_keywords if context_keywords is not None else [],
                "strategy_type": strategy_type
            }
        }
    }
    headers = {"Content-Type": "application/json"}

    print(f"Sending request to: {MCP_ENDPOINT}")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(MCP_ENDPOINT, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
        return None

if __name__ == "__main__":
    strategy_prompt = """This is a versatile scalping strategy designed primarily for low timeframes (like 1-min, 3-min, or 5-min charts). Its core logic is based on a classic EMA (Exponential Moving Average) crossover system, which is then filtered by the VWAP (Volume-Weighted Average Price) to confirm the trade's direction in alignment with the market's current intraday sentiment.

The strategy is highly customizable, allowing traders to add layers of confirmation, control trade direction, and manage exits with precision.

Core Strategy Logic

The strategy's entry signals are generated when two primary conditions are met simultaneously:
Momentum Shift (EMA Crossover): It looks for a crossover between a fast EMA (default length 9) and a slow EMA (default length 21).
Buy Signal: The fast EMA crosses above the slow EMA, indicating a potential shift to bullish momentum.
Sell Signal: The fast EMA crosses below the slow EMA, indicating a potential shift to bearish momentum.
Trend/Sentiment Filter (VWAP): The crossover signal is only considered valid if the price is on the "correct" side of the VWAP.
For a Buy Signal: The price must be trading above the VWAP. This confirms that, on average, buyers are in control for the day.
For a Sell Signal: The price must be trading below the VWAP. This confirms that sellers are generally in control.


Confirmation Filters (Optional)

To increase the reliability of the signals and reduce false entries, the strategy includes two optional confirmation filters:
Price Action Filter (Engulfing Candle): If enabled (Use Price Action), the entry signal is only valid if the crossover candle is also an "engulfing" candle.
A Bullish Engulfing candle is a large green candle that completely "engulfs" the body of the previous smaller red candle, signaling strong buying pressure.
A Bearish Engulfing candle is a large red candle that engulfs the previous smaller green candle, signaling strong selling pressure.
Volume Filter (Volume Spike): If enabled (Use Volume Confirmation), the entry signal must be accompanied by a surge in volume. This is confirmed if the volume of the entry candle is greater than its recent moving average (default 20 periods). This ensures the move has strong participation behind it.


Exit Strategy

A position can be closed in one of three ways, creating a comprehensive exit plan:
Stop Loss (SL): A fixed stop loss is set at a level determined by a multiple of the Average True Range (ATR). For example, a 1.5 multiplier places the stop 1.5 times the current ATR value away from the entry price. This makes the stop dynamic, adapting to market volatility.
Take Profit (TP): A fixed take profit is also set using an ATR multiplier. By setting the TP multiplier higher than the SL multiplier (e.g., 2.0 for TP vs. 1.5 for SL), the strategy aims for a positive risk-to-reward ratio on each trade.
Exit on Opposite Signal (Reversal): If enabled, an open position will be closed automatically if a valid entry signal in the opposite direction appears. For example, if you are in a long trade and a valid short signal occurs, the strategy will exit the long position immediately. This feature turns the strategy into more of a reversal system.


Key Features & Customization

Trade Direction Control: You can enable or disable long and short trades independently using the Allow Longs and Allow Shorts toggles. This is useful for trading in harmony with a higher-timeframe trend (e.g., only allowing longs in a bull market).
Visual Plots: The strategy plots the Fast EMA, Slow EMA, and VWAP on the chart for easy visualization of the setup. It also plots up/down arrows to mark where valid buy and sell signals occurred.
Dynamic SL/TP Line Plotting: A standout feature is that the strategy automatically draws the exact Stop Loss and Take Profit price lines on the chart for every active trade. These lines appear when a trade is entered and disappear as soon as it is closed, providing a clear visual of your risk and reward targets.
Alerts: The script includes built-in alertcondition calls. This allows you to create alerts in TradingView that can notify you on your phone or execute trades automatically via a webhook when a long or short signal is generated."""

    keywords = ["EMA crossover", "VWAP", "scalping", "stop loss", "take profit", "engulfing candle", "volume spike", "ATR"]
    strategy = "scalping"

    response_data = generate_haasscript_request(strategy_prompt, keywords, strategy)

    if response_data:
        print("\nResponse from server:")
        print(json.dumps(response_data, indent=2))
    else:
        print("\nFailed to get a response from the server.")
