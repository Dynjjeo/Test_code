# Logger for Parrot

This package is a thin [structlog](https://www.structlog.org/en/stable/) wrapper to set and provide defaults for logging.

## Usage

### Python Logging

1. Configure `logger` at app initialization

    ```python
    from logger import setup_logger

    setup_logger(json_logs=False)
    ```

2. Start logging with `logger`

    ```python
    from logger import get_logger

    log = get_logger(__name__) # create module level logger

    log.info("user.logged_in")
    ```

### FastAPI Logging

Add middleware:

```python
from starlette.middleware.base import BaseHTTPMiddleware
from logger import setup_logger, logging_middleware

setup_logger(json_logs=False)

app.add_middleware(BaseHTTPMiddleware, dispatch=logging_middleware)
```
