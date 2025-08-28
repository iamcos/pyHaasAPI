# Lab to Bot Automation - Complete System Plan

## 🎯 Executive Summary

Create a fully autonomous system that analyzes lab backtests and converts the best performing ones into live trading bots. The system will handle account management, bot creation, and deployment with minimal human intervention.

## 📋 System Architecture

### Core Components

1. **Lab Analyzer** - Analyzes all backtests in a lab
2. **Bot Recommender** - Identifies top-performing backtests for bot creation
3. **Account Manager** - Manages account inventory and allocation
4. **Bot Creator** - Creates bots from recommended backtests
5. **Deployment Orchestrator** - Coordinates the entire process

### Data Flow

```
Lab ID Input → Lab Analyzer → Bot Recommender → Account Manager → Bot Creator → Deployment Success
                      ↓              ↓              ↓              ↓
               Backtest Data → Recommendations → Account Assignment → Live Bots
```

## 🎯 Detailed Requirements

### 1. **Lab Analysis Phase**

#### Input
- Lab ID (string)
- Optional: Max bots to create (default: 10)
- Optional: Minimum performance thresholds

#### Process
1. **Retrieve all backtests** from the lab using existing `financial_analytics.py` logic
2. **Analyze performance metrics** for each backtest:
   - Total profit/loss
   - Win rate percentage
   - ROI percentage
   - Max drawdown
   - Sharpe ratio
   - Profit factor
   - Duration days
   - Total number of trades
   - Quality score (0-100)
3. **Apply diversity filtering**:
   - Compare backtests for statistical similarity
   - Remove duplicates with similar metrics (±5% ROI, ±10% trade count)
   - Keep only one representative from each similar group
   - Prioritize higher quality score within similar groups

#### Output
- List of diverse backtests with complete metrics
- Sorted by performance score
- Filtered by profitability criteria and diversity
- Guaranteed variety in trading approaches and results

### 2. **Bot Recommendation Phase**

#### Selection Criteria
1. **Profitability**: Must have positive total profit
2. **Consistency**: Minimum win rate (default: 40%)
3. **Risk Management**: Max drawdown < 30% of total profit
4. **Sample Size**: Minimum trades (default: 5)
5. **Quality Score**: Top performers by overall score

#### Ranking Algorithm
```python
overall_score = (
    profitability_weight * (total_profit / abs(total_profit)) +
    win_rate_weight * (win_rate / 100) +
    roi_weight * (roi_percentage / 100) +
    risk_weight * (1 - max_drawdown_percentage / 100) +
    consistency_weight * (total_trades / 100)
)
```

#### Output
- Ranked list of recommended backtests
- Limited to max_bots parameter
- Each with recommended bot name: `"lab_name + profit_pct + pop/gen"`

### 3. **Account Management Phase**

#### Current Account Inventory
- Accounts named: `4AA-10k`, `4AB-10k`, etc. (server adds [Sim] prefix automatically)
- Each has exactly 10,000 USDT
- Some already have bots associated
- All on Binance Futures

#### Process
1. **Inventory Discovery**:
   - Get all existing accounts
   - Identify which have associated bots by getting all the bots
   - Map bot_id ↔ account_id relationships

2. **Account Allocation**:
   - Find free accounts (no bot association)
   - Sort by account name for predictable assignment
   - Reserve accounts for recommended bots

3. **Account Creation (if needed)**:
   - Follow naming scheme: `4{letter}{letter}{letter}-10k` (server adds [Sim] prefix automatically)
   - Setup process (3-step sequence):
     1. **Create**: Create simulated account via API
     2. **Withdraw All**: Withdraw each coin individually (including USDT) to zero balance
     3. **Deposit**: Deposit exactly 10,000 USDT
     - Verify final balance shows 10,000 USDT

#### Output
- Mapping of recommended backtest → assigned account
- List of newly created accounts (if any)

### 4. **Bot Creation Phase**

#### Bot Configuration
- **Name**: `"lab_name + profit_pct + pop/gen"` (e.g., "ADX BB STOCH Scalper +469% pop/gen")
- **Account**: Assigned account ID (10,000 USDT balance)
- **Script**: Copy from backtest script
- **Parameters**: Copy from backtest parameters
- **Settings**: Copy from backtest configuration
- **Trading Mechanics**:
  - **Trading Pairs**: ETH/USDT, BTC/USDT, and other USDT pairs
  - **Position Size**: Fixed 2,000 USDT equivalent per position (configurable)
  - **Fixed Position**: Bot starts with 2,000 USDT equivalent in the first trading pair
  - **Example**: Buy/sell exactly 2,000 USDT worth of ETH when trading ETH/USDT

#### Process
1. **Retrieve backtest details**:
   - Script content
   - Parameter values
   - Configuration settings
   - Market information

2. **Create bot**:
   - Use `CREATE_BOT` API endpoint
   - Set bot name with naming scheme
   - Associate with assigned account
   - Copy all backtest settings

3. **Verification**:
   - Confirm bot creation success
   - Verify account association
   - Check bot status

#### Output
- List of successfully created bots
- Mapping of bot_id → account_id → backtest_id
- Error log for failed creations

### 5. **Orchestration & Error Handling**

#### Main Controller
```python
def create_bots_from_lab(lab_id, max_bots=10, min_score=70):
    """
    Complete autonomous pipeline from lab analysis to bot deployment
    """

    # Phase 1: Analyze lab
    backtests = analyze_lab_backtests(lab_id)

    # Phase 2: Get recommendations
    recommendations = recommend_bots(backtests, max_bots, min_score)

    # Phase 3: Manage accounts
    account_mapping = manage_accounts(recommendations)

    # Phase 4: Create bots
    bots_created = create_bots(recommendations, account_mapping)

    # Phase 5: Report results
    return generate_deployment_report(bots_created)
```

#### Error Handling Strategy
- **Graceful degradation**: Continue with available accounts/bots
- **Rollback capability**: Clean up partially created resources
- **Comprehensive logging**: Track all operations and failures
- **Retry logic**: Handle transient API failures

## 🛠️ Technical Implementation Plan

### Phase 1: Core Components Development

#### 1.1 Enhanced Lab Analyzer ✅ COMPLETED
- Created `wfo_analyzer.py` with comprehensive WFO capabilities
- Implemented diversity filtering algorithm with configurable thresholds
- Added bot recommendation system with risk assessment
- Enhanced metrics calculation (Sortino, Calmar ratios, stability scores)

#### 1.2 Account Management System
- Consolidate existing account creation code
- Add account discovery and mapping functionality
- Implement account reservation system

#### 1.3 Bot Creation Engine
- API integration for bot creation
- Parameter copying from backtests
- Bot naming scheme implementation

### Phase 2: Integration & Testing

#### 2.1 Integration Testing
- Test with existing labs
- Verify account management works
- Ensure bot creation succeeds

#### 2.2 Error Scenario Testing
- Test with insufficient accounts
- Test with bot creation failures
- Test with network/API issues

### Phase 3: Production Deployment

#### 3.1 Main Script Creation
- `lab_to_bot_automation.py` - Main orchestration script
- Command-line interface
- Configuration options

#### 3.2 Documentation
- Usage instructions
- Troubleshooting guide
- API reference

## 📊 Success Metrics

### Quantitative Metrics
- **Bot Creation Success Rate**: % of recommended bots successfully created
- **Account Utilization**: % of available accounts used
- **Processing Time**: Average time to analyze lab and create bots
- **Error Rate**: % of operations that fail

### Qualitative Metrics
- **Autonomy Level**: % of process that runs without human intervention
- **Reliability**: System uptime and consistent performance
- **Maintainability**: Code clarity and documentation quality

## 🔄 Configuration Options

### Bot Selection Criteria
```python
@dataclass
class BotSelectionConfig:
    # Core bot selection criteria (all configurable)
    max_bots_per_lab: int = 10
    min_total_profit: float = 0.0
    min_win_rate: float = 40.0
    max_drawdown_pct: float = 30.0
    min_trades: int = 5
    min_quality_score: int = 70

    # Scoring weights (adjustable)
    profitability_weight: float = 0.3
    win_rate_weight: float = 0.2
    roi_weight: float = 0.2
    risk_weight: float = 0.2
    consistency_weight: float = 0.1

    # Diversity filtering (configurable thresholds)
    roi_similarity_threshold: float = 0.05  # ±5%
    trade_count_similarity_threshold: float = 0.10  # ±10%
    win_rate_similarity_threshold: float = 0.08  # ±8%

@dataclass
class BotConfig:
    # Trading configuration (all adjustable)
    position_size_usdt: float = 2000.0  # Fixed position size in USDT
    max_position_multiplier: float = 1.0  # Default: 1x position size
    enable_dynamic_positioning: bool = False  # Future feature flag

### Trading Mechanics Clarification
```python
# Example: ETH/USDT Trading with 2,000 USDT Position Limit
# Account Balance: 10,000 USDT
# Position Size Limit: 2,000 USDT equivalent
#
# If ETH price is $2,000:
# - Can buy/sell up to 1 ETH (2,000 USDT / 2,000 = 1 ETH)
#
# If ETH price is $4,000:
# - Can buy/sell up to 0.5 ETH (2,000 USDT / 4,000 = 0.5 ETH)
#
# This ensures consistent risk management regardless of coin price
```

### Diversity Filtering Algorithm
```python
def filter_similar_strategies(backtests: List[BacktestResult], config: BotSelectionConfig) -> List[BacktestResult]:
    """
    Remove similar-performing strategies to ensure diversity in bot selection.

    Algorithm:
    1. Sort backtests by overall quality score
    2. For each backtest, compare with already selected ones
    3. Skip if too similar (±5% ROI, ±10% trade count, ±8% win rate)
    4. Keep the highest quality score from similar groups
    5. Return diverse set of top performers
    """
    # Implementation details in Phase 1 development
    pass
```

### Account Management
```python
@dataclass
class AccountConfig:
    account_suffix: str = "-10k"  # Server adds [Sim] prefix automatically
    initial_balance: float = 10000.0
    required_currency: str = "USDT"
    exchange: str = "BINANCEFUTURES"
```

### Bot Naming
```python
def generate_bot_name(lab_name: str, backtest_metrics: dict) -> str:
    """Generate bot name: lab_name + profit_pct + pop/gen"""
    profit_pct = round(backtest_metrics['roi_percentage'])
    # Always include both "pop" and "gen" in the name format
    return f"{lab_name} +{profit_pct}% pop/gen"
```

## 📁 File Structure

```
lab_to_bot_automation/
├── __init__.py
├── main.py                    # Main orchestration script
├── lab_analyzer.py           # Lab analysis functionality
├── bot_recommender.py        # Bot recommendation logic
├── account_manager.py        # Account management system
├── bot_creator.py           # Bot creation engine
├── config.py                # Configuration classes
├── utils.py                 # Utility functions
└── README.md               # Documentation
```

## 🎯 Usage Examples

### Basic Usage
```bash
# Analyze lab and create up to 10 bots
python lab_to_bot_automation.py --lab-id "6e04e13c-1a12-4759-b037-b6997f830edf"

# Custom configuration
python lab_to_bot_automation.py \
    --lab-id "6e04e13c-1a12-4759-b037-b6997f830edf" \
    --max-bots 5 \
    --min-score 80 \
    --min-profit 100
```

### Advanced Usage
```python
from lab_to_bot_automation import create_bots_from_lab

# Custom configuration
config = BotSelectionConfig(
    max_bots_per_lab=15,
    min_win_rate=50.0,
    min_quality_score=75
)

results = create_bots_from_lab(
    lab_id="6e04e13c-1a12-4759-b037-b6997f830edf",
    config=config
)

print(f"Created {len(results['bots_created'])} bots")
for bot in results['bots_created']:
    print(f"- {bot['name']} on account {bot['account']}")  # e.g., "ADX BB STOCH Scalper +469% pop/gen"
```

## ⚠️ Risk Mitigation

### 1. **Account Safety**
- Never touch accounts with existing bots
- Verify account balances before assignment
- Implement rollback for failed bot creation

### 2. **API Rate Limiting**
- Implement delays between API calls
- Batch operations where possible
- Handle API quota exhaustion

### 3. **Data Integrity**
- Validate all data before bot creation
- Implement checksums for critical operations
- Log all state changes

### 4. **Error Recovery**
- Checkpoint system for resumable operations
- Automatic cleanup of failed resources
- Comprehensive error reporting

## 🔄 Next Steps

### Immediate Actions
1. **Review existing code** in `server_setup.py` and `setup_trading_accounts.py`
2. **Consolidate account creation logic** into reusable components
3. **Create configuration system** for bot selection criteria
4. **Implement lab analysis enhancement** in existing financial analytics

### Development Phases
1. **Phase 1**: Core component development (1-2 weeks)
2. **Phase 2**: Integration testing (3-5 days)
3. **Phase 3**: Production deployment and documentation (2-3 days)

### Success Criteria
- [ ] Can analyze any lab autonomously
- [ ] Creates bots with proper naming and configuration
- [ ] Manages accounts automatically (create when needed)
- [ ] Handles all error scenarios gracefully
- [ ] Provides comprehensive reporting and logging
- [ ] Zero human intervention required for normal operation

---

**Status**: ✅ PLANNING COMPLETE
**Next**: Begin implementation of core components
**Estimated Timeline**: 2-3 weeks for full implementation
