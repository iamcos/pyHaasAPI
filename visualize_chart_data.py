
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import mplfinance as mpf

def visualize_chart_data(json_file_path="chart_sample.json", output_image_path="chart_visualization.png"):
    """
    Loads chart data from a JSON file, processes it, and visualizes it.
    """
    with open(json_file_path, 'r') as f:
        data = json.load(f)

    # Extract candlestick data
    candles_data = data.get("Charts", {}).get("0", {}).get("PricePlot", {}).get("Candles", {})
    market_name = data.get("Charts", {}).get("0", {}).get("PricePlot", {}).get("Market", "Unknown Market")

    ohlc_data = []
    for timestamp_str, candle in candles_data.items():
        timestamp = pd.to_datetime(int(timestamp_str), unit='s')
        ohlc_data.append([
            timestamp,
            candle['O'],
            candle['H'],
            candle['L'],
            candle['C'],
            candle['V']
        ])

    df_ohlc = pd.DataFrame(ohlc_data, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df_ohlc['Date'] = pd.to_datetime(df_ohlc['Date']) # Convert to datetime objects
    df_ohlc = df_ohlc.sort_values('Date')
    df_ohlc.set_index('Date', inplace=True) # Set Date as index

    # Prepare data for mplfinance
    df_ohlc = df_ohlc[['Open', 'High', 'Low', 'Close', 'Volume']]

    apds = []
    panel_counter = 1 # Start new panels from 1 (0 is for main OHLC)

    # Iterate through all charts to find indicator data
    for chart_key, chart_data in data.get("Charts", {}).items():
        if "DataLines" in chart_data:
            for line_key, line_info in chart_data["DataLines"].items():
                line_name = line_info.get("Name", line_key)
                data_points = line_info.get("DataPoints", {})

                if data_points:
                    timestamps = []
                    values = []
                    for ts_str, val in data_points.items():
                        timestamps.append(pd.to_datetime(int(ts_str), unit='s'))
                        values.append(val)

                    df_line = pd.DataFrame({'Date': timestamps, 'Value': values}).sort_values('Date')
                    df_line.set_index('Date', inplace=True)

                    # Align with OHLC index
                    aligned_values = pd.Series(index=df_ohlc.index, dtype=float)
                    aligned_values.loc[df_line.index] = df_line['Value']

                    # Determine panel and color based on indicator name
                    color = 'blue'
                    panel = 0 # Default to main panel
                    secondary_y = False
                    
                    if "BBands" in line_name:
                        color = 'orange'
                        panel = 0 # BBands usually on same panel as price
                    elif "MACD" in line_name:
                        color = 'purple'
                        panel = panel_counter
                        panel_counter += 1
                    elif "RSI" in line_name:
                        color = 'green'
                        panel = panel_counter
                        panel_counter += 1
                        secondary_y = True # RSI usually has its own scale (0-100)
                    # Handle buy/sell signals as scatter plots
                    elif "rgba(0, 255, 0, 1.00)" in line_name: # Assuming green is buy signal
                        buy_signal_plot_data = pd.Series(index=df_ohlc.index, dtype=float)
                        buy_signal_plot_data.loc[aligned_values[aligned_values == 1.0].index] = df_ohlc['Close'].loc[aligned_values[aligned_values == 1.0].index]
                        if not buy_signal_plot_data.dropna().empty:
                            apds.append(
                                mpf.make_addplot(buy_signal_plot_data, type='scatter', marker='^', markersize=100, color='green', panel=0, title='Buy Signal')
                            )
                    elif "rgba(255, 0, 0, 1.00)" in line_name: # Assuming red is sell signal
                        sell_signal_plot_data = pd.Series(index=df_ohlc.index, dtype=float)
                        sell_signal_plot_data.loc[aligned_values[aligned_values == 1.0].index] = df_ohlc['Close'].loc[aligned_values[aligned_values == 1.0].index]
                        if not sell_signal_plot_data.dropna().empty:
                            apds.append(
                                mpf.make_addplot(sell_signal_plot_data, type='scatter', marker='v', markersize=100, color='red', panel=0, title='Sell Signal')
                            )
                    else:
                        # Default plotting for other data lines
                        if not aligned_values.empty:
                            apds.append(
                                mpf.make_addplot(aligned_values, color=color, linestyle='-', panel=panel, secondary_y=secondary_y, title=line_name)
                            )
    
    print(f"Found {len(apds)} addplots.")
    # Debugging: Print the titles of the addplots
    for apd in apds:
        print(f"Addplot Title: {apd.get('title')}, Panel: {apd.get('panel')}, Secondary_y: {apd.get('secondary_y')}")

    # Plot using mplfinance
    mpf.plot(df_ohlc,
             type='candle',
             style='yahoo',
             title=f"Backtest Chart for {market_name} with Signal",
             ylabel=f"{market_name} Price",
             volume=True,
             addplot=apds,
             figsize=(25, 12), # Make the chart wider and less tall
             savefig=output_image_path)
    print(f"Chart visualization saved to {output_image_path}")

if __name__ == "__main__":
    visualize_chart_data()
