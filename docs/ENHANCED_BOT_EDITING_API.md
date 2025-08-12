# Enhanced Bot Editing API

## Overview

This document describes the comprehensive bot editing capabilities added to the pyHaasAPI library. These enhancements make bot parameter editing a breeze by providing multiple levels of control and validation.

## 🎯 **What Makes Bot Editing a Breeze**

### **1. Multiple Editing Approaches**
- **Whole Bot**: Edit entire bot object at once
- **Individual Parameters**: Edit single parameters by human-readable names
- **Group-based Editing**: Edit multiple parameters belonging to the same group
- **Bulk Validation**: Validate multiple parameter changes before applying

### **2. Comprehensive Data Retrieval**
- **Complete Bot Object**: Combines all data sources (GET_BOT, GET_RUNTIME, GET_RUNTIME_LOGBOOK, GET_RUNTIME_CLOSED_POSITIONS)
- **Parameter Metadata**: Full constraints, options, and type information
- **Group Organization**: Parameters organized by their groups
- **Closed Positions**: Historical trading data

### **3. Smart Validation**
- **Type Checking**: Automatic type conversion and validation
- **Range Validation**: Min/max value checking
- **Option Validation**: Enum/option value validation
- **Pre-flight Validation**: Validate changes before applying

## 📚 **API Functions**

### **Core Functions**

#### `get_comprehensive_bot(executor, bot_id)`
Mimics the web interface by combining all bot data sources:
- Basic bot information (GET_BOT)
- Runtime data and script parameters (GET_RUNTIME)
- Recent logs (GET_RUNTIME_LOGBOOK)
- Closed positions (GET_RUNTIME_CLOSED_POSITIONS)

```python
comprehensive_bot = get_comprehensive_bot(executor, bot_id)
print(f"Basic Info: {comprehensive_bot['basic_info']}")
print(f"Parameters: {comprehensive_bot['script_parameters']}")
print(f"Logs: {len(comprehensive_bot['recent_logs'])} entries")
print(f"Closed Positions: {len(comprehensive_bot['closed_positions'])}")
```

#### `edit_bot_parameter_by_name(executor, bot_id, parameter_name, new_value)`
Edit a single parameter using its human-readable name:

```python
# Edit stop loss by name
updated_bot = edit_bot_parameter_by_name(
    executor, 
    bot_id, 
    "Stop Loss (%)", 
    10
)
```

#### `edit_bot_parameters_by_group(executor, bot_id, group_name, parameters)`
Edit multiple parameters in the same group:

```python
# Edit all BBands parameters at once
bb_changes = {
    "BBands Length": 15,
    "BBands DevUp": 2.5,
    "BBands DevDown": 2.5
}
updated_bot = edit_bot_parameters_by_group(
    executor,
    bot_id,
    "MadHatter BBands",
    bb_changes
)
```

### **Validation Functions**

#### `validate_bot_parameters(executor, bot_id, parameters)`
Validate parameter changes without applying them:

```python
test_changes = {
    "Stop Loss (%)": 10,
    "Take Profit (%)": 15,
    "BBands Length": 20
}
result = validate_bot_parameters(executor, bot_id, test_changes)
print(f"Valid: {result['valid']}")
print(f"Invalid: {result['invalid']}")
```

### **Information Functions**

#### `get_bot_parameter_groups(executor, bot_id)`
Get all parameter groups and their parameters:

```python
groups = get_bot_parameter_groups(executor, bot_id)
for group_name, params in groups.items():
    print(f"Group '{group_name}': {params}")
```

#### `get_bot_parameter_metadata(executor, bot_id)`
Get detailed metadata for all parameters:

```python
metadata = get_bot_parameter_metadata(executor, bot_id)
for param_name, meta in metadata.items():
    print(f"{param_name}:")
    print(f"  Type: {meta['type']}")
    print(f"  Min: {meta['min']}, Max: {meta['max']}")
    print(f"  Options: {meta['options']}")
```

#### `get_bot_closed_positions(executor, bot_id)`
Get closed positions for a bot:

```python
closed_positions = get_bot_closed_positions(executor, bot_id)
for position in closed_positions:
    print(f"Market: {position['Market']}, PnL: {position['PnL']}")
```

## 🔧 **Parameter Types and Validation**

### **Type 0: Numeric**
- **Validation**: Min/max range checking
- **Conversion**: String → float/int
- **Example**: `"Stop Loss (%)": 10`

### **Type 2: Boolean**
- **Validation**: true/false values
- **Conversion**: "true"/"false" strings → boolean
- **Example**: `"Draw RSI?": true`

### **Type 3: Options/Enum**
- **Validation**: Must be in available options
- **Example**: `"BBands MA Type": "Ema"`

### **Type 10: Group Headers**
- **Validation**: No validation (display only)
- **Example**: `"Settings"`, `"MadHatter BBands"`

## 📊 **Parameter Metadata Structure**

Each parameter contains rich metadata:

```python
{
    "key": "3-3-11-16.Stop Loss (%)",
    "type": 0,
    "min": 0.0,
    "max": 0.0,
    "step": -1,
    "group": "Settings",
    "description": "5",
    "tooltip": "",
    "options": None,
    "current_value": 5,
    "extended_key": "3-3-11-16"
}
```

## 🚀 **Usage Examples**

### **Simple Parameter Edit**
```python
# Edit a single parameter
updated_bot = edit_bot_parameter_by_name(
    executor, bot_id, "Stop Loss (%)", 8
)
```

### **Group-based Editing**
```python
# Edit all RSI parameters
rsi_changes = {
    "RSI Length": 14,
    "RSI Buy Level": 30,
    "RSI Sell Level": 70
}
updated_bot = edit_bot_parameters_by_group(
    executor, bot_id, "MadHatter RSI", rsi_changes
)
```

### **Validation Before Editing**
```python
# Validate changes first
changes = {"Stop Loss (%)": 15, "Take Profit (%)": 20}
validation = validate_bot_parameters(executor, bot_id, changes)

if not validation['invalid']:
    # All changes are valid, apply them
    for param_name, value in changes.items():
        edit_bot_parameter_by_name(executor, bot_id, param_name, value)
else:
    print(f"Invalid changes: {validation['invalid']}")
```

### **Comprehensive Bot Analysis**
```python
# Get complete bot data
bot_data = get_comprehensive_bot(executor, bot_id)

# Analyze parameters by group
groups = get_bot_parameter_groups(executor, bot_id)
for group_name, params in groups.items():
    print(f"\nGroup: {group_name}")
    for param_name in params:
        metadata = get_bot_parameter_metadata(executor, bot_id)[param_name]
        print(f"  {param_name}: {metadata['current_value']} ({metadata['type']})")
```

## 🎯 **Why This Makes Bot Editing a Breeze**

### **1. Human-Readable Names**
- No need to remember cryptic parameter keys
- Use intuitive names like "Stop Loss (%)" instead of "3-3-11-16.Stop Loss (%)"

### **2. Group Organization**
- Edit related parameters together
- Natural organization by indicator groups (RSI, BBands, MACD, etc.)

### **3. Smart Validation**
- Automatic type conversion
- Range and option validation
- Clear error messages for invalid values

### **4. Comprehensive Data**
- All bot information in one place
- Historical data (closed positions, logs)
- Complete parameter metadata

### **5. Multiple Editing Levels**
- Single parameter: Quick tweaks
- Group editing: Related changes
- Whole bot: Major overhauls
- Validation: Safe experimentation

## 🔄 **Integration with Existing API**

These new functions complement the existing API:

- **`edit_bot_parameter()`**: Edit entire bot object
- **`edit_bot_settings()`**: Edit script settings object
- **`get_bot()`**: Get basic bot info
- **`get_bot_runtime()`**: Get runtime data

The new functions provide higher-level abstractions that make common tasks easier while still allowing access to the underlying functionality when needed.

## 📁 **File Structure**

```
pyHaasAPI/
├── api.py                    # Core API functions
├── bot_editing_api.py        # Enhanced bot editing functions
└── ...

examples/
├── comprehensive_bot_editing_demo.py  # Complete demo
└── ...
```

## 🎉 **Conclusion**

The enhanced bot editing API provides multiple levels of control over bot parameters, from simple single-parameter edits to comprehensive group-based changes. With built-in validation, human-readable names, and comprehensive data retrieval, bot parameter editing becomes intuitive and safe.

Whether you're making quick adjustments or comprehensive strategy changes, these functions provide the right level of abstraction for your needs. 