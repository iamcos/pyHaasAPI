# Utility for extracting parameter definitions and valid ranges/options from GET_SCRIPT_RECORD
from typing import Any, Dict, List, Optional

def extract_script_parameter_ranges(script_record: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Given a GET_SCRIPT_RECORD response (as dict), extract parameter definitions and valid ranges/options.
    Returns a list of dicts with keys: K (key), N (name), T (type), MIN, MAX, O (options), default, and suggested range.
    """
    params = []
    for param in script_record.get('I', []):
        key = param.get('K')
        name = param.get('N')
        ptype = param.get('T')
        min_val = param.get('MIN')
        max_val = param.get('MAX')
        options = param.get('O')
        default = param.get('V')
        # Only consider numeric params with min/max for range
        suggested_range = None
        if ptype == 0 and min_val is not None and max_val is not None:
            # Choose a sensible step, e.g., 1 or 0.1
            try:
                step = 1 if float(default).is_integer() else 0.1
            except Exception:
                step = 1
            try:
                min_val_f = float(min_val)
                max_val_f = float(max_val)
                values = []
                val = min_val_f
                while val <= max_val_f:
                    values.append(round(val, 2))
                    val += step
                suggested_range = values
            except Exception:
                suggested_range = None
        elif ptype == 3 and options:
            suggested_range = list(options.values()) if isinstance(options, dict) else options
        params.append({
            'K': key,
            'N': name,
            'T': ptype,
            'MIN': min_val,
            'MAX': max_val,
            'O': options,
            'default': default,
            'suggested_range': suggested_range
        })
    return params

def update_lab_parameters_by_key(lab_details: dict, updates: Dict[str, Any]) -> dict:
    """
    Update only selected parameters (by key) in a lab's parameter list, preserving all others.
    - lab_details: dict or LabDetails object (must have 'P' or 'parameters')
    - updates: dict mapping parameter key to new value(s) or a tuple (start, end, step) for ranges
    Returns the updated lab_details dict.
    """
    # Get parameter list
    params = lab_details.get('P', []) if isinstance(lab_details, dict) else getattr(lab_details, 'parameters', [])
    for param in params:
        key = param.get('K')
        if key in updates:
            value = updates[key]
            # If value is a tuple, treat as (start, end, step) for range
            if isinstance(value, tuple) and len(value) == 3:
                start, end, step = value
                if isinstance(start, int) and isinstance(end, int) and isinstance(step, int):
                    param['O'] = list(range(start, end + 1, step))
                else:
                    # For floats
                    vals = []
                    v = start
                    while v <= end:
                        vals.append(round(v, 6))
                        v += step
                    param['O'] = vals
            # If value is list, set all options (for enums, multi-select)
            elif isinstance(value, list):
                param['O'] = value
            # For booleans, allow single or both
            elif isinstance(value, bool):
                param['O'] = [value]
            else:
                param['O'] = [value]
            param['I'] = True
            param['IS'] = True
    # If using dict, update 'P'; if object, update .parameters
    if isinstance(lab_details, dict):
        lab_details['P'] = params
    else:
        lab_details.parameters = params
    return lab_details 