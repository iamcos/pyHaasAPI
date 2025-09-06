# HaasScript Editing Workflow

This document clarifies the intended usage of API functions for managing HaasScripts, particularly distinguishing between creating new scripts and updating existing ones.

## 1. Creating a New Script ("Save As")

To create a brand new HaasScript on the server, use the `add_script` function (which corresponds to the `/add_script` API endpoint). This is analogous to a "Save As" operation in a traditional editor, where you are creating a new file.

**Function:** `api.add_script(executor, script_name, script_content, description, script_type)`
**API Endpoint:** `POST /add_script`

## 2. Updating an Existing Script ("Save to Same File")

To modify and save changes to an existing HaasScript, use the `edit_script` function. This is analogous to a "Save" operation.

Internally, when `script_content` is provided to `edit_script`, it now utilizes the `EDIT_SCRIPT_SOURCECODE` channel on the HaasOnline server. This channel is specifically designed for updating the script's source code and associated settings. If only metadata like `script_name` or `description` are changed, the standard `EDIT_SCRIPT` channel is used.

**Function:** `api.edit_script(executor, script_id, script_name=None, script_content=None, description="", settings=None)`
**API Endpoint (internal for content changes):** `POST /edit_script_sourcecode`

### Key Distinction:

*   `add_script`: Generates a **new** `script_id`.
*   `edit_script`: Requires an **existing** `script_id` to modify its content or metadata.

This clear separation ensures that we can accurately manage scripts on the HaasOnline server, reflecting the user's intent whether they are creating something new or modifying an existing asset.
