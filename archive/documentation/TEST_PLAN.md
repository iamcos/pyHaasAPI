# 🧪 Interactive Analysis System - Test Plan

## Overview
This test plan covers the new interactive analysis and decision-making CLI system, including cache management, interactive analysis, visualization, and bot creation workflows.

## Test Environment Setup
- **Environment**: Development with real HaasOnline API
- **Data**: Use existing cached backtest data
- **Dependencies**: Ensure all visualization libraries are installed

## Test Categories

### 1. 🔧 **Enhanced Cache Management Tests**

#### 1.1 Analysis Result Persistence
- [ ] **Test**: Save analysis results to JSON
- [ ] **Test**: Load analysis results from JSON
- [ ] **Test**: List all saved analysis results
- [ ] **Test**: Load latest analysis result for a lab
- [ ] **Test**: Load specific timestamp analysis result

#### 1.2 Cache Refresh Functionality
- [ ] **Test**: Refresh specific backtest cache
- [ ] **Test**: Refresh all backtests for a lab
- [ ] **Test**: Verify cache files are deleted and recreated

#### 1.3 Cache Directory Structure
- [ ] **Test**: Verify cache directory structure
- [ ] **Test**: Verify file naming conventions
- [ ] **Test**: Verify JSON file format and content

### 2. 📊 **Interactive Analyzer Tests**

#### 2.1 Basic Functionality
- [ ] **Test**: Connect to HaasOnline API
- [ ] **Test**: Load cached labs list
- [ ] **Test**: Analyze cached lab data
- [ ] **Test**: Display detailed analysis table

#### 2.2 Advanced Metrics Calculation
- [ ] **Test**: Calculate ROE (Return on Equity)
- [ ] **Test**: Calculate risk scores
- [ ] **Test**: Calculate stability scores
- [ ] **Test**: Calculate advanced metrics (Sharpe, Sortino, etc.)

#### 2.3 Sorting and Filtering
- [ ] **Test**: Sort by ROI
- [ ] **Test**: Sort by ROE
- [ ] **Test**: Sort by win rate
- [ ] **Test**: Sort by risk score
- [ ] **Test**: Sort by stability score
- [ ] **Test**: Apply filters (min ROI, max risk, etc.)

#### 2.4 Interactive Selection
- [ ] **Test**: Select single backtest by number
- [ ] **Test**: Select range of backtests
- [ ] **Test**: Select all backtests
- [ ] **Test**: Clear selection
- [ ] **Test**: List current selection
- [ ] **Test**: Save selection to JSON

#### 2.5 Comparison Features
- [ ] **Test**: Display side-by-side comparison
- [ ] **Test**: Show detailed metrics for selected backtests
- [ ] **Test**: Handle empty selection gracefully

### 3. 📈 **Visualization Tool Tests**

#### 3.1 Chart Generation
- [ ] **Test**: Generate equity curve charts
- [ ] **Test**: Generate performance comparison charts
- [ ] **Test**: Generate risk analysis charts
- [ ] **Test**: Generate trade analysis charts

#### 3.2 Chart Quality and Content
- [ ] **Test**: Verify chart file creation
- [ ] **Test**: Verify chart content accuracy
- [ ] **Test**: Verify chart formatting and labels
- [ ] **Test**: Verify chart file sizes and quality

#### 3.3 Error Handling
- [ ] **Test**: Handle missing visualization libraries
- [ ] **Test**: Handle missing backtest data
- [ ] **Test**: Handle invalid backtest IDs
- [ ] **Test**: Handle empty backtest lists

### 4. 🤖 **Bot Creation Workflow Tests**

#### 4.1 Analysis Result Loading
- [ ] **Test**: Load saved analysis results
- [ ] **Test**: Load specific lab analysis results
- [ ] **Test**: Handle missing analysis results gracefully

#### 4.2 Bot Creation Process
- [ ] **Test**: Create bots from analysis results
- [ ] **Test**: Validate lab existence on server
- [ ] **Test**: Optional backtest validation
- [ ] **Test**: Bot naming convention
- [ ] **Test**: Account assignment

#### 4.3 Bot Activation
- [ ] **Test**: Activate created bots
- [ ] **Test**: Verify bot configuration
- [ ] **Test**: Handle activation failures

### 5. 🔄 **Integration Workflow Tests**

#### 5.1 Complete Workflow
- [ ] **Test**: Cache labs → Interactive analyze → Visualize → Create bots
- [ ] **Test**: Resume from any step using cached data
- [ ] **Test**: Handle interruptions gracefully

#### 5.2 Data Consistency
- [ ] **Test**: Verify data consistency across all steps
- [ ] **Test**: Verify analysis results match cached data
- [ ] **Test**: Verify bot creation uses correct analysis data

### 6. ⚠️ **Error Handling and Edge Cases**

#### 6.1 API Connection Issues
- [ ] **Test**: Handle API connection failures
- [ ] **Test**: Handle authentication failures
- [ ] **Test**: Handle API rate limiting

#### 6.2 Data Issues
- [ ] **Test**: Handle missing cached data
- [ ] **Test**: Handle corrupted cache files
- [ ] **Test**: Handle empty lab lists
- [ ] **Test**: Handle labs with no backtests

#### 6.3 User Input Issues
- [ ] **Test**: Handle invalid command line arguments
- [ ] **Test**: Handle invalid interactive selections
- [ ] **Test**: Handle keyboard interrupts

## Manual Testing Procedures

### Interactive Testing Checklist

#### Phase 1: Cache Management
1. **Run cache-labs command**
   ```bash
   python pyHaasAPI/cli/main.py cache-labs --help
   python pyHaasAPI/cli/main.py cache-labs
   ```
   - [ ] Verify command help displays correctly
   - [ ] Verify caching process starts
   - [ ] Verify progress indicators work
   - [ ] Verify cache files are created

2. **Test cache refresh**
   ```bash
   python pyHaasAPI/cli/main.py cache-labs --refresh
   ```
   - [ ] Verify existing cache is refreshed
   - [ ] Verify new data is cached

#### Phase 2: Interactive Analysis
1. **Run interactive analyzer**
   ```bash
   python pyHaasAPI/cli/main.py interactive-analyze --help
   python pyHaasAPI/cli/main.py interactive-analyze --sort-by roe
   ```
   - [ ] Verify help displays correctly
   - [ ] Verify analysis starts and shows progress
   - [ ] Verify detailed metrics table displays
   - [ ] Verify sorting by ROE works

2. **Test interactive selection**
   - [ ] Try selecting single backtest: `1`
   - [ ] Try selecting range: `1-5`
   - [ ] Try selecting all: `all`
   - [ ] Try clearing selection: `clear`
   - [ ] Try listing selection: `list`
   - [ ] Try finishing: `done`

3. **Test comparison and saving**
   - [ ] Verify side-by-side comparison displays
   - [ ] Verify selection is saved to JSON
   - [ ] Verify summary statistics are accurate

#### Phase 3: Visualization
1. **Test visualization tool**
   ```bash
   python pyHaasAPI/cli/main.py visualize --help
   python pyHaasAPI/cli/main.py visualize --all-labs
   ```
   - [ ] Verify help displays correctly
   - [ ] Verify charts are generated
   - [ ] Verify chart files are created in correct directory
   - [ ] Verify chart content is accurate

2. **Test specific backtest visualization**
   ```bash
   python pyHaasAPI/cli/main.py visualize --backtest-ids <backtest_id>
   ```
   - [ ] Verify individual backtest charts are generated
   - [ ] Verify equity curves are accurate
   - [ ] Verify trade analysis charts are generated

#### Phase 4: Bot Creation
1. **Test bot creation from analysis**
   ```bash
   python pyHaasAPI/cli/main.py create-bots-from-analysis --help
   python pyHaasAPI/cli/main.py create-bots-from-analysis --top-count 3
   ```
   - [ ] Verify help displays correctly
   - [ ] Verify analysis results are loaded
   - [ ] Verify bots are created successfully
   - [ ] Verify bot configuration is correct

2. **Test bot activation**
   ```bash
   python pyHaasAPI/cli/main.py create-bots-from-analysis --activate
   ```
   - [ ] Verify bots are activated
   - [ ] Verify activation status is reported

## Automated Test Scripts

### Test Script 1: Cache Management
```python
# test_cache_management.py
def test_analysis_result_persistence():
    """Test saving and loading analysis results"""
    pass

def test_cache_refresh():
    """Test cache refresh functionality"""
    pass
```

### Test Script 2: Interactive Analyzer
```python
# test_interactive_analyzer.py
def test_metrics_calculation():
    """Test advanced metrics calculations"""
    pass

def test_sorting_and_filtering():
    """Test sorting and filtering functionality"""
    pass
```

### Test Script 3: Visualization Tool
```python
# test_visualization_tool.py
def test_chart_generation():
    """Test chart generation functionality"""
    pass

def test_chart_content():
    """Test chart content accuracy"""
    pass
```

## Success Criteria

### Functional Requirements
- [ ] All CLI commands execute without errors
- [ ] Interactive selection works correctly
- [ ] Charts are generated with accurate data
- [ ] Bot creation uses correct analysis data
- [ ] Cache management works reliably

### Performance Requirements
- [ ] Analysis completes within reasonable time
- [ ] Chart generation is efficient
- [ ] Memory usage is reasonable
- [ ] Cache operations are fast

### User Experience Requirements
- [ ] Commands are intuitive and well-documented
- [ ] Progress indicators are clear
- [ ] Error messages are helpful
- [ ] Output is well-formatted and readable

## Test Data Requirements

### Required Test Data
- [ ] At least 3 labs with cached backtest data
- [ ] Backtests with varying performance metrics
- [ ] Backtests with different trade counts and win rates
- [ ] Backtests with different risk profiles

### Test Environment Setup
- [ ] HaasOnline API connection configured
- [ ] Visualization libraries installed (matplotlib, seaborn, pandas, numpy)
- [ ] Cache directory with existing data
- [ ] Test accounts available for bot creation

## Risk Assessment

### High Risk Areas
- [ ] Interactive selection input handling
- [ ] Chart generation with missing data
- [ ] Bot creation with invalid analysis data
- [ ] Cache corruption handling

### Mitigation Strategies
- [ ] Comprehensive input validation
- [ ] Graceful error handling
- [ ] Data validation before bot creation
- [ ] Cache integrity checks

## Test Execution Schedule

### Phase 1: Unit Tests (Day 1)
- [ ] Cache management tests
- [ ] Metrics calculation tests
- [ ] Basic functionality tests

### Phase 2: Integration Tests (Day 2)
- [ ] Interactive analyzer tests
- [ ] Visualization tool tests
- [ ] Bot creation workflow tests

### Phase 3: End-to-End Tests (Day 3)
- [ ] Complete workflow tests
- [ ] Error handling tests
- [ ] Performance tests

### Phase 4: User Acceptance Tests (Day 4)
- [ ] Manual testing procedures
- [ ] User experience validation
- [ ] Documentation review

## Test Results Documentation

### Test Report Template
- Test case ID
- Test description
- Expected result
- Actual result
- Pass/Fail status
- Notes and observations

### Bug Tracking
- Bug ID
- Description
- Severity
- Steps to reproduce
- Expected vs actual behavior
- Fix status

## Conclusion

This comprehensive test plan ensures that the interactive analysis system is thoroughly tested across all functionality areas, from basic operations to complex workflows. The combination of automated tests and manual procedures provides confidence in the system's reliability and user experience.






