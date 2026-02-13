# Debugging

SQLStratum can log executed SQL statements (compiled SQL + parameters + duration), but logging is
intentionally gated to avoid noisy output in production. Debug output requires two conditions:
- Environment variable gate: `SQLSTRATUM_DEBUG` must be truthy (`"1"`, `"true"`, `"yes"`,
  case-insensitive).
- Logger gate: the `sqlstratum` logger must be DEBUG-enabled.

Python logging defaults to WARNING level, so even if `SQLSTRATUM_DEBUG=1` is set, DEBUG logs will not
appear unless logging is configured.

## Enable in a development app
Step 1 - set the environment variable:
```bash
SQLSTRATUM_DEBUG=1
```

Step 2 - configure logging early in the app:
```python
import logging

logging.basicConfig(level=logging.DEBUG)
# or
logging.getLogger("sqlstratum").setLevel(logging.DEBUG)
```

Output looks like:
```
SQL: <compiled sql> | params={<sorted params>} | duration_ms=<...>
```

Architectural intent: logging happens at the Runner boundary (after execution). AST building and
compilation remain deterministic and side-effect free, preserving separation of concerns.
