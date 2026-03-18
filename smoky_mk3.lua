Log('Tip wallet ERC20: 0xaa28dE4372CA0a8BC36722886E9749f70DF32382')
EnableHighSpeedUpdates(true)
HideOrderSettings()
HideTradeAmountSettings()
 
-- Always start with ALL Trade Settings options UN-TICKED to let the bot preparing values.
-- Test with default values before changing anything to understand the bot.
-- PAY ATTENTION to the log warning if you feel something is off before screeaming the bot is not working.
 
-- inputs
    InputGroupHeader('Super Trend Setting')  
        local short_lookback = Input('01A. Short Period', 8, '')
        local short_atr = Input('02. Short ATR', 3, '')
        local long_lookback = Input('01. Long Period', 21, '')
        local long_atr = Input('02. Long ATR', 8, '')
 
    InputGroupHeader('Trade Settings')
        local okLong = Input('01A. Long Entry', false, 'Allow bot to open Long')
        local okProfitL = Input('01B. Long Exit', false, 'Allow bot to exit Long')
        local okShort = Input('02A. Short Entry', false, 'Allow bot to open Short')
        local okProfitS = Input('02B. Short Exit', false, 'Allow bot to exit Short')
        local okReduce = Input('03. BalRatio Reduction', false, 'Allow Bal Ratio based size reduction')
        local okDerisk = Input('04. Risk Reduction', false, 'Allow Signal based size reduction')
        local oneWay = Input('05. Not Hedge', false, 'Selec this if the market is NOT HEDGE mode')
        local onlyWeekdays = Input('06. Only Weekdays', false, 'Bot will close any position and not trading during weekend')
 
    InputGroupHeader('Bot Settings')
        local wtfStop = Input('01. Stop at no position', false, 'Deactivate bot when there is no open position.')
        local clearSlot = Input('02. Recalculate Slot Size', false, 'If activated will ALWAYS calculating slot size. If not activatated slot size will only calculated when there is no open position.')
        local FOL = Input('03. Force Open Long', false, 'Force open LONG position')
        local FEL = Input('04. Force Exit Long', false, 'Force exit LONG position')
        local FOS = Input('05. Force Open Short', false, 'Force open SHORT position')
        local FES = Input('06. Force Exit Short', false, 'Force exit SHORT position')
        local wtfLoss = Input('07. Pause at % LOSS', 0, 'Pause trading until next day UTC when LOSS % below this. 0 is disalbe.')
        local wtfProfit = Input('08. Pause at % PROFIT', 0, 'Pause trading until next day UTC when PROFIT % above this. 0 is disable.')
                                                                            
    InputGroupHeader('Backtest Settings')
        local wtfBal = Input('01. Deactivate on Over Budget', false, 'ONLY FOR BACKTEST. Disable bot when Bal. Ratio hit trigger')
    
    InputGroupHeader('Custom Wallet')
        local testWallet = Input('01. Activate Custom Wallet', false, 'Use custom wallet amount. A must in Haaslab')
        local testBal = Input('02. Custom Wallet Balance', 0, 'Amount of custom wallet')
    
    InputGroupHeader('Budget')
        local startBal = Input('01. Starting Balance ', 0, 'Starting trading balance which also maximum COST to limit working balance (margin cost + unrealised loss)')
        local stopAtprofit = Input('02. Profit Limit %', 0, 'Deactivate bot when bot gaining this % amount from the starting balance')
        local stopAtloss = Input('03. Loss Limit %', 0, 'Deactivate bot when bot losing this % amount from the highest balance recorded')
        local leverage = Input('04. Leverage', 50, 'MUST be filled and same as in exchange setting. Important for trading budget')
        local contVal = Input('05. Inverse Contract Value', 10, 'ONLY if bot trading on INVERSE Futures then enter the Contract Value. Ignore if not') 
        
    InputGroupHeader('Safety')
        local slTrigger = Input('01.Fix SL %', 0, '0 is disable, else DISREGARDING RISK REDUCTION option and signal bot will derisking when % price change againts average entry.')
        local slDistance = Input('02. Min. Dynamic SL %', 1, 'Signal based min % price distance from 1st entry to calculate stop loss price.')
        local reduceTrigger = Input('03. Bal Ratio Trigger', 0.8, 'Ratio between working balance and trading balance to trigger size reduction')
        local reduceSize = Input('04. Size Reduction %', 100, 'SHOULD BE factors of 100. In risk reduction: 1st reduction 25%, 2nd reduction 50% and so on. In balance ratio reduction: balRatio > Bal. Ratio Trigger then fixed 25% reduction')
        local reduceOrderType = InputOrderType('05. Reduction Order Type', MakerOrCancelOrderType, 'The order type for size reduction')
        local profitOut = Input('06. Profit Hodl %', 100, '% of the bot profit taken out or not compounded into trading balance calculation')
        local dynamicHodl = Input('07. Dynamic Hodl', false, 'After in profit will only take out profit if current profit < 80% of highest profit recorded.')
        local delay = Input('08. SL Delay (Min)', 0, 'Stop the bot from opening new long/short order for X minutes after close at loss.')
 
    InputGroupHeader('Order')
        local orderCount = Input('01. Orders Count', 1, 'How many total filled orders are allowed for DCA.')
        local slotBudget = Input('02. Risk % per order', 1, '1 = risk losing ~1% of trading balance PER ORDER if SL hit from current order price. Total risk PER POSITION = order count * risk.') 
        local orderDistance = Input('02A. Fix Orders Distance %', 0, 'Minimum % price distance from filled order to the next.')
        local dynamicDist = Input('02B. Dynamic Order Distance %', true, 'Auto calculate order distance. If ticked will ignore Order Distance value')
        local slotSizeD = Input('03A. Min. Order Size ', 0, 'Minimum order size if Dynamic Slot Size activated. Static amount if Dynamic Slot Size disabled.')
        local autoSlot = Input('03B. Dynamic Order Size', true, 'Dynamically change order size. Calculated based on distance to SL price.')
        
    InputGroupHeader('Profit')
        local RR = Input('01. Reward to Risk', 3, 'Reward to risk ratio. 2 = reward 2x risk. At this level bot will close position.')
        local halvingAt = Input('02. Halving %', 0, '% of profit price change to start halving size at doubling rate. 0 is disable. If 1 = 1st at 1%, 2nd when 2% and so on.')
        local tpOrderType = InputOrderType('03. TP Order Type', MakerOrCancelOrderType, 'The order type for take-profit')
 
---------------------
-- DATA
    local getMarket = PriceMarket()
    local getAccount = AccountGuid()
    local cp = CurrentPrice(getMarket)
    local ct = Time()
    local cd = CurrentDate()
    local prevDate = Load('prevDate', cd - 1)
    local today = CurrentDay()
    local mainInterval = CurrentInterval()
 
    -- counters 
        local highestP = Load('highestP', 0)
        local lowestP = Load('lowestP', 0)
        local SRCounter = Load('SRCounter', 0)
 
    -- Indicators
        local o, h, l, c, p = OptimizedForInterval(mainInterval, function()
            local o = OpenPrices()
            local h = HighPrices()
            local l = LowPrices()
            local c = ClosePrices()
            local p = HLCPrices()
            
            return o, h, l, c, p
            end)
        
        local o2 = ArrayGet(o, 2)
        local h2 = ArrayGet(h, 2)
        local l2 = ArrayGet(l, 2)
        local c2 = ArrayGet(c, 2)
 
        local H3 = c + ((h - l) * 0.275)
        local L3 = c - ((h - l) * 0.275)
 
        local ma = SMA(p, 21)
        Plot(0, 'Pivot SMA', ma, Yellow)
        local longMA = c < ma
        local shortMA = c > ma
        local fastST = CC_SuperTrendExt(h, l, c, c, short_lookback, short_atr)
        local slowST = CC_SuperTrendExt(h, l, c, c, long_lookback, long_atr)
        Plot(0, 'Slow SuperTrend', slowST, DarkGray)
        Plot(0, 'Fast SuperTrend', fastST, White)
 
 
---------------------
-- POSITIONS
            local hedge_longPosId = Load(getMarket..'hedge_longPosId', NewGuid())
            local hedge_shortPosId = Load(getMarket..'hedge_shortPosId', NewGuid())
 
            local dir_l = GetPositionDirection(hedge_longPosId)
            local aep_l = GetPositionEnterPrice(hedge_longPosId)
            local pamt_l = GetPositionAmount(hedge_longPosId)
            local delta_l = pamt_l > 0 and (cp.close - aep_l) / aep_l * 100 or 0
            local proi_l = delta_l * leverage 
 
            local dir_s = GetPositionDirection(hedge_shortPosId)
            local aep_s = GetPositionEnterPrice(hedge_shortPosId)
            local pamt_s = GetPositionAmount(hedge_shortPosId)
            local delta_s = pamt_s > 0 and (aep_s - cp.close) / aep_s * 100 or 0
            local proi_s = delta_s * leverage
 
        -- DELTA
            local topDeltaL = Load('topDeltaL', 0)
            local btmDeltaL = Load('btmDeltaL', 0)
            if pamt_l > 0 and delta_l > topDeltaL then 
                Save('topDeltaL', delta_l) 
            elseif pamt_l > 0 and delta_l < btmDeltaL then 
                Save('btmDeltaL', delta_l) 
            elseif pamt_l == 0 then 
                Save('topDeltaL', 0)
                Save('btmDeltaL', 0)
            end
            --Log('deltaL '..delta_l..' topDeltaL '..topDeltaL..' btmDeltaL '..btmDeltaL)
 
            local topDeltaS = Load('topDeltaS', 0)
            local btmDeltaS = Load('btmDeltaS', 0)
            if pamt_s > 0 and delta_s > topDeltaS then 
                Save('topDeltaS', delta_s)
            elseif pamt_s > 0 and delta_s < btmDeltaS then 
                Save('btmDeltaS', delta_s)  
            elseif pamt_s == 0 then 
                Save('topDeltaS', 0)
                Save('btmDeltaS', 0)
            end
            --Log('deltaS '..delta_s..' topDeltaS '..topDeltaS..' btmDeltaS '..btmDeltaS)
 
        -- manage position ids
            if pamt_l == 0 and IsPositionClosed(hedge_longPosId) then
                if IsAnyOrderOpen(hedge_longPosId) then
                    CancelAllOrders(hedge_longPosId)
                else
                    hedge_longPosId = NewGuid()
                    dir_l = GetPositionDirection(hedge_longPosId)
                    aep_l = GetPositionEnterPrice(hedge_longPosId)
                    pamt_l = GetPositionAmount(hedge_longPosId)
                    proi_l = delta_l * leverage 
                end
            end
            
            if pamt_s == 0 and IsPositionClosed(hedge_shortPosId) then
                if IsAnyOrderOpen(hedge_shortPosId) then
                    CancelAllOrders(hedge_shortPosId)
                else
                    hedge_shortPosId = NewGuid()
                    dir_s = GetPositionDirection(hedge_shortPosId)
                    aep_s = GetPositionEnterPrice(hedge_shortPosId)
                    pamt_s = GetPositionAmount(hedge_shortPosId)
                    proi_s = delta_s * leverage
                end
            end
        
        -- get pos id
            local getPositionId = function(isLong)
                return isLong and hedge_longPosId or hedge_shortPosId
            end
 
---------------------
-- WALLET CHECK
    local profitLabel = ProfitLabel(getMarket)
    if profitLabel == nil then profitLabel = QuoteCurrency(getMarket) end
 
    -- inverse or not
        if profitLabel == 'USD' or profitLabel == 'USDT' or profitLabel == 'BUSD' or profitLabel == 'USDC' then
            isInverse = false 
        else
            isInverse = true 
        end
 
    -- check balance usage
        if pamt_l > 0 then
            usedLong = isInverse and ((pamt_l * contVal) / leverage) / cp.close or (pamt_l * aep_l) / leverage
            getProfitL = isInverse and (cp.close - aep_l) * (leverage * usedLong) / cp.close or (cp.close - aep_l) * pamt_l
        else 
            getProfitL = 0
            usedLong = 0
        end
 
        if pamt_s > 0 then
            usedShort = isInverse and ((pamt_s * contVal) / leverage) / cp.close or (pamt_s * aep_s) / leverage
            getProfitS = isInverse and (aep_s - cp.close) * (leverage * usedShort) / cp.close or (aep_s - cp.close) * pamt_s
        else 
            getProfitS = 0
            usedShort = 0
        end
 
        local getProfit = getProfitL + getProfitS
        local botProfit = GetBotProfit()
        local netbotProfit = botProfit + getProfit
 
    -- trading balance
        local xchangeBal = WalletAmount(getAccount, profitLabel)
        local walletBal = testWallet and testBal + botProfit
                            or xchangeBal
        local workBal = usedLong + usedShort - getProfit
        local botBalance = startBal + botProfit
        local netBalance = startBal + netbotProfit - usedLong - usedShort
 
        if dynamicHodl and botProfit >= highestP * 0.8 then 
            profitOut = 0 
        end 
 
        local maxCost = botProfit > 0 
                        and botBalance - (botProfit * profitOut / 100)
                        or botBalance  
        
    
    -- balance warning
        local balRatio = startBal > 0 and workBal / maxCost or 0
        local okBalance = walletBal >= maxCost
 
        if balRatio > 0.5 and balRatio < 0.8 then 
            Log('Working balance is > 50% of Budget!!!', Yellow) 
        end
 
        if balRatio > 0.8 then 
            LogWarning('Working balance is > 80% of Budget!!!') 
        end
 
        local BRCounter = Load('BRCounter', 0)
        if balRatio > BRCounter then Save('BRCounter', balRatio) end
    
 
---------------------        
-- WTF
    if stopAtloss > 0 then  
        if startBal + highestP > AddPerc(startBal, stopAtloss) then 
            if pamt_l == 0 and pamt_s == 0 and botBalance < SubPerc(startBal + highestP, stopAtloss) then 
                DeactivateBot('Bot loss limit reached.', true)
            elseif netBalance < SubPerc(startBal + highestP, stopAtloss) then 
                if pamt_l != 0 then 
                    FEL = true 
                end 
 
                if pamt_s != 0 then 
                    FES = true 
                end 
            end
            Log('Bot will stop when Bot Balance < '..SubPerc(startBal + highestP, stopAtloss)..' '..profitLabel, Yellow)
            Plot(2, 'Stop @ Loss', SubPerc(startBal + highestP, stopAtloss), {c=Aqua, s=Step}) 
        else 
            Log('Stop at loss will start when Bot Balance > '..AddPerc(startBal, stopAtloss)..' '..profitLabel, Yellow)
        end   
    end 
 
    if stopAtprofit > 0 then  
        if pamt_l == 0 and pamt_s == 0 and botBalance > AddPerc(startBal, stopAtprofit) then 
            DeactivateBot('Bot profit target reached.', true)
        elseif netBalance > AddPerc(startBal, stopAtprofit) then 
                if pamt_l != 0 then 
                    FEL = true 
                end 
 
                if pamt_s != 0 then 
                    FES = true 
                end 
            Log('Bot will deactivate when Bot Balance > '..AddPerc(startBal, stopAtprofit)..' '..profitLabel, Yellow)
        end   
    end 
 
    if onlyWeekdays then
        if today == 1 or today == 7 then 
            FEL = true 
            FES = true
            Log('Not trading on weekend')
        end
        Log('Bot will not trading on weekend', Yellow)
    end
 
    if wtfBal then
        if balRatio > reduceTrigger then
            DeactivateBot('Deactivated because over budget', true)
        end
        Log('STOP at over budget safety activated. Is this a backtest ?', Yellow)
    end
 
    if wtfLoss != 0 or wtfProfit != 0 then
        local pBalance = Load('pBalance', botBalance)
 
        if wtfLoss != 0 then
            local baseLoss = SubPerc(startBal, wtfLoss)
            local targetAmount = maxCost * wtfLoss / 100
            local lossLimit = botBalance - targetAmount
            local newLL = Load('newLL', baseLoss)
            Log('Bot will rest at Bot Balance below '..newLL..' '..profitLabel, DarkGreen)        
            
            if botBalance < newLL then
                if prevDate != cd then 
                    Save('prevDate', cd)
                end
                Save('pBalance', botBalance)
                Save('newLL', lossLimit) 
            end
 
            if botBalance > pBalance then 
                Save('newLL', lossLimit)
            end
            Plot(2, 'Loss Limit', newLL, {c=Purple, s=Step}) 
        end
 
        if wtfProfit != 0 then 
            local baseProfit = AddPerc(startBal, wtfProfit)
            local targetAmount = maxCost * wtfProfit / 100
            local profitLimit = botBalance + targetAmount
            local newPL = Load('newPL', baseProfit)
            Log('Bot will rest at Bot Balance above '..newPL..' '..profitLabel, DarkGreen)
            
            if botBalance > newPL then
                if prevDate != cd then 
                    Save('prevDate', cd)
                end
                Save('pBalance', botBalance) 
                Save('newPL', profitLimit)
            end
 
            if botBalance < pBalance then 
                Save('newPL', profitLimit)
            end
            Plot(2, 'Profit Limit', newPL, {c=Purple, s=Step}) 
        end
 
        if prevDate == cd 
            and botBalance == pBalance
            and botProfit != 0
            and pamt_l == 0
            and pamt_s == 0 then 
                okLong = false
                okShort = false
            Log('Target reached, Bot is resting.', DarkGreen) 
            ChartSetOptions(-2, 'Resting Signal')
            PlotSignalBar(-2, White)
        end 
 
        Log('pBalance '..pBalance..' botBalance '..botBalance)
        Plot(2, 'pBalance', pBalance) 
    end
 
    if wtfStop then
        local longNull = pamt_l == 0
        local shortNull = pamt_s == 0
        if longNull and shortNull then
            DeactivateBot('Deactivated by No Position', true)
        else
            LogWarning('Will deactivate on No Position, waiting...maybe next second, maybe never :)')
        end
        Log('Deactivate on No Position is active.', Yellow)
    end
 
 
---------------------
-- DYNAMICS
    local LLP = LastLongPrice()
    local longTrim = Load('LT', 0) 
    local longFilled = Load('LFM', 0)
 
    local LSP = LastShortPrice()
    local shortTrim = Load('ST', 0)
    local shortFilled = Load('SFM', 0)
    --Plot(8, 'LT ', longTrim, Green)
    --Plot(8, 'ST ', shortTrim, Red)
 
    -- ENTRY TP SL
        -- ENTRY  
            local longPrice = cp.bid
            local shortPrice = cp.ask
 
        -- SL
            if longFilled == 0 then  
                if slTrigger != 0 then 
                    longSLP = SubPerc(longPrice, slTrigger)
                else 
                    longSLP = Min(SubPerc(fastST, slDistance), slowST) 
                end
            elseif longFilled == 1 and longTrim == 0 then
                Save('longSLP', longSLP)  
            elseif longTrim >= 1 then
                longSLP = AddPerc(Load('longSLP'), halvingAt * (longTrim + 1))
            else 
                longSLP = Load('longSLP')
            end
        
            if shortFilled == 0 then 
                if slTrigger != 0 then 
                    shortSLP = AddPerc(shortPrice, slTrigger)
                else 
                    shortSLP = Max(AddPerc(fastST, slDistance), slowST)
                end
            elseif shortFilled == 1 and shortTrim == 0 then
                Save('shortSLP', shortSLP)
            elseif shortTrim >= 1 then 
                shortSLP = SubPerc(Load('shortSLP'), halvingAt * (shortTrim + 1))
            else
                shortSLP = Load('shortSLP')
            end
 
            local longSL_range = longPrice - longSLP
            local shortSL_range = shortSLP - shortPrice
 
        -- TP
            local longTPrange = aep_l - longSLP
            if pamt_l != 0 and longTrim == 0 then 
                exitPriceL = aep_l + (longTPrange * RR)
                Save('EPL', exitPriceL)
            else 
                exitPriceL = Load('EPL', H3)
            end
 
            local shortTPrange = shortSLP - aep_s
            if pamt_s != 0 and shortTrim == 0 then 
                exitPriceS = aep_s - (shortTPrange * RR)
                Save('EPS', exitPriceS)
            else 
                exitPriceS = Load('EPS', L3)
            end
 
    -- the force
        if FEL then 
            okLong = false
            okProfitL = false
            exitPriceL = cp.ask
            LET = 'Forced'
            Log('FORCE EXIT LONG POSITION ACTIVATED', Red) 
        end 
        
        if FES then
            okShort = false
            okProfitS = false
            exitPriceS = cp.bid
            SET = 'Forced'
            Log('FORCE EXIT SHORT POSITION ACTIVATED', Red) 
        end
 
        --Log('Last Price Long: '..LLP..' | Short: '..LSP)
        --Log('Exit Price -> Long: '..exitPriceL..' | Short: '..exitPriceS)
        --Log('Enter Price -> Long: '..longPrice..' | Short: '..shortPrice)         
 
    -- SLOT SIZE
        if autoSlot then   
            local risk = slotBudget / 100 * maxCost
            --Log('risk '..risk..' longSL_range '..longSL_range..' shortSL_range '..shortSL_range)  
 
            local sizeL = isInverse and (risk * longSLP / longSL_range ) * (longPrice / contVal) or risk / longSL_range
            slotSizeL = sizeL > slotSizeD and sizeL or slotSizeD
            
            local sizeS = isInverse and (risk * shortSLP / shortSL_range) * (shortPrice / contVal) or risk / shortSL_range
            slotSizeS = sizeS > slotSizeD and sizeS or slotSizeD
            --Log('slotSizeL '..slotSizeL..' slotSizeS '..slotSizeS)
        else
            slotSizeL = slotSizeD 
            slotSizeS = slotSizeD 
        end
 
        local halvingAtL = halvingAt
        local halvingAtS = halvingAt
        if fastST > slowST and c > fastST then 
            halvingAtS = halvingAt / 2
            Log('Strong uptrend', Green)
        elseif fastST > slowST and c < fastST then
            halvingAtS = halvingAt / 2
            Log('Weak uptrend', Green(50))        
        elseif fastST < slowST and c < fastST then 
            halvingAtL = halvingAt / 2
            Log('Strong downtrend', Red)
        elseif fastST < slowST and c > fastST then 
            halvingAtL = halvingAt / 2
            Log('Downtrend', Red(50))
        end
    
    -- ORDER COST 
        local longCost = isInverse and ((slotSizeL * contVal) / leverage) / longPrice or (slotSizeL * longPrice) / leverage
        local shortCost = isInverse and ((slotSizeS * contVal) / leverage) / shortPrice or (slotSizeS * shortPrice) / leverage
        --Log('Cost Long: '..longCost..' Short: '..shortCost)
 
 
---------------------
-- EXECUTION
    local ODL = PercentageChange(longSLP, aep_l) / orderCount 
    local ODS = PercentageChange(aep_s, shortSLP) / orderCount
    if orderCount > 1 and longFilled == 1 and longTrim == 0 then 
        Save('ODL', ODL)
    end 
    if orderCount > 1 and shortFilled == 1 and shortTrim == 0 then 
        Save('ODS', ODS)
    end
    local orderDistanceL = Load('ODL', ODL)
    local orderDistanceS = Load('ODS', ODS)
    --Log('ODL '..orderDistanceL..' ODS '..orderDistanceS)
    
    --LONG
        --OPEN
            local longOpen1 = pamt_l == 0
                                and l > fastST
                                and l2 > fastST
                                and longPrice > AddPerc(longSLP, slDistance)
                                and c < o 
                                and c2 < o2
                                and fastST > slowST
                                and longMA
            local longOpen2 = orderCount > 1
                                and pamt_l != 0
                                and L3 < SubPerc(LLP, IfElse(dynamicDist, orderDistanceL, orderDistance)) 
                                and L3 > AddPerc(longSLP, IfElse(dynamicDist, orderDistanceL, orderDistance))
 
            if longOpen1 then 
                LT = '1stOrder'
            elseif longOpen2 then
                longPrice = L3
                LT = 'DCA'
            elseif FOL then 
                longPrice = L3
                LT = 'ForceLong' 
            end
 
            local longOpen = okLong
                                and okBalance
                                and longFilled < orderCount
                                and cp.close > longPrice
                                and longCost < maxCost / 2 
                                and IfElse(oneWay, pamt_s == 0, true)
                                and (longOpen1 or longOpen2)
 
        --DERISK
            local okLongDerisk1 = pamt_l > 0
                                    and (cp.ask < longSLP or fastST < slowST)
            local okLongDerisk2 = pamt_l > 0
                                    and halvingAt > 0
                                    and delta_l > 0
                                    and IfElse(okProfitL, cp.close < SubPerc(exitPriceL, halvingAtL), true) 
                                    and not okLongDerisk1
 
            local longFSL = slTrigger > 0
                            and pamt_l > 0
                            and H3 < SubPerc(aep_l, slTrigger)
 
            if okLongDerisk1 then 
                LDP = cp.ask
                LDT = 'Derisking'
            elseif okLongDerisk2 then
                LDPc = AddPerc(aep_l, halvingAtL * (longTrim + 1)) 
                LDP = IfElse(cp.close < LDPc, LDPc, cp.ask)
                LDT = 'LongHalving'
                PlotSignalBar(3, Green)
            else 
                LDP = longSLP
            end
 
            local okLongDerisk = okDerisk
                                    and pamt_l > 0
                                    and (okLongDerisk1 or okLongDerisk2)
 
        --EXIT                        
            local longExit1 = pamt_l > 0
                                and halvingAt == 0
                                and delta_l > 0
                                and c > fastST
            local longExit2 = pamt_l > 0
                                and halvingAt != 0
                                and H3 > exitPriceL
                                and cp.close > SubPerc(exitPriceL, halvingAtL)
            local longExit3 = pamt_l > 0 
                                and halvingAt != 0
                                and delta_l > halvingAtL
                                and c < fastST
                                and c < ma
 
            if longExit1 then 
                LET = 'LE1'
            elseif longExit2 then 
                exitPriceL = H3
                LET = 'LE2'
            elseif longExit3 then 
                exitPriceL = cp.ask
                LET = 'LE3'
            end
 
            local longExit = okProfitL
                                and not okLongDerisk
                                and not FEL
                                and (longExit1 or longExit2 or longExit3)
 
    --SHORT 
        --OPEN       
            local shortOpen1 = pamt_s == 0 
                                and h < fastST 
                                and h2 < fastST
                                and shortPrice < SubPerc(shortSLP, slDistance)
                                and c > o 
                                and c2 > o2
                                and fastST < slowST
                                and shortMA
            local shortOpen2 = orderCount > 1
                                and pamt_s != 0
                                and H3 > AddPerc(LSP, IfElse(dynamicDist, orderDistanceS, orderDistance))
                                and H3 < SubPerc(shortSLP, IfElse(dynamicDist, orderDistanceS, orderDistance))
 
            if shortOpen1 then 
                ST = '1stOrder'
            elseif shortOpen2 then 
                shortPrice = H3
                ST = 'DCA'
            elseif FOS then 
                shortPrice = H3
                LT = 'ForceShort'
            end
 
            local shortOpen = okShort
                                and okBalance
                                and shortFilled < orderCount
                                and cp.close < shortPrice
                                and shortCost < maxCost / 2 
                                and IfElse(oneWay, pamt_l == 0, true)
                                and (shortOpen1 or shortOpen2)
        
        --DERISK
            local okShortDerisk1 = pamt_s > 0
                                    and (cp.bid > shortSLP or fastST > slowST)
            local okShortDerisk2 = pamt_s > 0
                                    and halvingAt > 0
                                    and delta_s > 0
                                    and IfElse(okProfitS, cp.close > AddPerc(exitPriceS, halvingAtS), true) 
                                    and not okShortDerisk1
            
            local shortFSL = slTrigger > 0
                                and pamt_s > 0 
                                and L3 > AddPerc(aep_s, slTrigger)
 
            if okShortDerisk1 then 
                SDP = cp.bid
                SDT = 'Derisking'
            elseif okShortDerisk2 then 
                SDPc = SubPerc(aep_s, halvingAtS * (shortTrim + 1)) 
                SDP = IfElse(cp.close > SDPc, SDPc, cp.bid)
                SDT = 'ShortHalving'
                PlotSignalBar(3, Red)
            else 
                SDP = SubPerc(aep_s, halvingAtS * (shortTrim + 1))
            end
 
            local okShortDerisk = okDerisk
                                    and (okShortDerisk1 or okShortDerisk2)
 
        --EXIT                        
            local shortExit1 = pamt_s > 0
                                and halvingAt == 0
                                and delta_s > 0
                                and c < fastST
            local shortExit2 = pamt_s > 0
                                and halvingAt != 0
                                and L3 < exitPriceS
                                and cp.close < AddPerc(exitPriceS, halvingAtS)
            local shortExit3 = pamt_s > 0 
                                and halvingAt != 0
                                and delta_s > halvingAtS
                                and c > fastST
                                and c > ma
 
            if shortExit1 then 
                SET = 'SE1'
            elseif shortExit2 then
                exitPriceS = L3
                SET = 'SE2'
            elseif shortExit3 then
                exitPriceS = cp.bid
                SET = 'SE3'
            end
 
            local shortExit = okProfitS
                                and not okShortDerisk
                                and not FES
                                and (shortExit1 or shortExit2 or shortExit3 )
 
 
---------------------
-- CORE LOGIC HEDGE MODE
    -- ENTRY
            local timerL = Load('timerL', ct)
            local timerS = Load('timerS', ct)
            --Log('ct '..ct..' timerL '..timerL..' timerS '..timerS)
            local slot = function(isLong, amount, timer, trigger, canPlace)
                local prefix = isLong and 'L' or 'S'
                local name = prefix
                local cmd = isLong and PlaceGoLongOrder or PlaceGoShortOrder
                local price = isLong and longPrice or shortPrice
                local posId = getPositionId(isLong)
                local aep = isLong and aep_l or aep_s
                local pamt = isLong and pamt_l or pamt_s
                local TOPB = TradeOncePerBar(mainInterval, posId)
                local filled = isLong and longFilled + 1 or shortFilled + 1
 
                local oid = Load(name..'oid', '') -- order id
                if oid != '' then
                    local order = OrderContainer(oid)
 
                    if order.isOpen then
                        if not canPlace then
                            CancelOrder(oid)
                            LogWarning('Not allowed right now '..name)
                        end
                    elseif order.isFilled then 
                        if isLong then 
                            Save('LFM', longFilled + 1)
                        else 
                            Save('SFM', shortFilled + 1)
                        end
                        oid = '' 
                    else 
                        oid = ''
                    end
                else
                    if canPlace and TOPB and ct >= timer then
                        SetFee(MakersFee(getMarket))
                        oid = cmd(price, amount, {market = getMarket, type = MakerOrCancelOrderType, note = name..filled..'-'..trigger, positionId = posId})
                    end
                end
 
                Save(name..'oid', oid)
            end
 
            -- variables
                slot(true, slotSizeL, timerL, LT, longOpen or FOL) -- long slot
                slot(false, slotSizeS, timerS, ST, shortOpen or FOS) -- short slot
 
    -- EXIT
            local updateTakeProfit = function(isLong, exitPrice, ET, canExit)
                local price = isLong and IfElse(cp.close < exitPrice, exitPrice, cp.ask) 
                                or IfElse(cp.close > exitPrice, exitPrice, cp.bid) 
                local placeDelta = isLong and (price - aep_l) / aep_l * 100
                                    or (aep_s - price) / aep_s * 100
                local prefix = isLong and 'L' or 'S'
                local name = prefix .. ' TP '..placeDelta..'%'
                local oid = Load(prefix .. 'tp_oid', '')
                local posId = getPositionId(isLong)
 
                if oid != '' then
                    local order = OrderContainer(oid)
 
                    if order.isOpen then
                        if not canExit then
                            CancelOrder(oid)
                            LogWarning('Exit cancelled '..name)
                        end
                    else
                        oid = ''
                    end
                else
                    if canExit then
                        SetFee(tpOrderType == MarketOrderType and TakersFee() or MakersFee())
                        oid = PlaceExitPositionOrder({timeout = mainInterval * 60, price = price, type = tpOrderType, note = name..'-'..ET, positionId = posId})
                    end
                end
 
                Save(prefix .. 'tp_oid', oid)
            end
 
            -- variables
                updateTakeProfit(true, exitPriceL, LET, longExit or FEL)
                updateTakeProfit(false, exitPriceS, SET, shortExit or FES)
 
    -- Balance Ratio REDUCTION
            local updatePositionManagement = function(isLong, currentSize, canReduce)
                local price = isLong and cp.ask or cp.bid
                local placeDelta = isLong and (price - aep_l) / aep_l * 100
                                    or (aep_s - price) / aep_s * 100
                local prefix = isLong and 'Long' or 'Short'
                local name = prefix .. ' Size Reduction '..placeDelta..'%'
                local oid = Load(prefix .. 'pos_oid', '')
                local posId = getPositionId(isLong)
                local amount = SubPerc(currentSize, 100 - reduceSize) -- take X% of position
                local cmd = isLong
                        and PlaceExitLongOrder
                        or PlaceExitShortOrder
                local timer = Load(prefix .. 'pos_timer', Time())
 
                if oid != '' then
                    local order = OrderContainer(oid)
 
                    if order.isOpen then                        
                        if not canReduce then
                            CancelOrder(oid)
                            LogWarning('Reduction cancelled '..name)
                        end
                    else
                        sizeRed = 1
                        Save('SRCounter', SRCounter + sizeRed)
                        oid = ''
                    end
                else
                    if canReduce and Time() >= timer then
                        CancelAllOrders()
                        SetFee(reduceOrderType == MarketOrderType and TakersFee() or MakersFee())
                        oid = cmd(price, amount, {market = getMarket, type = reduceOrderType, note = name, timeout = 6000, positionId = posId})
                        timer = Time() + 60 -- 1min   
                    end
                end
 
                Save(prefix .. 'pos_oid', oid)
                Save(prefix .. 'pos_timer', timer)
            end
 
            -- variables
                updatePositionManagement(true, pamt_l, okReduce and pamt_l > 0 and balRatio > reduceTrigger and delta_l < delta_s)
                updatePositionManagement(false, pamt_s, okReduce and pamt_s > 0 and balRatio > reduceTrigger and delta_s < delta_l)
 
    -- Derisking REDUCTION
            local derisking = function(isLong, currentSize, price, DT, canDerisk)
                local amount = SubPerc(currentSize, 100 - reduceSize) -- take X% of position
                local openDT = Load('openDT', DT)
                local trimDone = isLong and longTrim or shortTrim
                if DT == 'ShortHalving' or DT == 'LongHalving' then
                    reduceOrderType = MakerOrCancelOrderType
                    amount = currentSize / 2 
                end
                local placeDelta = isLong and (price - aep_l) / aep_l * 100
                                    or (aep_s - price) / aep_s * 100
                local prefix = isLong and 'Long ' or 'Short '
                local name = prefix..' Derisking '..placeDelta..'%'
                local oid = Load(prefix .. 'derisk_oid', '')
                local posId = getPositionId(isLong)
                local cmd = isLong
                            and PlaceExitLongOrder
                            or PlaceExitShortOrder
 
                -- amount check 
                    if amount < MinimumTradeAmount(getMarket, price) then 
                        amount = currentSize
                    end
 
                if oid != '' then
                    local order = OrderContainer(oid)
                     
                    if order.isOpen then
                        if not canDerisk then
                            CancelOrder(oid)
                            LogWarning('Reduction cancelled '..name)
                        end
                        if openDT != DT then 
                            CancelOrder(oid)
                        end
                    elseif order.isFilled then
                        if isLong then
                            if LDT == 'LongHalving' then
                                Save('LT', longTrim + 1)
                            end
                            Save('timerL', ct + (delay * 60))
                        else 
                            if SDT == 'ShortHalving' then 
                                Save('ST', shortTrim + 1)
                            end
                            Save('timerS', ct + (delay * 60))
                        end
                        oid = ''
                    else
                        oid = '' 
                    end
                else
                    if canDerisk then
                        CancelAllOrders()
                        SetFee(reduceOrderType == MarketOrderType and TakersFee() or MakersFee())
                        oid = cmd(price, amount, {market = getMarket, type = reduceOrderType, note = name..'-'..DT, timeout = mainInterval * 60, positionId = posId})
                        Save('openDT', DT)
                    end
                end
                Save(prefix .. 'derisk_oid', oid) 
            end
        -- variables
            derisking(true, pamt_l, LDP, LDT, okLongDerisk or longFSL)
            derisking(false, pamt_s, SDP, SDT, okShortDerisk or shortFSL)
 
    -- Positions Data
        if pamt_l > 0 then
            if halvingAt > 0 then 
                Log('Next LONG halving is at '..LDP)
            end
            Log('LONG Delta: '..Round(delta_l, 2)..
                '% | Highest: '..Round(topDeltaL, 2)..
                '% | Lowest: '..Round(btmDeltaL, 2)..
                '% | Amount: '..getProfitL)
        end
        if pamt_s > 0 then 
            if halvingAt > 0 then 
                Log('Next SHORT halving is at '..SDP)
            end
            Log('SHORT Delta: '..Round(delta_s, 2)..
                '% | Highest: '..Round(topDeltaS, 2)..
                '% | Lowest: '..Round(btmDeltaS, 2)..
                '% | Amount: '..getProfitS)
        end
 
 
---------------------
-- DATA SAVING
    Save(getMarket..'hedge_longPosId', hedge_longPosId)
    Save(getMarket..'hedge_shortPosId', hedge_shortPosId)
 
    if botProfit > highestP then 
        Save('highestP', botProfit)
    elseif botProfit < lowestP then 
        Save('lowestP', botProfit) 
    end
 
    if pamt_l == 0 then 
        Save('LT', 0) 
        Save('LFM', 0) 
    end
    if pamt_s == 0 then  
        Save('ST', 0)
        Save('SFM', 0)
    end 
 
 
--------------------- 
-- PLOT
    -- AEP Plot
        if aep_l > 0 then
            local posId = getPositionId(true)
            Plot(0, 'AvgEP Long', aep_l, {c=Teal, id=posId, w=2})
            Plot(0, 'SL Long', longSLP, {c=Teal, id=posId, w=1})
            --Plot(0, 'TP Long', exitPriceL, {c=Teal, id=posId, w=1})
        end
    
        if aep_s > 0 then
            local posId = getPositionId(false)
            Plot(0, 'AvgEP Short', aep_s, {c=Purple, id=posId, w=2})
            Plot(0, 'SL Short', shortSLP, {c=Purple, id=posId, w=1})
            --Plot(0, 'TP Short', exitPriceS, {c=Purple, id=posId, w=1})
        end
 
    ChartSetOptions(1, 'Exposure')
    local lineLong = IfElse(pamt_l > 0, pamt_l, 0)
    local lineShort = IfElse(pamt_s > 0, -pamt_s, 0)
    Plot(1, 'Longs', lineLong, {c=Green, s=Step})
    Plot(1, 'Shorts', lineShort, {c=Red, s=Step})
    
    ChartSetOptions(2, 'Balance Monitor')
    Plot(2, 'Net Balance', netBalance, {c=Orange, s=Step})
    Plot(2, 'Trading Balance', maxCost, {c=White, s=Step})
    Plot(2, 'WorkBal', workBal, {c=Red, s=Step})
    Plot(2, 'Bot Profit', botProfit, {c=DarkGreen, s=Step})
    Plot(2, 'Bot Balance', botBalance, {c=Yellow, s=Step}) 
 
    Log('Size Reduction: '..SRCounter..' times')
 
 
---------------------
-- FINAL REPORT
    Finalize(function()
        CustomReport('Current Balance Ratio', Round(100 * balRatio, 2)..'%')
        CustomReport('Highest Balance Ratio', Round(100 * BRCounter, 2)..'%')
        CustomReport('Size Reduction', SRCounter..' times')
        CustomReport('Final Wallet Balance', Round(walletBal, 5)..' '..profitLabel)
        CustomReport('Final Net Balance', Round(netBalance, 5)..' '..profitLabel)
        CustomReport('Highest Profit', Round(highestP, 5)..' '..profitLabel)
        CustomReport('Lowest Profit', Round(lowestP, 5)..' '..profitLabel)
        if testWallet then
            local realprofitPercent = Round(botProfit / startBal * 100, 2) 
            local runprofitPercent = Round(netbotProfit / startBal * 100, 2) 
            CustomReport('Running Profit %: ', runprofitPercent..'%')
            CustomReport('Realized Profit %: ', realprofitPercent..'%')
            CustomReport('Profit to Highest Bal Ratio', Round(realprofitPercent / (100 * BRCounter), 2))
        end    
    end)
 
 
---------------------
-- INFO 
    Log('Profit Monitor -> Current: '..Round(botProfit, 5)..' '..profitLabel..' | Highest: '..Round(highestP, 5)..' '..profitLabel..' | Lowest: '..Round(lowestP, 5)..' '..profitLabel)
    Log('Balance Monitor -> Wallet: '..Round(walletBal, 5)..' '..profitLabel..
        ' | Bot: '..Round(botBalance, 5)..' '..profitLabel..
        ' | Trading: '..Round(maxCost, 5)..' '..profitLabel..
        ' | Net: '..Round(netBalance, 5)..' '..profitLabel..
        ' | Working: '..Round(workBal, 5)..' '..profitLabel..
        ' | Ratio: '..Round(balRatio, 3))
 
 
---------------------
-- BALANCE WARNING
    if not okBalance then
        LogWarning('TRADING BALANCE < EXCHANGE BALANCE')
    end
    if startBal == 0 then 
        LogWarning('Please enter trading balance')
    end
 
Log('Market '..getMarket)
Log('SMOKYBOT MK3')
Log(' ')
