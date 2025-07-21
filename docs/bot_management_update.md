# Bot Management Documentation

**Last updated: July 2024**

## Overview

This document describes how to manage trading bots using the pyHaasAPI client. All major bot management workflows are covered by robust, tested example scripts. See [examples/bot_lifecycle_example.py](../examples/bot_lifecycle_example.py) and [examples/README.md](../examples/README.md) for real-world usage.

---

## Bot Lifecycle

- Create bot: `add_bot(executor, CreateBotRequest)`
- Activate bot: `activate_bot(executor, bot_id, cleanreports=False)`
- Pause bot: `pause_bot(executor, bot_id)`
- Resume bot: `resume_bot(executor, bot_id)`
- Deactivate bot: `deactivate_bot(executor, bot_id, cancelorders=False)`
- Delete bot: `delete_bot(executor, bot_id)`
- Get bot details: `get_bot(executor, bot_id)`

See [Bot Lifecycle Example](../examples/bot_lifecycle_example.py) for a full workflow.

---

## Best Practices

- Always check bot status (`is_activated`, `is_paused`) before taking actions
- Handle all API errors with try/except and print actionable messages
- Use robust parameter validation (see example script)
- Automate bot management for CI/CD or production with environment-based configuration

---

## Error Handling

- All bot management functions raise `HaasApiError` on failure
- Example scripts demonstrate robust error handling for all major workflows

---

## Notes
- All examples and API functions are up to date as of July 2024
- For full details, see the code and docstrings in `pyHaasAPI/api.py` and the example scripts 