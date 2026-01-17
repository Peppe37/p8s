# Testing

P8s provides Django-style testing utilities for FastAPI applications.

## Overview

```python
from p8s.testing import TestClient, RequestFactory
from p8s.testing import assert_status_code, assert_json_contains, assert_redirect
```

## TestClient

Wrapper around Starlette's TestClient:

```python
from p8s.testing import TestClient
from backend.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

---

## RequestFactory

Create mock requests for unit testing:

```python
from p8s.testing import RequestFactory

factory = RequestFactory()

# GET request
request = factory.get("/products", params={"page": 1})

# POST request with JSON
request = factory.post("/products", json={"name": "Widget"})

# With authentication
request = factory.get("/api/me", headers={"Authorization": "Bearer token123"})

# Custom defaults
factory = RequestFactory(headers={"X-API-Key": "secret"})
```

### Factory Methods

| Method                           | Description           |
| -------------------------------- | --------------------- |
| `factory.get(path, **kwargs)`    | Create GET request    |
| `factory.post(path, **kwargs)`   | Create POST request   |
| `factory.put(path, **kwargs)`    | Create PUT request    |
| `factory.patch(path, **kwargs)`  | Create PATCH request  |
| `factory.delete(path, **kwargs)` | Create DELETE request |

---

## Assertions

### assert_status_code

```python
from p8s.testing import assert_status_code

response = client.get("/products")
assert_status_code(response, 200)
# Raises AssertionError with helpful message if status doesn't match
```

### assert_json_contains

```python
from p8s.testing import assert_json_contains

response = client.get("/products/1")
assert_json_contains(response, "name")  # Check key exists
assert_json_contains(response, "name", "Widget")  # Check value
```

### assert_redirect

```python
from p8s.testing import assert_redirect

response = client.get("/old-url", follow_redirects=False)
assert_redirect(response, "/new-url")
```

---

## Example Test File

```python
# tests/test_products.py
import pytest
from p8s.testing import TestClient, assert_status_code, assert_json_contains
from backend.main import app

@pytest.fixture
def client():
    return TestClient(app)

class TestProductAPI:
    def test_list_products(self, client):
        response = client.get("/api/products")
        assert_status_code(response, 200)
        assert isinstance(response.json(), list)

    def test_create_product(self, client):
        response = client.post("/api/products", json={
            "name": "Test Product",
            "price": 9.99,
        })
        assert_status_code(response, 201)
        assert_json_contains(response, "id")
        assert_json_contains(response, "name", "Test Product")

    def test_get_product_not_found(self, client):
        response = client.get("/api/products/nonexistent-id")
        assert_status_code(response, 404)
```

---

## Running Tests

```bash
# Run all tests
pytest tests/

# Verbose output
pytest tests/ -v

# Specific file
pytest tests/test_products.py

# With coverage
pytest tests/ --cov=backend
```

---

## Async Tests

For async test functions:

```bash
pip install pytest-asyncio
```

```python
import pytest

@pytest.mark.asyncio
async def test_async_operation():
    result = await some_async_function()
    assert result == expected
```

---

## Database Testing

For tests that need a clean database:

```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlmodel import SQLModel

@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    await engine.dispose()

async def test_create_user(db_session):
    from backend.apps.users.models import User

    user = User(email="test@example.com", password_hash="...")
    db_session.add(user)
    await db_session.commit()

    assert user.id is not None
```
