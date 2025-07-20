# Lab Cloning Discovery and Best Practices

## Overview
This document outlines the important discoveries made while working with HaasOnline lab cloning and configuration management.

## Key Discovery: Use CLONE_LAB Instead of Create + Update

### The Problem
Initially, we attempted to create new labs and then update their parameters to match an existing lab. This approach was unreliable and often resulted in 404 errors or incomplete parameter copying.

### The Solution
**Use the `CLONE_LAB` API channel instead of creating new labs and updating parameters.**

### Why CLONE_LAB is Better
1. **Preserves All Settings**: Cloning automatically copies all lab settings, parameters, and configurations
2. **More Reliable**: Fewer API calls means fewer points of failure
3. **Consistent Results**: Cloned labs are exact copies of the original
4. **Better Performance**: Single API call vs multiple create/update calls

## Config Parameter Mapping Fix

### The Issue
The `LabConfig` model had incorrect field names that didn't match the actual API parameters:

**❌ Incorrect (Previous):**
```python
class LabConfig(BaseModel):
    max_positions: int = Field(alias="MP")      # Wrong!
    max_generations: int = Field(alias="MG")    # Wrong!
    max_evaluations: int = Field(alias="ME")    # Wrong!
    min_roi: float = Field(alias="MR")          # Wrong!
    acceptable_risk: float = Field(alias="AR")  # Wrong!
```

**✅ Correct (Fixed):**
```python
class LabConfig(BaseModel):
    max_population: int = Field(alias="MP")     # Correct!
    max_generations: int = Field(alias="MG")    # Correct!
    max_elites: int = Field(alias="ME")         # Correct!
    mix_rate: float = Field(alias="MR")         # Correct!
    adjust_rate: float = Field(alias="AR")      # Correct!
```

### Parameter Meanings
- **MP** = Max Population (not Max Positions)
- **MG** = Max Generations  
- **ME** = Max Elites (not Max Evaluations)
- **MR** = Mix Rate (not Min ROI)
- **AR** = Adjust Rate (not Acceptable Risk)

### Example Config
```json
{
  "MP": 10,    // Max Population: 10
  "MG": 100,   // Max Generations: 100
  "ME": 3,     // Max Elites: 3
  "MR": 40.0,  // Mix Rate: 40.0
  "AR": 25.0   // Adjust Rate: 25.0
}
```

## API Serialization Fix

### The Problem
When updating lab details, the config was being serialized with full field names instead of the required aliases.

### The Solution
Use `model_dump_json(by_alias=True)` to serialize with the correct field aliases:

```python
# ❌ Incorrect (Previous):
"config": lab_details.config.model_dump_json()

# ✅ Correct (Fixed):
"config": lab_details.config.model_dump_json(by_alias=True)
```

This ensures the config is sent as:
```json
{"MP":10,"MG":100,"ME":3,"MR":40.0,"AR":25.0}
```

Instead of:
```json
{"max_population":10,"max_generations":100,"max_elites":3,"mix_rate":40.0,"adjust_rate":25.0}
```

## Best Practices for Lab Cloning

### 1. Clone Existing Labs
```python
# ✅ Good: Clone an existing lab
cloned_lab = api.clone_lab(executor, source_lab_id, new_lab_name)

# ❌ Avoid: Create new lab and update parameters
new_lab = api.create_lab(executor, lab_details)
updated_lab = api.update_lab_details(executor, new_lab)
```

### 2. Update Market and Account After Cloning
```python
# Get the cloned lab details
lab_details = api.get_lab_details(executor, cloned_lab.lab_id)

# Update market tag and account ID
lab_details.settings.market_tag = "BINANCE_BTC_USDT_"
lab_details.settings.account_id = account.account_id

# Update the lab
updated_lab = api.update_lab_details(executor, lab_details)
```

### 3. Ensure Correct Config Parameters
```python
# Create config with correct field names
config = LabConfig(
    max_population=10,    # Max Population
    max_generations=100,  # Max Generations
    max_elites=3,         # Max Elites
    mix_rate=40.0,        # Mix Rate
    adjust_rate=25.0      # Adjust Rate
)

# Apply to lab
lab_details.config = config
updated_lab = api.update_lab_details(executor, lab_details)
```

## API Call Patterns

### UPDATE_LAB_DETAILS
- **Method**: GET
- **Parameters**: `labid`, `name`, `type`, `config`, `settings`, `parameters`
- **Config Format**: JSON string with field aliases (MP, MG, ME, MR, AR)

### CLONE_LAB
- **Method**: GET
- **Parameters**: `labid`, `name`
- **Result**: Creates exact copy of source lab

### START_LAB_EXECUTION
- **Method**: POST (with form-encoded data)
- **Parameters**: `labid`, `startunix`, `endunix`, `sendemail`

## Troubleshooting

### 404 Errors on UPDATE_LAB_DETAILS
1. Ensure `labid` parameter name (not `labId`)
2. Use `by_alias=True` for config serialization
3. Use GET method (not POST)

### Config Parameters Not Applied
1. Check field names in `LabConfig` model
2. Ensure `by_alias=True` in serialization
3. Verify parameter values are correct

### Backtest Start Failures
- Ensure lab is in CREATED status
- Check parameter format for START_LAB_EXECUTION
- Verify lab has valid market tag and account ID

## Files Modified

### Core API Changes
- `pyHaasAPI/parameters.py`: Fixed `LabConfig` field names
- `pyHaasAPI/api.py`: Fixed config serialization in `update_lab_details`

### Example Scripts
- `examples/fixed_clone_example_lab.py`: Working example with correct config
- `examples/simple_clone_example_lab.py`: Simplified cloning script

## Results

After implementing these fixes:
- ✅ All 15 labs cloned successfully with correct config parameters
- ✅ Config parameters properly applied: MP=10, MG=100, ME=3, MR=40.0, AR=25.0
- ✅ No more 404 errors on lab updates
- ✅ Consistent and reliable lab cloning process

## Future Improvements

1. **Backtest Execution**: Resolve 404 errors on START_LAB_EXECUTION
2. **Error Handling**: Add better error handling for API failures
3. **Validation**: Add validation for config parameter ranges
4. **Monitoring**: Add progress tracking for bulk operations 