"""
Enumerations for pyHaasAPI v2

This module contains all enumeration types from the HaasOnline API reference.
Generated from HaasOnline Trade Server v4.0.7.102
Production date: 11/4/2025
"""

from enum import Enum


class EnumAccountPositionMode(Enum):
    """EnumAccountPositionMode enumeration"""
    OneWay = 0
    Hedge = 1
    Unknown = -1


class EnumAccountStatus(Enum):
    """EnumAccountStatus enumeration"""
    Created = 0
    Connected = 1
    KeysError = 2
    Deactivate = 3


class EnumAuthenticationMethod(Enum):
    """EnumAuthenticationMethod enumeration"""
    APIKeys = 0
    OAuth = 1


class EnumCloudMarketContractType(Enum):
    """EnumCloudMarketContractType enumeration"""
    Vanilla = 0
    Inverse = 1
    Quanto = 2


class EnumDecimalType(Enum):
    """EnumDecimalType enumeration"""
    Fixed = 0
    SignificantNumber = 1


class EnumExchangeType(Enum):
    """EnumExchangeType enumeration"""
    Spot = 0
    Margin = 1
    Leverage = 2


class EnumHaasChartAnnotationsType(Enum):
    """EnumHaasChartAnnotationsType enumeration"""
    HorizontalLine = 0
    HorizontalZone = 1
    VerticalLine = 2
    VerticalZone = 3


class EnumHaasChartAxisSide(Enum):
    """EnumHaasChartAxisSide enumeration"""
    Left = 1000
    Right = 1001


class EnumHaasChartAxisType(Enum):
    """EnumHaasChartAxisType enumeration"""
    Linear = 1100
    Percentage = 1101


class EnumHaasChartLineDecoration(Enum):
    """EnumHaasChartLineDecoration enumeration"""
    Solid = 800
    Dashed = 801
    Dotted = 802


class EnumHaasChartLineStyle(Enum):
    """EnumHaasChartLineStyle enumeration"""
    Smooth = 700
    Spiked = 701
    Step = 702
    StepAfter = 703
    StepBefore = 704


class EnumHaasChartLineType(Enum):
    """EnumHaasChartLineType enumeration"""
    Line = 0
    Bars = 1
    Band = 2
    Circle = 3
    Cloud = 4
    DoubleColor = 5
    DoubleColorFill = 6
    Histogram = 7
    StackedArea = 9
    Volume = 10
    SignalBars = 11
    PricePlotVolume = 13
    Shape = 14


class EnumHaasChartPricePlotStyle(Enum):
    """EnumHaasChartPricePlotStyle enumeration"""
    CandleStick = 300
    CandleStickHLC = 301
    HeikinAshi = 302
    OHLC = 303
    HLC = 304
    CloseLine = 305
    Line = 306
    Mountain = 307
    Spread = 308
    SpreadCandle = 309


class EnumHaasChartShapeType(Enum):
    """EnumHaasChartShapeType enumeration"""
    Cross = 1600
    Add = 1601
    Circle = 1602
    TriangleUp = 1603
    TriangleDown = 1604
    Square = 1605
    Diamond = 1606
    Text = 1607
    Dash = 1608


class EnumHaasChartStatus(Enum):
    """EnumHaasChartStatus enumeration"""
    IsPerfect = 0
    IsEmpty = 1
    IsBroken = 2
    CompileError = 3
    IsRunning = 4
    IsLimit = 5


class EnumHaasChatPerson(Enum):
    """EnumHaasChatPerson enumeration"""
    Echo = 0
    Julia = 1
    Thomas = 2
    Edgar = 3
    Carlos = 4
    Eunomia = 5
    GPT = 6
    Gemini = 7
    David = 8
    Simone = 9


class EnumHaasCommandCategory(Enum):
    """EnumHaasCommandCategory enumeration"""
    ArrayHelper = 0
    PositionPrices = 1
    Charting = 2
    CustomCommands = 3
    CustomCommandsHelpers = 4
    EnumerationsTradingLR = 5
    EnumerationsColor = 6
    EnumerationsCharting = 7
    EnumerationsMovingAverages = 8
    EnumerationsPosition = 9
    EnumerationsParameterType = 10
    EnumerationsSignal = 11
    EnumerationsTrading = 12
    EnumerationsOrderType = 13
    EasySafeties = 14
    EasyInsurances = 15
    EasyIndicators = 16
    Equations = 17
    InputFields = 18
    InputSettings = 19
    ManagedTradingSignals = 20
    Mathematical = 21
    MemoryHelpers = 22
    Miscellaneous = 23
    PositionInformation = 24
    OrderHandling = 25
    OrderInformation = 26
    PriceData = 27
    PriceMarketInformation = 28
    ProfitInformation = 29
    Settings = 30
    SignalHelpers = 31
    StringHelpers = 32
    TechnicalAnalysis = 33
    TechnicalAnalysisHelpers = 34
    TimeInformation = 35
    TradeBot = 36
    TradeMarketInformation = 37
    UnmanagedTradingSignals = 38
    Wallet = 39
    FlowControl = 40
    EnumerationsCandlePattern = 41
    EnumerationsSignalType = 42
    EnumerationsDataType = 43
    EnumerationsArrayFilterType = 44
    SocialMedia = 45
    EnumerationsSourcePriceType = 46
    MachineLearningType = 47
    EnumerationsPositionMode = 48
    EnumerationsMarginMode = 49


class EnumHaasCommandParameterType(Enum):
    """EnumHaasCommandParameterType enumeration"""
    String = 0
    Number = 1
    Enum = 2
    Boolean = 3
    Dynamic = 4
    NumberOrTable = 6
    ListNumbers = 7
    ListDynamic = 8
    Function = 9
    Void = 10
    Connector = 11
    DynamicParams = 100
    EnumParams = 101
    BooleanParams = 102
    StringParams = 103
    NumberParams = 104
    ListNumberParams = 105
    NumberOrTableParams = 106


class EnumHaasCommandSyntaxType(Enum):
    """EnumHaasCommandSyntaxType enumeration"""
    Function = 1
    Enum = 15
    Color = 19


class EnumHaasCommandType(Enum):
    """EnumHaasCommandType enumeration"""
    ArrayAdd = 0
    ArrayAny = 1
    ArrayConcat = 2
    ArrayCount = 3
    ArrayFilter = 4
    ArrayIndex = 5
    ArrayIndexField = 6
    ArrayLast = 7
    ArrayNew = 8
    ArrayNewSorted = 9
    ArrayOffset = 10
    ArrayPop = 11
    ArrayRange = 12
    ArrayShift = 13
    ArrayUnshift = 14
    ArraySort = 16
    ArraySum = 17
    ArrayReplace = 18
    ReplaceBelow = 19
    ReplaceAbove = 20
    FilterBelow = 21
    FilterAbove = 22
    SourceManager = 23
    ArrayRemove = 24
    ArrayFind = 25
    ArrayDistinct = 26
    AverageExitPrice = 200
    AverageLongPrice = 201
    LastBuyPrice = 202
    LastExitLongPrice = 203
    LastExitShortPrice = 204
    LastNoPositionPrice = 205
    LastSellPrice = 206
    LastLongProfit = 207
    LastShortProfit = 208
    LastLongROI = 209
    LastShortROI = 210
    ChangeColorOpacity = 401
    ChartAddAxisLabel = 402
    ChartSetAxisOptions = 404
    ChartSetOptions = 405
    LineOptions = 406
    MarkCandle = 407
    Plot = 408
    PlotBands = 409
    PlotBars = 410
    PlotBBands = 411
    PlotBuySellZone = 412
    PlotCircle = 413
    PlotCloud = 414
    PlotDoubleColor = 415
    PlotHistogram = 416
    PlotHistogramSignals = 417
    PlotHorizontalLine = 418
    PlotHorizontalZone = 419
    PlotLineBuySellZone = 420
    PlotPrice = 422
    PlotSignalBar = 423
    PlotSignalEnum = 424
    PlotStackedArea = 425
    PlotVerticalLine = 426
    PlotVerticalZone = 427
    PlotVolume = 428
    PlotShape = 430
    PlotPivot = 431
    SetStackedAreaOpacity = 432
    PlotShapes = 433
    CustomCommand = 600
    DefineCommand = 601
    DefineOutput = 602
    DefineOutputIndex = 603
    DefineParameter = 604
    DefineEasyIndicatorParameters = 605
    DefineEasyIndicatorOutput = 606
    DefineIntervalOptimizationCommand = 607
    EasyABANDS = 800
    EasyADOSC = 801
    EasyAO = 802
    EasyAPO = 803
    EasyAROON = 804
    EasyAROONOSC = 805
    EasyBBANDS = 806
    EasyBOP = 807
    EasyCCI = 808
    EasyCMO = 809
    EasyCOPPOCK = 810
    EasyCRSI = 811
    EasyDMI = 812
    EasyDONCHIAN = 813
    EasyDPO = 814
    EasyDX = 815
    EasyICHIMOKU = 816
    EasyIMI = 817
    EasyKELTNER = 818
    EasyKRI = 819
    EasyLINEARREG = 820
    EasyMA = 821
    EasyMACD = 822
    EasyMFI = 823
    EasyMOM = 824
    EasyOBV = 825
    EasyPPO = 826
    EasyROC = 827
    EasyRSI = 828
    EasySSTOCH = 829
    EasySTOCH = 830
    EasySTOCHF = 831
    EasyTRIX = 832
    EasyTSI = 833
    EasyUDRSI = 834
    EasyWILLR = 835
    EasyZLMA = 836
    EasyAlice = 837
    EasyCDL = 838
    EasySLOWRSI = 839
    EasyFASTRSI = 840
    EasyBBANDSB = 841
    EasyBBANDSW = 842
    EasySTOCHRSI = 843
    EasyFIBONACCI = 844
    EasyKST = 845
    EasySAR = 846
    EasyDynamicLongShortLevels = 850
    EasyFixedLongShortLevels = 851
    EasyULTOSC = 852
    PercentagePriceChange = 1000
    NeverExitWithLoss = 1001
    OvercomeFeeCosts = 1002
    WaitAfterTrade = 1003
    TradeOnlyTrending = 1004
    TradeOnlySideways = 1005
    TradeOncePerBar = 1006
    DisableOnLosses = 1007
    StopLossCooldown = 1008
    AbsolutePriceChange = 1009
    OvercomeDoubleFeeCosts = 1010
    NeverEnterWithALoss = 1011
    WaitAfterOrder = 1012
    OrderOncePerBar = 1013
    ChandelierStopLoss = 1200
    DynamicStopLoss = 1201
    DynamicTakeProfit = 1202
    StopLoss = 1203
    TakeProfit = 1204
    TrailingArmStopLoss = 1205
    TrailingStopLoss = 1206
    ShrinkingTrailingStopLossCommand = 1207
    StopLossRoi = 1208
    TakeProfitRoi = 1209
    GrowingTrailingStopLoss = 1210
    DeactivateAfterEnter = 1211
    DeactivateAfterExit = 1212
    DeactivateAfterXOrders = 1213
    DeactivateAfterXPositions = 1214
    DeactivateAfterXIdleMinutes = 1215
    DeactivateAfterXActiveMinutes = 1216
    DeactivateOnLoss = 1217
    DeactivateOnProfit = 1218
    ChartAxisLeftSide = 1400
    ChartAxisLinear = 1401
    ChartAxisPercentage = 1402
    ChartAxisRightSide = 1403
    ChartLineDecorationDashed = 1404
    ChartLineDecorationDotted = 1405
    ChartLineDecorationSolid = 1406
    ChartLineStyleSmooth = 1407
    ChartLineStyleSpiked = 1408
    ChartLineStyleStep = 1409
    ChartLineStyleStepAfter = 1410
    ChartLineStyleStepBefore = 1411
    PricePlotStyleCandleStick = 1412
    PricePlotStyleCandleStickHLC = 1413
    PricePlotStyleCloseLine = 1414
    PricePlotStyleHeikinAshi = 1415
    PricePlotStyleHLC = 1416
    PricePlotStyleLine = 1417
    PricePlotStyleMountain = 1418
    PricePlotStyleOHLC = 1419
    PricePlotStyleSpread = 1420
    PricePlotStyleSpreadCandle = 1421
    ShapeTypeAdd = 1422
    ShapeTypeCross = 1423
    ShapeTypeCircle = 1424
    ShapeTypeTriangleUp = 1425
    ShapeTypeTriangleDown = 1426
    ShapeTypeSquare = 1427
    ShapeTypeDiamond = 1428
    ShapeTypeText = 1429
    ShapeTypeDash = 1430
    ColorAqua = 1600
    ColorBlack = 1601
    ColorBlue = 1602
    ColorCyan = 1603
    ColorDarkGray = 1604
    ColorDarkGreen = 1605
    ColorFuchsia = 1606
    ColorGold = 1607
    ColorGray = 1608
    ColorGreen = 1609
    ColorMaroon = 1610
    ColorOlive = 1611
    ColorOrange = 1612
    ColorPurple = 1613
    ColorRed = 1614
    ColorSkyBlue = 1615
    ColorTeal = 1616
    ColorWhite = 1617
    ColorYellow = 1618
    Color = 1619
    DemaType = 1800
    EmaType = 1801
    KamaType = 1802
    MamaType = 1803
    SmaType = 1804
    T3Type = 1805
    TemaType = 1806
    TrimaType = 1807
    WmaType = 1808
    LimitOrderType = 2000
    MarketOrderType = 2001
    NoTimeOutOrderType = 2002
    MakerOrCancelOrderType = 2003
    StopLimitOrderType = 2004
    StopMarketOrderType = 2005
    TakeProfitLimitOrderType = 2006
    TakeProfitMarketOrderType = 2007
    TrailingStopMarketOrderType = 2008
    BooleanType = 2200
    CallbackType = 2201
    DynamicType = 2202
    EnumType = 2203
    ListDynamicType = 2204
    ListNumberType = 2205
    NumberType = 2206
    StringType = 2207
    VoidType = 2208
    NoPosition = 2400
    PositionLong = 2401
    PositionShort = 2402
    SignalBuy = 2600
    SignalExitPosition = 2601
    SignalNone = 2602
    SignalSell = 2603
    IndicatorSignalCross = 2604
    IndicatorCenterCross = 2605
    SignalCenterCross = 2606
    BothCenterCross = 2607
    IndicatorThreshold = 2608
    SignalThreshold = 2609
    BothThreshold = 2610
    SignalExitLong = 2611
    SignalExitShort = 2612
    SignalReserveA = 2613
    SignalReserveB = 2614
    SignalError = 2615
    LeverageTrading = 2800
    MarginTrading = 2801
    SpotTrading = 2802
    CrossMarginMode = 2803
    IsolatedMarginMode = 2804
    HedgePositionMode = 2805
    OneWayPositionMode = 2806
    LR_Angle = 3000
    LR_Default = 3001
    LR_Intercept = 3002
    LR_Slope = 3003
    Compare = 3201
    Equals = 3202
    FalseValue = 3203  # Renamed from False (Python keyword)
    IsBiggerOrSmallerThan = 3204
    IsBiggerThan = 3205
    IsFalse = 3206
    IsNotNull = 3207
    IsNull = 3208
    IsSmallerThan = 3209
    IsTrue = 3210
    Or = 3211
    TrueValue = 3212
    IfNull = 3213
    NotEquals = 3214
    IsBiggerAndSmallerThan = 3215
    Branch = 3300
    IfElseIf = 3301
    Switch = 3302
    Merge = 3303
    DelayExecution = 3304
    Input = 3400
    InputAccount = 3401
    InputAccountMarket = 3402
    InputInterval = 3404
    InputLrTypes = 3405
    InputMarket = 3406
    InputMaTypes = 3407
    InputOptions = 3408
    InputOrderType = 3409
    InputPriceSource = 3410
    InputPriceSourceMarket = 3411
    InputCdlTypes = 3413
    InputGroupHeader = 3414
    InputTable = 3415
    InputTableOptions = 3416
    InputTableColumn = 3417
    InputSignalTypes = 3418
    InputTableColumnDropdown = 3419
    InputConstant = 3420
    InputSlider = 3421
    InputSignalManagement = 3422
    InputButton = 3423
    InputSourcePrice = 3424
    AccountGuid = 3600
    CurrentInterval = 3601
    Fee = 3602
    Leverage = 3603
    PriceMarket = 3604
    TradeAmount = 3605
    DoExitPosition = 3800
    DoLong = 3801
    DoShort = 3802
    DoSignal = 3803
    DoFlipPosition = 3804
    AddPercentage = 4000
    CompressTicks = 4001
    GetHigh = 4002
    GetHighs = 4003
    GetLow = 4004
    GetLows = 4005
    MathAbsolute = 4006
    MathAcos = 4007
    MathAdd = 4008
    MathAsin = 4009
    MathAtan = 4010
    MathAtan2 = 4011
    MathAverage = 4012
    MathCeil = 4013
    MathClamp = 4014
    MathCos = 4015
    MathCosh = 4016
    MathDelta = 4017
    MathDivide = 4018
    MathExp = 4019
    MathFloor = 4020
    MathLog = 4021
    MathLog10 = 4022
    MathMax = 4023
    MathMin = 4024
    MathMultiply = 4025
    MathPower = 4026
    MathRandom = 4027
    MathRound = 4028
    MathSign = 4029
    MathSin = 4030
    MathSinh = 4031
    MathSqrt = 4032
    MathSub = 4033
    MathTan = 4034
    MathTanh = 4035
    NumberMax = 4036
    NumberMin = 4037
    PI = 4038
    PriceChange = 4039
    Satoshi = 4040
    SubtractPercentage = 4041
    MathAverage2 = 4042
    MathSd = 4043
    MathTruncate = 4044
    Load = 4200
    Log = 4201
    LogError = 4202
    LogWarning = 4203
    Save = 4204
    SessionGet = 4205
    SessionSet = 4206
    LogWalletError = 4207
    Delete = 4208
    Comment = 4401
    Number = 4403
    Return = 4404
    Text = 4406
    HNC = 4407
    CustomReport = 4408
    GetType = 4409
    GetCommand = 4410
    ConvertNull = 4411
    GetPositionAmount = 4600
    GetPositionDirection = 4601
    GetPositionEnterPrice = 4602
    GetPositionMarket = 4603
    GetPositionProfit = 4604
    GetPositionROI = 4605
    LongAmount = 4606
    PositionContainer = 4607
    ShortAmount = 4608
    CreatePosition = 4610
    IsPositionClosed = 4611
    GetAllOpenPositions = 4612
    ClosePosition = 4613
    AdjustPosition = 4614
    CancelAllOrders = 4800
    CancelOrder = 4801
    IsAnyOrderFinished = 4802
    IsAnyOrderOpen = 4803
    IsOrderFilled = 4804
    IsOrderOpen = 4805
    IsBuyOrder = 4806
    IsSellOrder = 4807
    GetOrderCancelledAmount = 5000
    GetOrderFilledAmount = 5001
    GetOrderOpenTimeCommand = 5002
    OrderContainer = 5003
    GetAllOpenOrders = 5004
    GetAllFilledOrders = 5005
    GetFailedOrderMessageCommand = 5006
    GetOrderProfit = 5007
    GetBuyPrices = 5200
    GetClosePrices = 5201
    GetHeikenOpen = 5202
    GetHighLowClosePrices = 5203
    GetHighLowPrices = 5204
    GetHighPrices = 5205
    GetLowPrices = 5206
    GetOpenClosePrices = 5207
    GetOpenHighLowClosePrices = 5208
    GetOpenPrices = 5209
    GetSellPrices = 5211
    GetVolumes = 5212
    CurrentPrice = 5213
    GetSourcePrices = 5214
    GetBodyHighPrices = 5215
    GetBodyLowPrices = 5216
    AverageCandleSize = 5400
    AverageOrderbookSpread = 5401
    GetLastTrades = 5402
    GetOrderbookAsk = 5403
    GetOrderbookBid = 5404
    GetPriceLevel = 5405
    LastTradesSentiment = 5406
    OrderbookSentiment = 5407
    GetOrderbook = 5408
    CreateMarket = 5409
    LastSellTrades = 5410
    LastBuyTrades = 5411
    GetBotProfit = 5600
    GetBotROI = 5601
    GetCurrentProfit = 5602
    GetCurrentROI = 5603
    GetTradingReport = 5604
    SetBotRoiBaseValue = 5605
    DeactivateBot = 5800
    EnableHighSpeedUpdates = 5802
    EnableOrderPersistence = 5803
    OptimizedForInterval = 5804
    SetUsedOrderType = 5805
    HideTradeAmountSettings = 5806
    HideOrdersSettings = 5807
    Finalize = 5808
    SetLeverage = 5809
    GetMaxLeverage = 5810
    GetMarginMode = 5811
    SetMarginMode = 5812
    IsMarginModeSupported = 5813
    GetPositionMode = 5816
    SetPositionMode = 5817
    IsPositionModeSupported = 5818
    GetUsedOrderType = 5821
    GetHaasScriptVersion = 5822
    PauseBot = 5823
    ResumeBot = 5824
    IsBotPaused = 5825
    IsEnterpriseVersion = 5826
    DisableIndicatorContainerLogs = 5827
    GetLeverage = 5828
    SetTradeAmount = 5829
    GetAboveBelowSignal = 6000
    GetBuySellLevelSignal = 6001
    GetConsensusSignal = 6002
    GetCrossOverUnderSignal = 6003
    GetRemoteSignal = 6004
    GetThresholdSignal = 6005
    GetUnanimousSignal = 6006
    IgnoreSignalIf = 6007
    ReverseSignal = 6008
    SaveRemoteSignal = 6009
    UseSignalIf = 6010
    GetSuperSignal = 6011
    ConvertSignal = 6012
    DelaySignal = 6013
    GetWeightedConsensusSignal = 6014
    SignalWeight = 6015
    SignalMapper = 6016
    SignalProperties = 6017
    SignalToBool = 6018
    BoolToSignal = 6019
    SignalToLog = 6020
    PositionToBool = 6021
    GetWebHookSignal = 6022
    NewGuid = 6200
    StringContains = 6201
    StringExplode = 6202
    StringFromQuery = 6203
    StringIndexOf = 6204
    StringJoin = 6205
    StringSub = 6206
    Parse = 6207
    ParseJson = 6208
    ParseCsv = 6209
    ABANDS = 6400
    AD = 6401
    ADOSC = 6402
    ADX = 6403
    ADXR = 6404
    AO = 6405
    APO = 6406
    AROON = 6407
    AROONOSC = 6408
    ATR = 6409
    AVGDEV = 6410
    AVGPRICE = 6411
    BBANDS = 6412
    BETA = 6413
    BOP = 6414
    CCI = 6415
    ChandelierExitLong = 6416
    ChandelierExitShort = 6417
    CMO = 6418
    COPPOCK = 6419
    CORREL = 6420
    CRSI = 6421
    DEMA = 6422
    DONCHIAN = 6423
    DPO = 6424
    DX = 6425
    EMA = 6426
    HT_DCPERIOD = 6427
    HT_DCPHASE = 6428
    HT_PHASOR = 6429
    HT_SINE = 6430
    HT_TRENDLINE = 6431
    HT_TRENDMODE = 6432
    ICHIMOKU = 6433
    IMI = 6434
    KAMA = 6435
    KAMA2 = 6436
    KELTNER = 6437
    KRI = 6438
    LINEARREG = 6439
    MA = 6440
    MACD = 6441
    MACDEXT = 6442
    MACDFIX = 6443
    MAMA = 6444
    MAVP = 6445
    MAXINDEX = 6446
    MEDPRICE = 6447
    MFI = 6448
    MIDPOINT = 6449
    MIDPRICE = 6450
    MININDEX = 6451
    MINUSDI = 6452
    MINUSDM = 6453
    MOM = 6454
    NATR = 6455
    OBV = 6456
    PLUSDI = 6457
    PLUSDM = 6458
    PPO = 6459
    ROC = 6460
    RSI = 6461
    RSI_ALTB = 6462
    SAR = 6463
    SAREXT = 6464
    SMA = 6465
    SMA2 = 6466
    SSTOCH = 6467
    STDDEV = 6468
    STOCH = 6469
    STOCHF = 6470
    STOCHRSI = 6471
    T3 = 6472
    TEMA = 6473
    TRANGE = 6474
    TRIMA = 6475
    TRIX = 6476
    TSF = 6477
    TSI = 6478
    TYPPRICE = 6479
    UDRSI = 6480
    ULTOSC = 6481
    VAR = 6482
    WCLPRICE = 6483
    WILLR = 6484
    WiMA = 6485
    WMA = 6486
    WWS = 6487
    ZLEMA = 6488
    ZLMA = 6489
    CDL = 6490
    KST = 6491
    FastRSI = 6492
    SlowRSI = 6493
    ROCP = 6494
    ROCR = 6495
    ROCR100 = 6496
    CHOP = 6497
    CrossOver = 6600
    CrossOverSince = 6601
    CrossUnder = 6602
    CrossUnderSince = 6603
    GetSwing = 6604
    IsFalling = 6605
    IsRising = 6606
    IsFallingSince = 6607
    IsRisingSince = 6608
    LocateTimeVal = 6800
    Time = 6801
    CurrentSecond = 6802
    CurrentMinute = 6803
    CurrentHour = 6804
    CurrentDay = 6805
    CurrentDate = 6806
    CurrentWeek = 6807
    CurrentMonth = 6808
    CurrentYear = 6809
    CreateTimestamp = 6810
    AdjustTimestamp = 6811
    StartTimer = 6812
    GetTimer = 6813
    StopTimer = 6814
    OpenTime = 6815
    CloseTime = 6816
    IndicatorContainer = 7000
    InsuranceContainer = 7001
    SafetyContainer = 7002
    TradeBotContainer = 7003
    AmountLabel = 7200
    BaseCurrency = 7201
    ContractName = 7202
    ContractValue = 7203
    IsTradeAmountEnough = 7204
    LeverageUsedMargin = 7205
    MakerFee = 7206
    MarketType = 7207
    ParseTradeAmount = 7208
    ParseTradePrice = 7209
    ProfitLabel = 7210
    QuoteCurrency = 7211
    SetFee = 7212
    TakerFee = 7213
    UnderlyingAsset = 7214
    MinimumTradeAmount = 7215
    TradeMarketContainer = 7216
    PriceStep = 7217
    AmountDecimals = 7218
    PriceDecimals = 7219
    AmountStep = 7220
    IsValidMarket = 7221
    GetExchangeMarkets = 7222
    GetAccountMarkets = 7223
    PlaceBuyOrder = 7400
    PlaceExitLongOrder = 7401
    PlaceExitPositionOrder = 7402
    PlaceExitShortOrder = 7403
    PlaceGoLongOrder = 7404
    PlaceGoShortOrder = 7405
    PlaceSellOrder = 7406
    PlaceCancelledOrder = 7407
    MaxBuyAmount = 7600
    MaxExitLongAmount = 7601
    MaxExitShortAmount = 7602
    MaxSellAmount = 7603
    WalletAmount = 7604
    WalletCheck = 7605
    UserPositionContainer = 7606
    BalanceAmount = 7607
    Balance = 7608
    MarginToTradeAmount = 7609
    TwoCrowsType = 7800
    ThreeBlackCrowsType = 7801
    ThreeInsideType = 7802
    ThreeLineStrikeType = 7803
    ThreeOutsideType = 7804
    ThreeStarsInSouthType = 7805
    ThreeWhiteSoldiersType = 7806
    AdvanceBlockType = 7807
    BeltHoldType = 7808
    BreakawayType = 7809
    ClosingMarubozuType = 7810
    ConcealBabysWallType = 7811
    CounterAttackType = 7812
    DojiType = 7813
    DojiStarType = 7814
    DragonflyDojiType = 7815
    EngulfingType = 7816
    GapSideSideWhiteType = 7817
    GravestoneDojiType = 7818
    HammerType = 7819
    HangingManType = 7820
    HaramiType = 7821
    HaramiCrossType = 7822
    HignWaveType = 7823
    HikkakeType = 7824
    HikkakeModType = 7825
    HomingPigeonType = 7826
    IdenticalThreeCrowsType = 7827
    InNeckType = 7828
    InvertedHammerType = 7829
    KickingType = 7830
    KickingByLengthType = 7831
    LadderBottomType = 7832
    LongLeggedDojiType = 7833
    LongLineType = 7834
    MarubozuType = 7835
    MatchingLowType = 7836
    OnNeckType = 7837
    PiercingType = 7838
    RickshawManType = 7839
    RiseFallThreeMethodsType = 7840
    SeparatingLinesType = 7841
    ShootingStarType = 7842
    ShortLineType = 7843
    SpinningTopType = 7844
    StalledPatternType = 7845
    StickSandwichType = 7846
    TakuriType = 7847
    TasukiGapType = 7848
    ThrustingType = 7849
    TristarType = 7850
    UniqueThreeRiverType = 7851
    UpsideGapTwoCrowsType = 7852
    XSideGapThreeMethodsType = 7853
    AbandonedBabyType = 7854
    DarkCloudCoverType = 7855
    MatHoldType = 7856
    MorningDojiStarType = 7857
    MorningStarType = 7858
    EveningDojiStarType = 7859
    EveningStarType = 7860
    SimpleUpCandleType = 7861
    SimpleDownCandleType = 7862
    SimpleDoubleUpCandleType = 7863
    SimpleDoubleDownCandleType = 7864
    UnknownDataType = 7900
    NilDataType = 7901
    BoolDataType = 7902
    NumberDataType = 7903
    TextDataType = 7904
    ArrayDataType = 7905
    HncDataType = 7906
    FunctionDataType = 7907
    CommandDataType = 7908
    UserDataDataType = 7909
    TupleDataType = 7910
    VoidDataType = 7911
    ArrayFilterInclusiveType = 8000
    ArrayFilterExclusiveType = 8001
    ArrayFilterLessThanType = 8002
    ArrayFilterGreaterThanType = 8003
    BroadcastToSlack = 8100
    BroadcastToTelegram = 8101
    BroadcastToTwitter = 8102
    BroadcastToDiscord = 8103
    OpenPriceSourceType = 8200
    HighPriceSourceType = 8201
    LowPriceSourceType = 8202
    ClosePriceSourceType = 8203
    HLPriceSourceType = 8204
    HLCPriceSourceType = 8205
    OHLCPriceSourceType = 8206
    VolumeSourceType = 8207
    IsAbnormal = 8300
    SimpleForecastBySsa = 8301
    HindSightSignal = 8303
    InitExportData = 8400
    WriteExportData = 8401


class EnumHaasInputFieldType(Enum):
    """EnumHaasInputFieldType enumeration"""
    Number = 0
    Text = 1
    Checkbox = 2
    Dropdown = 3
    PriceSource = 4
    PriceSourceMarket = 5
    Account = 6
    AccountMarket = 7
    Market = 8
    Interval = 9
    Header = 10
    Table = 11
    Button = 12
    OrderType = 90
    ChartStyle = 91


class EnumHaasOrderDirection(Enum):
    """EnumHaasOrderDirection enumeration"""
    Buy = 0
    Sell = 1
    GoLong = 2
    ExitLong = 3
    GoShort = 4
    ExitShort = 5


class EnumHaasOrderStatus(Enum):
    """EnumHaasOrderStatus enumeration"""
    Unknown = 0
    Open = 1
    Completed = 2
    Cancelled = 3
    Pending = -2
    Failed = -1


class EnumHaasOrderTimeInForce(Enum):
    """EnumHaasOrderTimeInForce enumeration"""
    GoodTillCancel = 0
    FillOrKill = 1
    ImmediateOrCancel = 2


class EnumHaasOrderTriggerPrice(Enum):
    """EnumHaasOrderTriggerPrice enumeration"""
    LastPrice = 0
    MarkPrice = 1
    IndexPrice = 2


class EnumHaasOrderType(Enum):
    """EnumHaasOrderType enumeration"""
    Limit = 0
    Market = 1
    StopLimit = 2
    StopMarket = 3
    TakeProfitLimit = 4
    TakeProfitMarket = 5
    TrailingStopLimit = 6
    TrailingStopMarket = 7


class EnumHaasPositionDirection(Enum):
    """EnumHaasPositionDirection enumeration"""
    Long = 0
    Short = 1


class EnumHaasScriptMarketType(Enum):
    """EnumHaasScriptMarketType enumeration"""
    Spot = 1500
    Margin = 1501
    Leverage = 1502


class EnumHaasScriptOrderType(Enum):
    """EnumHaasScriptOrderType enumeration"""
    Limit = 500
    Market = 501
    NoTimeout = 502
    MakerOrCancel = 503
    StopLimit = 504
    StopMarket = 505
    TakeProfitLimit = 506
    TakeProfitMarket = 507
    TrailingStopMarket = 508
    Default = -1


class EnumHaasScriptStatus(Enum):
    """EnumHaasScriptStatus enumeration"""
    Private = 0
    Default = 1
    Community = 2
    Store = 3
    ReleaseToCommunity = 4
    ReleaseToStore = 5


class EnumHaasScriptType(Enum):
    """EnumHaasScriptType enumeration"""
    Lua = 0
    Visual = 1
    TradeBot = 2


class EnumHaasTradeSignal(Enum):
    """EnumHaasTradeSignal enumeration"""
    SignalLong = 201
    SignalShort = 202
    SignalExitPosition = 203
    SignalNone = 204
    SignalError = 205
    SignalExitLong = 206
    SignalExitShort = 207
    SignalReservedA = 208
    SignalReservedB = 209


class EnumHaasUserDataType(Enum):
    """EnumHaasUserDataType enumeration"""
    NoneValue = 0
    HaasNumberCollection = 1
    HaasCallback = 2
    HaasEnum = 3
    HaasResultContainer = 4
    HaasColor = 5
    HaasSignal = 6


class EnumLoginResult(Enum):
    """EnumLoginResult enumeration"""
    Success = 0
    InvalidUsernameOrPassword = 1
    Invalid2FACode = 2
    UnknownDevice = 3
    Failed = 4
    TwoFANeeded = 5
    Blocked = 6
    NotAllowed = 7
    ActivationNeeded = 8
    Banned = 9
    Unapproved = -1


class EnumMarginMode(Enum):
    """EnumMarginMode enumeration"""
    Cross = 0
    Isolated = 1


class EnumPlaceOrderResult(Enum):
    """EnumPlaceOrderResult enumeration"""
    Open = 0
    Filled = 1
    InvalidMarket = 2
    InvalidAmount = 3
    InvalidTriggerPrice = 4
    BelowMinimumTradeAmount = 5
    BelowMinimumTradeVolume = 6
    PostOnly = 7
    ReduceOnly = 8
    InsufficientFunds = 9
    TradingEngineException = 10
    LeverageMismatch = 11
    KrakenFuturesDustOrderLimit = 12
    GoodTillCancel = 13
    FillOrKill = 14
    ImmediateOrCancel = 15
    Failed = 16


class EnumRelationType(Enum):
    """EnumRelationType enumeration"""
    NoneValue = 0
    Bronze = 1
    Silver = 2
    Golden = 3


class EnumSharedScriptStatus(Enum):
    """EnumSharedScriptStatus enumeration"""
    Public = 0
    Private = 1
    Restricted = 2


class EnumUserBalanceMutation(Enum):
    """EnumUserBalanceMutation enumeration"""
    Deposit = 0
    Withdrawal = 1
    Transfer = 2


class EnumUserLabAlgorithm(Enum):
    """EnumUserLabAlgorithm enumeration"""
    BruteForce = 0
    Intelligent = 1
    Random = 2
    Cluster = 3


class EnumUserLabStatus(Enum):
    """EnumUserLabStatus enumeration"""
    Created = 0
    Queued = 1
    Running = 2
    Completed = 3
    Cancelled = 4


class EnumUserLabsBacktestStatus(Enum):
    """EnumUserLabsBacktestStatus enumeration"""
    Queued = 0
    Executing = 1
    Cancelled = 2
    Done = 3


class EnumUserOrderCancelStatus(Enum):
    """EnumUserOrderCancelStatus enumeration"""
    FullyCancelled = 0
    PartiallyCancelled = 1
    Failed = 2

