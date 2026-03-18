{
  "Success": true,
  "Error": "",
  "Data": {
    "SC": "DefineCommand('EasySuperTrend', 'EasySuperTrend indicator by pshai.')\n \nlocal chartIndex = DefineParameter(NumberType, 'chartIndex', 'The index on which to chart', true, 0, 'Number')\nlocal name = DefineParameter(StringType, 'name', 'Unique name of the indicator.', false, '', 'Text')\nlocal interval = DefineParameter(NumberType, 'interval', 'Used interval for price data. Default is 0 and the main interval will be used.', false, 0, 'Number,InputInterval')\n \nDefineIntervalOptimization(interval)\n \n-- Input fields for the indicator.\nInputGroupHeader('EasySuperTrend '..name..' Settings')\n \n-- Parameters\nlocal atrPeriod = Input('ATR Period Length', 22)\nlocal atrMult = Input('ATR Multiplier', 3)\nlocal wicks = Input('Use wicks', false)\n \n-- Data\nlocal h = HighPrices(interval)\nlocal l = LowPrices(interval)\nlocal c = ClosePrices(interval)\nlocal hl = HLPrices(interval)\nlocal atr = ATR(h, l, c, atrPeriod) * atrMult\n \n-- Stuff\nlocal dir = Load('dir', 1)\nlocal upperId = Load('uid', NewGuid())\nlocal lowerId = Load('lid', NewGuid())\nlocal result = SignalNone\n \nlocal run = function(offset)\n    if offset == nil then\n        offset = 1\n    end\n \n    -- Update short side\n    if dir == -1 then\n        local upper = ArrayGet(hl, offset) + ArrayGet(atr, offset)\n        local upperPrev = Load('upper', upper) -- load previous\n        local finalUpper = Min(upper, upperPrev) -- take min\n \n        -- if close cuts through upper, we switch to other side\n        if (c >= finalUpper) or (wicks and h >= finalUpper) then\n            dir = 1\n            Save('lower', ArrayGet(hl, offset) - ArrayGet(atr, offset)) -- \"reset\" lower line\n        end\n \n        Save('upper', finalUpper)\n        result = SignalSell -- set result\n \n        -- Plot\n        if offset <= 1 then\n            lowerId = NewGuid() -- reset lower id\n            Plot(chartIndex, name..' Short Stop', finalUpper, {c=Red, id=upperId})\n        end\n \n    -- update long side\n    elseif dir == 1 then\n        local lower = ArrayGet(hl, offset) - ArrayGet(atr, offset)\n        local lowerPrev = Load('lower', lower) -- load previous\n        local finalLower = Max(lower, lowerPrev) -- take max\n \n        -- if close cuts through lower, we switch to other side\n        if c <= finalLower or (wicks and l <= finalLower) then\n            dir = -1\n            Save('upper', ArrayGet(hl, offset) + ArrayGet(atr, offset)) -- \"reset\" upper line\n        end\n \n        Save('lower', finalLower)\n        result = SignalBuy -- set result\n \n        -- Plot\n        if offset <= 1 then\n            upperId = NewGuid() -- reset upper id\n            Plot(chartIndex, name..' Long Stop', finalLower, {c=Green, id=lowerId})\n        end\n    end\nend\n \n-- Warmup\nif Load('warmup') == nil then\n    LogWarning('Warming up SuperTrend...')\n \n    for i=100, 1, -1 do\n        run(i)\n    end\n \n    LogWarning('Result after warmup: '..result)\n \n    Save('warmup', false)\nelse\n    run() -- only update current step\nend\n \n \n \nSave('dir', dir)\nSave('uid', upperId)\nSave('lid', lowerId)\n \nDefineOutput(EnumType, result, 'SuperTrend output values')",
    "CR": {
      "IV": true,
      "C": {
        "CN": "EasySuperTrend",
        "CD": "EasySuperTrend indicator by pshai.",
        "MC": false,
        "US": false,
        "UL": false,
        "OH": false,
        "P": [
          {
            "Index": 0,
            "Name": "chartIndex",
            "Type": 1,
            "IsRequired": true,
            "IsHidden": false,
            "IsField": false,
            "AllowNull": false,
            "Description": "The index on which to chart",
            "ScriptType": null,
            "Suggestion": [
              4403
            ]
          },
          {
            "Index": 0,
            "Name": "name",
            "Type": 0,
            "IsRequired": false,
            "IsHidden": false,
            "IsField": false,
            "AllowNull": true,
            "Description": "Unique name of the indicator.",
            "ScriptType": null,
            "Suggestion": [
              4406
            ]
          },
          {
            "Index": 0,
            "Name": "interval",
            "Type": 1,
            "IsRequired": false,
            "IsHidden": false,
            "IsField": false,
            "AllowNull": true,
            "Description": "Used interval for price data. Default is 0 and the main interval will be used.",
            "ScriptType": null,
            "Suggestion": [
              4403,
              3404
            ]
          }
        ],
        "O": {
          "Index": 0,
          "Name": "result",
          "Type": 2,
          "IsRequired": false,
          "IsHidden": false,
          "IsField": false,
          "AllowNull": false,
          "Description": "SuperTrend output values",
          "ScriptType": null,
          "Suggestion": []
        },
        "OI": []
      },
      "CR": [],
      "CL": [
        "1765218723 ||| 0 ||| Compiling script...",
        "1765218723 ||| 0 ||| TIP: Using OptimizedForInterval() in combination with the technical analysis commands will improve the backtest speed.",
        "1765218723 ||| 0 ||| Field chartIndex found.",
        "1765218723 ||| 0 ||| DefineParameter(): Input parameter suggestion added: Number",
        "1765218723 ||| 0 ||| Field name found.",
        "1765218723 ||| 0 ||| DefineParameter(): Input parameter suggestion added: Text",
        "1765218723 ||| 0 ||| Field interval found.",
        "1765218723 ||| 0 ||| DefineParameter(): Input parameter suggestion added: Number",
        "1765218723 ||| 0 ||| DefineParameter(): Input parameter suggestion added: InputInterval",
        "1765218723 ||| 0 ||| Registered input 'EasySuperTrend  Settings'",
        "1765218723 ||| 0 ||| Registered input 'ATR Period Length'",
        "1765218723 ||| 0 ||| Registered input 'ATR Multiplier'",
        "1765218723 ||| 0 ||| Registered input 'Use wicks'",
        "1765218723 ||| 2 ||| WARNING: Warming up SuperTrend...",
        "1765218723 ||| 2 ||| WARNING: Result after warmup: SignalShort",
        "1765218723 ||| 0 ||| Output found. Type: Enum. Result: (UserData)",
        "1765218723 ||| 0 ||| Compile test OK."
      ],
      "LCE": [],
      "VCE": [],
      "I": [
        {
          "T": 10,
          "ST": -1,
          "G": "EasySuperTrend  Settings",
          "K": "10-10-0-16.EasySuperTrend  Settings",
          "EK": "10-10-0-16",
          "N": "EasySuperTrend  Settings",
          "TT": "",
          "V": "",
          "D": "",
          "O": null,
          "MIN": 0.0,
          "MAX": 0.0
        },
        {
          "T": 0,
          "ST": -1,
          "G": "EasySuperTrend  Settings",
          "K": "13-13-18-23.ATR Period Length",
          "EK": "13-13-18-23",
          "N": "ATR Period Length",
          "TT": "",
          "V": "22",
          "D": "22",
          "O": null,
          "MIN": 0.0,
          "MAX": 0.0
        },
        {
          "T": 0,
          "ST": -1,
          "G": "EasySuperTrend  Settings",
          "K": "14-14-16-21.ATR Multiplier",
          "EK": "14-14-16-21",
          "N": "ATR Multiplier",
          "TT": "",
          "V": "3",
          "D": "3",
          "O": null,
          "MIN": 0.0,
          "MAX": 0.0
        },
        {
          "T": 2,
          "ST": -1,
          "G": "EasySuperTrend  Settings",
          "K": "15-15-14-19.Use wicks",
          "EK": "15-15-14-19",
          "N": "Use wicks",
          "TT": "",
          "V": "False",
          "D": "False",
          "O": null,
          "MIN": 0.0,
          "MAX": 0.0
        }
      ],
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
    "SID": "e80eba304e8f4dc899c1b57ca8e99026",
    "SN": "[pshaiCmd] EasySuperTrend",
    "SD": "",
    "ST": 0,
    "SS": 0,
    "CN": "EasySuperTrend",
    "IC": true,
    "IV": true,
    "CU": 1765218707,
    "UU": 1765218725,
    "FID": -1
  }
}
