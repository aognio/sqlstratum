# Hydration

Hydration is the post-execution step that maps row data into application-level structures. By
default, SQLStratum hydrates to dictionaries.

## Dict Hydration
```python
q = (
    SELECT(users.c.id, users.c.email)
    .FROM(users)
    .WHERE(users.c.id == 1)
    .hydrate(dict)
)
row = runner.fetch_one(q)
```

## Dataclass Hydration
```python
from dataclasses import dataclass

@dataclass
class User:
    id: int
    email: str

q = SELECT(users.c.id, users.c.email).FROM(users).WHERE(users.c.id == 1).hydrate(User)
row = runner.fetch_one(q)
```

## Optional Pydantic Hydration
SQLStratum does not depend on Pydantic, but it provides an optional adapter for Pydantic v2 models.

Install:
```bash
pip install sqlstratum[pydantic]
```

Use the adapter directly:
```python
from pydantic import BaseModel
from sqlstratum.hydrate.pydantic import hydrate_model

class User(BaseModel):
    id: int
    email: str

row = {"id": "1", "email": "a@b.com"}
user = hydrate_model(User, row)
```

Or use the wrapper pattern with chainable hydration:
```python
from pydantic import BaseModel
from sqlstratum.hydrate.pydantic import using_pydantic

class User(BaseModel):
    id: int
    email: str

q = using_pydantic(
    SELECT(users.c.id, users.c.email).FROM(users).WHERE(users.c.id == 1)
).hydrate(User)
row = runner.fetch_one(q)
```
