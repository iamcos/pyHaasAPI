{
  "Success": true,
  "Error": "",
  "Data": {
    "SC": "--  Stoch RSI Custom Command  HaasScript v3 clean version\nDefineCommand(\"CC_StorchRSI\", \"Stochastic RSI custom command\")\n\n-- Inputs\nlocal src      = DefineParameter(ListNumberType, \"source\", \"\", false, ClosePrices(), \"ClosePrices\")\nlocal rsiLen   = DefineParameter(NumberType, \"rsiLen\", \"RSI Length\", false, 14, \"\")\nlocal stochLen = DefineParameter(NumberType, \"stochLen\", \"Stoch Lookback\", false, 14, \"\")\nlocal smoothK  = DefineParameter(NumberType, \"smoothK\", \"Smooth K\", false, 3, \"\")\nlocal smoothD  = DefineParameter(NumberType, \"smoothD\", \"Smooth D\", false, 3, \"\")\nlocal ob       = DefineParameter(NumberType, \"ob\", \"Overbought\", false, 80, \"\")\nlocal os       = DefineParameter(NumberType, \"os\", \"Oversold\", false, 20, \"\")\n\n-- Outputs\nlocal out = { k = {}, d = {}, signal = {} }\n\n-- RSI\nlocal rsi = RSI(src, rsiLen)\nif rsi == nil or #rsi < stochLen then\n    DefineOutput(TableDynamicType, out, \"Result\")\n    return out\nend\n\n-- Safe getter\nlocal function barVal(series, idx)\n    if idx < 1 or idx > #series then\n        return series[#series]\n    end\n    return series[idx]\nend\n\n-- Raw Stoch RSI\nfor i = 1, #rsi do\n    local low = barVal(rsi, i)\n    local high = barVal(rsi, i)\n    for j = i, i + stochLen - 1 do\n        local v = barVal(rsi, j)\n        if v < low then low = v end\n        if v > high then high = v end\n    end\n\n    local curr = barVal(rsi, i)\n    local raw = 50\n    if high ~= low then raw = ((curr - low) / (high - low)) * 100 end\n    out.k[i] = raw\nend\n\n-- Smooth K & D\nfor i = 1, #out.k do\n    local sumK, countK = 0, 0\n    for j = i, i + smoothK - 1 do sumK = sumK + barVal(out.k, j) countK = countK + 1 end\n    out.k[i] = sumK / countK\n\n    local sumD, countD = 0, 0\n    for j = i, i + smoothD - 1 do sumD = sumD + barVal(out.k, j) countD = countD + 1 end\n    out.d[i] = sumD / countD\n\n    local prevK = barVal(out.k, i+1)\n    local prevD = barVal(out.d, i+1)\n    local s = 0\n    if prevK <= prevD and out.k[i] > out.d[i] and out.k[i] < os then s = 1 end\n    if prevK >= prevD and out.k[i] < out.d[i] and out.k[i] > ob then s = -1 end\n    out.signal[i] = s\nend\n\n--  HaasScript v3 correct Plot (4 args max)\nPlot(0, \"K\", out.k[1], ColorBlue)\nPlot(0, \"D\", out.d[1], ColorOrange)\nPlot(0, \"OB\", ob, ColorRed)\nPlot(0, \"OS\", os, ColorGreen)\n\n-- Final output\nDefineOutput(TableDynamicType, out, \"Result\")\nreturn out\n",
    "CR": {
      "IV": false,
      "C": {
        "CN": null,
        "CD": null,
        "MC": false,
        "US": false,
        "UL": false,
        "OH": false,
        "P": [],
        "O": {
          "Index": 0,
          "Name": "",
          "Type": 10,
          "IsRequired": false,
          "IsHidden": false,
          "IsField": false,
          "AllowNull": false,
          "Description": "",
          "ScriptType": null,
          "Suggestion": null
        },
        "OI": []
      },
      "CR": [],
      "CL": [
        "1773164118 ||| 0 ||| Compiling script...",
        "1773164118 ||| 0 ||| TIP: Using OptimizedForInterval() in combination with the technical analysis commands will improve the backtest speed.",
        "1773164118 ||| 3 ||| ERROR:  - TableDynamicType",
        "1773164118 ||| 3 ||| ERROR:  - ColorRed",
        "1773164118 ||| 3 ||| ERROR:  - ColorOrange",
        "1773164118 ||| 3 ||| ERROR:  - ColorGreen",
        "1773164118 ||| 3 ||| ERROR:  - ColorBlue",
        "1773164118 ||| 3 ||| ERROR: Unknown references:"
      ],
      "LCE": [],
      "VCE": [],
      "I": [],
      "O": 500,
      "HT": false,
      "HO": false,
      "SS": false,
      "MS": false,
      "LS": false,
      "MT": false,
      "OD": false,
      "MM": false,
      "RSB": false,
      "TAU": false
    },
    "UID": "02f3cd9afebb46bf9d4c9b6ef5e6e823",
    "SID": "9fb39e76d6c546879b2eb924dd1f2d60",
    "SN": "CC_StorchRSI",
    "SD": "",
    "ST": 0,
    "SS": 0,
    "CN": "",
    "IC": true,
    "IV": false,
    "CU": 1762240376,
    "UU": 1773164117,
    "FID": -1
  }
}
