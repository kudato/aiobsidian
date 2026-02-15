# Error Handling

aiobsidian uses a simple exception hierarchy for API errors.

## Exception hierarchy

```
ObsidianError          # Base exception for all aiobsidian errors
└── APIError           # HTTP error from the REST API
    ├── AuthenticationError  # 401 Unauthorized
    └── NotFoundError        # 404 Not Found
```

## Catching errors

```python
from aiobsidian import (
    ObsidianClient,
    APIError,
    AuthenticationError,
    NotFoundError,
)

async with ObsidianClient(api_key="your-api-key") as client:
    try:
        content = await client.vault.get("nonexistent.md")
    except NotFoundError:
        print("File not found")
    except AuthenticationError:
        print("Invalid API key")
    except APIError as e:
        print(f"API error [{e.status_code}]: {e.message}")
```

## APIError attributes

All API exceptions (`APIError`, `AuthenticationError`, `NotFoundError`) have these attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `status_code` | `int` | HTTP status code (e.g. 401, 404, 500) |
| `message` | `str` | Error message from the API response |
| `error_code` | `int \| None` | Optional numeric error code from the API |

## Example: retry on transient errors

```python
from aiobsidian import APIError

async def get_with_retry(client, path, retries=3):
    for attempt in range(retries):
        try:
            return await client.vault.get(path)
        except APIError as e:
            if e.status_code >= 500 and attempt < retries - 1:
                continue
            raise
```
