# Chart Data Discoveries (from `get_backtest_chart` API)

This document details the structure and data types found in the `chart_sample.json` file, which is generated from the `get_backtest_chart` API call in `pyHaasAPI`. Understanding this structure is crucial for accurate data extraction and visualization.

## Overall JSON Structure

The `chart_sample.json` file is a JSON object with the following top-level keys:

*   `Guid` (string): A unique identifier for the chart data.
*   `Interval` (integer): The time interval of the chart data (e.g., 1 for 1-minute candles).
*   `Charts` (object): Contains multiple chart plots, each identified by a key (e.g., "0", "-1").
*   `Colors` (object): Defines color schemes for the chart elements.
*   `IsLastPartition` (boolean): Indicates if this is the last partition of data.
*   `Status` (integer): The status of the chart data retrieval.

## `Charts` Object Details

The `Charts` object contains individual plot configurations. In our observed `chart_sample.json`, we typically find two main plots:

### `Charts["0"]`: Price Plot (Candlestick Data)

This plot contains the primary price data, usually in candlestick format.

*   `PlotId` (string): Unique identifier for this plot.
*   `PlotIndex` (integer): Index of the plot (e.g., 0 for the main price plot).
*   `Title` (string): Title of the plot (e.g., "Haasonline Original - MadHatter Bot").
*   `Height` (float): Height of the plot.
*   `IsSignalPlot` (boolean): Indicates if this plot is primarily for signals (usually `false` for the main price plot).
*   `RightAxis` (object): Configuration for the right Y-axis.
*   `LeftAxis` (object): Configuration for the left Y-axis.
*   `PricePlot` (object): Contains the actual candlestick data.
    *   `Market` (string): The market identifier (e.g., "BINANCE_AVAX_USDT_").
    *   `Interval` (integer): The interval of the candles (e.g., 1 for 1-minute).
    *   `Candles` (object): A dictionary where keys are Unix timestamps (as strings) and values are candlestick objects.
        *   **Candlestick Object Structure:**
            *   `O` (float): Open price.
            *   `H` (float): High price.
            *   `L` (float): Low price.
            *   `C` (float): Close price.
            *   `V` (float): Volume.
            *   `M` (boolean): Marker (purpose unknown, often `false`).
    *   `Colors` (object): Color settings for the candles.
    *   `Style` (integer): Plotting style.
    *   `Side` (integer): Side of the plot.
*   `DataLines` (object): Can contain additional lines plotted on this panel (e.g., moving averages, Bollinger Bands).
*   `Shapes` (object): Contains shape data (often empty if no shapes are defined).
*   `Annotations` (array): Contains annotation data (often empty).
*   `TradeAnnotations` (array): Contains trade annotation data (often empty).

### `Charts["-1"]`: Indicator and Signal Plot

This plot typically contains various indicators and signals, often overlaid or on a separate panel.

*   `PlotId` (string): Unique identifier for this plot.
*   `PlotIndex` (integer): Index of the plot (e.g., -1 for indicators/signals).
*   `Title` (string): Title of the plot (often empty).
*   `Height` (float): Height of the plot.
*   `IsSignalPlot` (boolean): Indicates if this plot is primarily for signals (usually `true`).
*   `RightAxis` (object): Configuration for the right Y-axis.
*   `LeftAxis` (object): Configuration for the left Y-axis.
*   `PricePlot` (object): Often empty or contains minimal data for this plot, as it's not the primary price display.
*   `DataLines` (object): A crucial section containing various indicator and signal lines. Keys are often color codes (e.g., "rgba(0, 255, 0, 1.00)") or indicator names (e.g., "MHB BBands Upper").
    *   **`DataLine` Object Structure:**
        *   `Guid` (string): Unique identifier for the data line.
        *   `Name` (string): Name of the data line (e.g., "MHB BBands Upper", "MHB Histogram", "MHB RSI").
        *   `Interval` (integer): Interval of the data points.
        *   `Color` (string): Color of the line.
        *   `Width` (float): Line width.
        *   `Type` (integer): Type of data line.
        *   `Style` (integer): Line style.
        *   `Decoration` (integer): Line decoration.
        *   `Side` (integer): Side of the plot.
        *   `LineShapeType` (integer): Shape type of the line.
        *   `Visible` (boolean): Visibility of the line.
        *   `Behind` (boolean): Whether the line is behind other elements.
        *   `IgnoreOnAxis` (boolean): Whether to ignore on axis.
        *   `DrawTrailingLine` (boolean): Whether to draw a trailing line.
        *   `FixedValue` (float): Fixed value for the line (if applicable).
        *   `ConnectedLines` (array): Connected lines (often empty).
        *   `DataSets` (array): Data sets (often empty).
        *   `DataPoints` (object): A dictionary where keys are Unix timestamps (as strings) and values are the data points for the line.
            *   **Data Types:** Values can be floats (for indicator values) or integers (for signals, typically `1.0` for an event).

## Key Data Types and Interpretation

*   **Candlestick Data (`Charts["0"].PricePlot.Candles`):**
    *   **Timestamps:** Unix timestamps (integers) representing the start of the candle period.
    *   **OHLCV:** Open, High, Low, Close, Volume are all `float` values.
*   **Indicator Data (`Charts["-1"].DataLines`):**
    *   **Timestamps:** Unix timestamps (integers) corresponding to the indicator value.
    *   **Values:** Typically `float` values representing the indicator's calculation (e.g., RSI value, MACD histogram value, Bollinger Band levels).
*   **Signal Data (`Charts["-1"].DataLines` with color names):**
    *   **Timestamps:** Unix timestamps (integers) where a signal event occurred.
    *   **Values:** Often `1.0` (float) to indicate the presence of a signal at that specific timestamp. These are best plotted as discrete scatter points rather than continuous lines.

## Example DataLine Names and Their Interpretation

*   `rgba(0, 255, 0, 1.00)`: Often represents a **Buy Signal**.
*   `rgba(255, 0, 0, 1.00)`: Often represents a **Sell Signal**.
*   `MHB BBands Upper`: Upper Bollinger Band.
*   `MHB BBands Middle`: Middle Bollinger Band (usually a Simple Moving Average).
*   `MHB BBands Lower`: Lower Bollinger Band.
*   `MHB Histogram`: MACD Histogram.
*   `MHB Short`: MACD Fast Line.
*   `MHB Long`: MACD Slow Line.
*   `MHB RSI`: Relative Strength Index (RSI).

This documentation will be updated as further insights into the chart data structure are gained.
