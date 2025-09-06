# Script Management Guide for pyHaasAPI

## Quick Start

```python
from pyHaasAPI import api

# Get all scripts
scripts = api.get_all_scripts(executor)

# Get script by ID
script = api.get_script_item(executor, script_id)

# Get script record with parameters
script_record = api.get_script_record(executor, script_id)
```

## Script Operations

### Listing Scripts
```python
# Get all scripts
scripts = api.get_all_scripts(executor)

for script in scripts:
    print(f"Script: {script.script_name}")
    print(f"  ID: {script.script_id}")
    print(f"  Type: {script.script_type}")
    print(f"  Status: {script.script_status}")
```

### Finding Scripts by Name
```python
# Search scripts by name pattern
scripts = api.get_scripts_by_name(
    executor, 
    name_pattern="Scalper",
    case_sensitive=False
)
```

### Getting Script Parameters
```python
# Get script with parameter definitions
script_record = api.get_script_record(executor, script_id)

for param in script_record.parameters:
    print(f"Parameter: {param.title}")
    print(f"  Type: {param.type}")
    print(f"  Default: {param.default}")
    print(f"  Min: {param.min}")
    print(f"  Max: {param.max}")
```

## Script Management

### Creating Scripts
```python
# Add new script
script = api.add_script(
    executor,
    script_name="My Script",
    script_content="-- Your Lua script here --",
    description="My custom trading script",
    script_type=0  # 0 = trading script
)
```

### Editing Scripts
```python
# Edit existing script
updated_script = api.edit_script(
    executor,
    script_id=script_id,
    script_name="Updated Name",
    script_content="-- Updated script content --",
    description="Updated description"
)
```

### Deleting Scripts
```python
# Delete script
success = api.delete_script(executor, script_id)
```

### Publishing Scripts
```python
# Publish script
success = api.publish_script(executor, script_id)
```

## Script Folders

### Managing Folders
```python
# Get all folders
folders = api.get_all_script_folders(executor)

# Create folder
folder = api.create_script_folder(executor, "My Folder")

# Move script to folder
success = api.move_script_to_folder(executor, script_id, folder_id)
```

## Best Practices

1. Always validate script parameters before using
2. Use descriptive script names
3. Test scripts in labs before deploying to bots
4. Keep script content organized and documented 