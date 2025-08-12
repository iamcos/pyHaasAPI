# Authentication

## ⚠️ SECURITY WARNING ⚠️
**DO NOT EXPOSE PRIVATE DATA IN SCRIPTS! USE .env FILE!!!**

- **NEVER** hardcode API keys, passwords, emails, or any sensitive credentials in your scripts
- **ALWAYS** use environment variables loaded from a `.env` file
- **NEVER** commit credentials to version control

## Best Practices

- Use `RequestsExecutor.authenticate()` for all scripts and workflows.
- Store credentials in `.env` and load via `config/settings.py`.
- For multi-account or CI/CD, use environment variables or secrets management.
- All example scripts and workflows in `examples/` use this pattern.

## Example

```python
from config import settings
from pyHaasAPI import api

executor = api.RequestsExecutor(
    host=settings.API_HOST,
    port=settings.API_PORT,
    state=api.Guest()
).authenticate(
    email=settings.API_EMAIL,
    password=settings.API_PASSWORD
)
```

- See [docs/lab_workflows.md](./lab_workflows.md) for authentication in context of lab and bot workflows. 