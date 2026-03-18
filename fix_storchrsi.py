import asyncio
import os
import json
from dotenv import load_dotenv

from pyHaasAPI.core.server_manager import ServerManager
from pyHaasAPI.config.settings import Settings
from pyHaasAPI.config.api_config import APIConfig
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.api.script.script_api import ScriptAPI

async def main():
    load_dotenv()
    sm = ServerManager(Settings())
    await sm.connect_server('srv03')
    
    api_config = APIConfig(host='127.0.0.1', port=8090, email=os.getenv('API_EMAIL'), password=os.getenv('API_PASSWORD'))
    client = AsyncHaasClient(api_config)
    await client.connect()
    
    auth = AuthenticationManager(client, api_config)
    await auth.ensure_authenticated()
    
    script_api = ScriptAPI(client, auth)
    
    # Fix CC_StorchRSI
    script_id = "9fb39e76d6c546879b2eb924dd1f2d60"
    print(f"Fixing script {script_id} on srv03...")
    
    source = """--  Stoch RSI Custom Command  HaasScript v3 clean version
DefineCommand(\"CC_StorchRSI\", \"Stochastic RSI custom command\")

-- Inputs
local src      = DefineParameter(ListNumberType, \"source\", \"\", false, ClosePrices(), \"ClosePrices\")
local rsiLen   = DefineParameter(NumberType, \"rsiLen\", \"RSI Length\", false, 14, \"\")
local stochLen = DefineParameter(NumberType, \"stochLen\", \"Stoch Lookback\", false, 14, \"\")
local smoothK  = DefineParameter(NumberType, \"smoothK\", \"Smooth K\", false, 3, \"\")
local smoothD  = DefineParameter(NumberType, \"smoothD\", \"Smooth D\", false, 3, \"\")
local ob       = DefineParameter(NumberType, \"ob\", \"Overbought\", false, 80, \"\")
local os       = DefineParameter(NumberType, \"os\", \"Oversold\", false, 20, \"\")

-- Outputs
local out = { k = {}, d = {}, signal = {} }

-- RSI
local rsi = RSI(src, rsiLen)
if rsi == nil or #rsi < stochLen then
    return out
end

-- Safe getter
local function barVal(series, idx)
    if idx < 1 or idx > #series then
        return series[#series]
    end
    return series[idx]
end

-- Raw Stoch RSI
for i = 1, #rsi do
    local low = barVal(rsi, i)
    local high = barVal(rsi, i)
    for j = i, i + stochLen - 1 do
        local v = barVal(rsi, j)
        if v < low then low = v end
        if v > high then high = v end
    end

    local curr = barVal(rsi, i)
    local raw = 50
    if high ~= low then raw = ((curr - low) / (high - low)) * 100 end
    out.k[i] = raw
end

-- Smooth K & D
for i = 1, #out.k do
    local sumK, countK = 0, 0
    for j = i, i + smoothK - 1 do sumK = sumK + barVal(out.k, j) countK = countK + 1 end
    out.k[i] = sumK / countK

    local sumD, countD = 0, 0
    for j = i, i + smoothD - 1 do sumD = sumD + barVal(out.k, j) countD = countD + 1 end
    out.d[i] = sumD / countD

    local prevK = barVal(out.k, i+1)
    local prevD = barVal(out.d, i+1)
    local s = 0
    if prevK <= prevD and out.k[i] > out.d[i] and out.k[i] < os then s = 1 end
    if prevK >= prevD and out.k[i] < out.d[i] and out.k[i] > ob then s = -1 end
    out.signal[i] = s
end

--  HaasScript v3 correct Plot
Plot(0, \"K\", out.k[1], Blue)
Plot(0, \"D\", out.d[1], Orange)
Plot(0, \"OB\", ob, Red)
Plot(0, \"OS\", os, Green)

-- Final output
return out
"""
    await script_api.edit_script(script_id, script_name="CC_StorchRSI", script_content=source)
    print("Fixed!")
    
    await client.close()
    await sm.shutdown()

if __name__ == '__main__':
    asyncio.run(main())
