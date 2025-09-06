### Backtest Runtime Response Structure

This document outlines the structure of the `backtest_runtime` response obtained from the HaasOnline API (e.g., via `api.get_backtest_runtime`). This response provides detailed execution data for a specific backtest.

```json
{
  "Success": true, // Boolean: Indicates if the API call was successful.
  "Error": "",     // String: Error message if Success is false, otherwise empty.
  "Data": {        // Object: Contains the actual runtime data.
    "Chart": {
      "Guid": "...", // String: Unique identifier for the chart.
      "Interval": 1, // Integer: Chart interval.
      "Charts": {},  // Object: Contains chart data lines (e.g., indicators, price series).
      "Colors": { /* ... color settings for the chart ... */ }, // Object: Chart color configurations.
      "IsLastPartition": true, // Boolean: Indicates if it's the last partition of chart data.
      "Status": 1    // Integer: Status code for the chart data.
    },
    "CompilerErrors": [], // Array: List of any compiler errors encountered during script execution.
    "Reports": {          // Object: Contains detailed financial reports and summary metrics.
      // Key is typically a combination of Account ID and Market Tag (e.g., "6bccabce-9bbe-42a3-a6ee-0cc4bf1e0cbe_BINANCEFUTURES_ETH_USDT_PERPETUAL")
      "ACCOUNT_ID_MARKET_TAG": {
        "AID": "...", // String: Account ID.
        "M": "...",   // String: Market Tag.
        "AL": "...",  // String: Asset Label (e.g., ETH).
        "ML": "...",  // String: Margin Label (e.g., USDT).
        "PL": "...",  // String: Profit Label (e.g., USDT).
        "F": { /* ... Fee details ... */ }, // Object: Fee details.
        "PR": { /* ... Profit/Return details ... */ }, // Object: Profit/Return details (includes ROI, Realized Profit).
        "O": { /* ... Order details ... */ }, // Object: Order details (includes Filled Orders).
        "P": { /* ... Position details ... */ }, // Object: Position details (includes Closed Positions).
        "T": { /* ... various trade-related statistics ... */ } // Object: Trade statistics.
      }
    },
    "CustomReport": {}, // Object: Custom report data.
    "ScriptNote": "",   // String: Notes from the script.
    "TrackedOrderLimit": 150, // Integer: Limit for tracked orders.
    "OpenOrders": [],         // Array: List of open orders.
    "FailedOrders": [],       // Array: List of failed orders.
    "ManagedLongPosition": { /* ... details of managed long position ... */ }, // Object: Managed long position details.
    "ManagedShortPosition": { /* ... details of managed short position ... */ }, // Object: Managed short position details.
    "UnmanagedPositions": [], // Array: List of unmanaged positions.
    "FinishedPositions": [    // Array: List of finished positions (each contains entry/exit orders).
      { /* ... Position object structure (see example in prompt) ... */ }
    ],
    "InputFields": { // Object: **CRITICAL - Contains the parameters used for this specific backtest run.**
      // Each key is the parameter's full key (e.g., "3-3-17-22.Trade amount by margin").
      "PARAMETER_KEY": {
        "T": 2,      // Integer: Parameter Type (matches ParameterType enum: 0=INTEGER, 1=DECIMAL, 2=BOOLEAN, 3=STRING, 4=SELECTION).
        "ST": -1,    // Integer: Sub-Type (appears to be -1 consistently).
        "G": "TRADE SETTINGS", // String: Group name for the parameter.
        "K": "...", // String: Full parameter key (redundant with outer key).
        "EK": "...", // String: "Extended Key" - numerical prefix of the key.
        "N": "...", // String: Human-readable Name of the parameter.
        "TT": "",    // String: Tooltip or description for the parameter.
        "V": "...", // String: **The actual value used for this parameter in the backtest.**
        "D": "...", // String: Default value for the parameter.
        "O": null,   // Mixed: Options for SELECTION types (dictionary of key-value pairs), otherwise null.
        "MIN": 0.0,  // Float: Minimum value for numerical parameters.
        "MAX": 0.0   // Float: Maximum value for numerical parameters.
      }
      // ... more InputFields objects for each parameter ...
    },
    "ScriptMemory": {}, // Object: Script's internal memory.
    "LocalMemory": {},  // Object: Local memory.
    "RedisKeys": [],    // Array: Redis keys.
    "Files": {},        // Object: Files.
    "LogId": "...", // String: Log ID.
    "LogCount": 0,      // Integer: Log count.
    "ExecutionLog": [], // Array: List of log entries from the backtest execution.
    "UserId": "...", // String: User ID.
    "BotId": "...", // String: Bot ID.
    "BotName": "",      // String: Bot Name.
    "ScriptId": "...", // String: Script ID.
    "ScriptName": "...", // String: Script Name.
    "Activated": true,  // Boolean: Is bot activated.
    "Paused": false,    // Boolean: Is bot paused.
    "IsWhiteLabel": false, // Boolean: Is white label.
    "ActivatedSince": 0, // Integer: Activated since timestamp (Unix).
    "DeactivatedSince": 0, // Integer: Deactivated since timestamp (Unix).
    "DeactivatedReason": "", // String: Deactivated reason.
    "AccountId": "...", // String: Account ID.
    "PriceMarket": "...", // String: Price Market.
    "Leverage": 0.0, // Float: Leverage.
    "MarginMode": 0,    // Integer: Margin Mode.
    "PositionMode": 0,  // Integer: Position Mode.
    "TradeAmount": 0.0, // Float: Trade Amount.
    "OrderTemplate": 0, // Integer: Order Template.
    "DefaultInterval": 0, // Integer: Default Interval.
    "DefaultChartType": 0, // Integer: Default Chart Type.
    "HideTradeAmountSettings": false, // Boolean: Hide Trade Amount Settings.
    "HideOrderSettings": false, // Boolean: Hide Order Settings.
    "OrderPersistenceEnabled": false, // Boolean: Order Persistence Enabled.
    "OrderPersistenceLimit": 0, // Integer: Order Persistence Limit.
    "EnableHighSpeedUpdates": false, // Boolean: Enable High Speed Updates.
    "UpdateAfterCompletedOrder": false, // Boolean: Update After Completed Order.
    "IndicatorContainerLogs": false, // Boolean: Indicator Container Logs.
    "IsScriptOk": false, // Boolean: Is Script OK.
    "TradeAmountError": false, // Boolean: Trade Amount Error.
    "ScriptTradeAmountError": false, // Boolean: Script Trade Amount Error.
    "UpdateCounter": 0, // Integer: Update Counter.
    "IsSpotSupported": false, // Boolean: Is Spot Supported.
    "IsMarginSupported": false, // Boolean: Is Margin Supported.
    "IsLeverageSupported": false, // Boolean: Is Leverage Supported.
    "IsManagedTrading": false, // Boolean: Is Managed Trading.
    "IsOneDirection": false, // Boolean: Is One Direction.
    "IsMultiMarket": false, // Boolean: Is Multi Market.
    "IsRemoteSignalBased": false, // Boolean: Is Remote Signal Based.
    "IsWebHookBased": false, // Boolean: Is Web Hook Based.
    "WebHookSignalId": "", // String: Web Hook Signal ID.
    "IsTAUsed": false, // Boolean: Is TA Used.
    "Timestamp": 0, // Integer: Timestamp (Unix).
    "MinuteTimestamp": 0, // Integer: Minute Timestamp (Unix).
    "LastUpdateTimestamp": 0 // Integer: Last Update Timestamp (Unix).
  }
}
```