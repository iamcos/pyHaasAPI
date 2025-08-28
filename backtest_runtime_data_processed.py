from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class Colors:
    Font: str
    Axis: str
    Grid: str
    Text: str
    Background: str
    PriceGhostLine: str
    VolumeGhostLine: str


@dataclass
class Chart:
    Guid: str
    Interval: int
    Charts: Dict[str, Any]
    Colors: Colors
    IsLastPartition: bool
    Status: int


@dataclass
class Fees:
    FC: float
    FR: float
    TFC: float
    FPC: Dict[str, float]


@dataclass
class Performance:
    SP: float
    SB: float
    PC: float
    BC: float
    GP: float
    RP: float
    UP: float
    ROI: float
    RM: float
    CRM: float
    RPH: List[float]
    ROIH: List[float]


@dataclass
class Orders:
    F: int
    P: int
    C: int
    R: int
    A: int
    L: int
    PT: int
    LT: int
    BW: float
    BL: float


@dataclass
class Positions:
    C: int
    W: int
    AP: float
    APS: float
    APM: float
    TEM: float
    AW: float
    BW: float
    TW: float
    AL: float
    BL: float
    TL: float
    PH: List[float]


@dataclass
class Trades:
    SHR: float
    SOR: float
    WP: float
    WLP: float
    PF: float
    CPC: float
    TR: float
    CSR: float
    OWR: float
    OLR: float
    PMR: float
    BW: float
    BL: float
    HP: float
    LP: float
    TM: float
    AVM: float
    AVP: float


@dataclass
class Report:
    AID: str
    M: str
    AL: str
    ML: str
    PL: str
    F: Fees
    PR: Performance
    O: Orders
    P: Positions
    T: Trades


@dataclass
class Order:
    paid: str
    pa: int
    id: str
    eid: str
    ot: int
    ct: int
    to: int
    d: int
    t: int
    p: float
    tp: float
    ep: float
    a: float
    af: float
    fe: float
    fc: str
    m: float
    pr: float
    r: float
    cr: int
    n: str


@dataclass
class ManagedPosition:
    pg: str
    g: str
    ac: str
    ma: str
    le: float
    d: int
    mt: int
    pl: Optional[str]
    al: Optional[str]
    pd: int
    ad: int
    ot: int
    ct: int
    ic: bool
    ap: float
    t: float
    av: float
    io: float
    eno: List[Any]
    exo: List[Any]
    cp: float
    fe: float
    rp: float
    up: float
    roi: float
    hpip: float
    lpip: float


@dataclass
class FinishedPosition:
    pg: str
    g: str
    ac: str
    ma: str
    le: float
    d: int
    mt: int
    pl: str
    al: str
    pd: int
    ad: int
    ot: int
    ct: int
    ic: bool
    ap: float
    t: float
    av: float
    io: float
    eno: List[Order]
    exo: List[Order]
    cp: float
    fe: float
    rp: float
    up: float
    roi: float
    hpip: float
    lpip: float


@dataclass
class InputField:
    T: int
    ST: int
    G: str
    K: str
    EK: str
    N: str
    TT: str
    V: str
    D: str
    O: Optional[Dict[str, str]]
    MIN: float
    MAX: float


@dataclass
class BacktestData:
    Chart: Chart
    CompilerErrors: List[Any]
    Reports: Dict[str, Report]
    CustomReport: Dict[str, Any]
    ScriptNote: str
    TrackedOrderLimit: int
    OpenOrders: List[Any]
    FailedOrders: List[Any]
    ManagedLongPosition: ManagedPosition
    ManagedShortPosition: ManagedPosition
    UnmanagedPositions: List[Any]
    FinishedPositions: List[FinishedPosition]
    InputFields: Dict[str, InputField]
    ScriptMemory: Dict[str, Any]
    LocalMemory: Dict[str, Any]
    RedisKeys: List[Any]
    Files: Dict[str, Any]
    LogId: str
    LogCount: int
    ExecutionLog: List[Any]
    UserId: str
    BotId: str
    BotName: str
    ScriptId: str
    ScriptName: str
    Activated: bool
    Paused: bool
    IsWhiteLabel: bool
    ActivatedSince: int
    DeactivatedSince: int
    DeactivatedReason: str
    AccountId: str
    PriceMarket: str
    Leverage: float
    MarginMode: int
    PositionMode: int
    TradeAmount: float
    OrderTemplate: int
    DefaultInterval: int
    DefaultChartType: int
    HideTradeAmountSettings: bool
    HideOrderSettings: bool
    OrderPersistenceEnabled: bool
    OrderPersistenceLimit: int
    EnableHighSpeedUpdates: bool
    UpdateAfterCompletedOrder: bool
    IndicatorContainerLogs: bool
    IsScriptOk: bool
    TradeAmountError: bool
    ScriptTradeAmountError: bool
    UpdateCounter: int
    IsSpotSupported: bool
    IsMarginSupported: bool
    IsLeverageSupported: bool
    IsManagedTrading: bool
    IsOneDirection: bool
    IsMultiMarket: bool
    IsRemoteSignalBased: bool
    IsWebHookBased: bool
    WebHookSignalId: str
    IsTAUsed: bool
    Timestamp: int
    MinuteTimestamp: int
    LastUpdateTimestamp: int


@dataclass
class BacktestRuntimeResponse:
    Success: bool
    Error: str
    Data: BacktestData
