"""
P8s Test Client - Django-style test client for testing FastAPI applications.

Provides:
- TestClient wrapper with convenience methods
- RequestFactory for creating mock requests
- Response assertions
"""

from typing import Any

from fastapi.testclient import TestClient as FastAPITestClient


class TestClient:
    """
    Django-style test client for FastAPI.

    Example:
        ```python
        from p8s.testing import TestClient
        from backend.main import app

        client = TestClient(app)

        # Simple requests
        response = client.get("/api/products")
        assert response.status_code == 200

        # POST with JSON
        response = client.post("/api/products", {"name": "Test"})
        assert response.json()["name"] == "Test"

        # Authenticated requests
        client.login(email="admin@example.com", password="password")
        response = client.get("/api/admin/stats")
        assert response.status_code == 200
        ```
    """

    def __init__(self, app: Any) -> None:
        """
        Initialize test client.

        Args:
            app: FastAPI application instance.
        """
        self._client = FastAPITestClient(app)
        self._token: str | None = None

    def _headers(self, extra: dict | None = None) -> dict:
        """Build headers with auth token if logged in."""
        headers = {}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        if extra:
            headers.update(extra)
        return headers

    def get(self, path: str, **kwargs: Any) -> Any:
        """
        Make a GET request.

        Args:
            path: URL path.
            **kwargs: Additional arguments to pass to request.

        Returns:
            Response object.
        """
        headers = self._headers(kwargs.pop("headers", None))
        return self._client.get(path, headers=headers, **kwargs)

    def post(
        self,
        path: str,
        data: dict | None = None,
        json_data: dict | None = None,
        **kwargs: Any,
    ) -> Any:
        """
        Make a POST request.

        Args:
            path: URL path.
            data: Form data or JSON data (auto-detected).
            json_data: Explicit JSON data.
            **kwargs: Additional arguments.

        Returns:
            Response object.
        """
        headers = self._headers(kwargs.pop("headers", None))

        if json_data is not None:
            return self._client.post(path, json=json_data, headers=headers, **kwargs)
        elif data is not None:
            return self._client.post(path, json=data, headers=headers, **kwargs)
        else:
            return self._client.post(path, headers=headers, **kwargs)

    def put(self, path: str, data: dict | None = None, **kwargs: Any) -> Any:
        """Make a PUT request."""
        headers = self._headers(kwargs.pop("headers", None))
        return self._client.put(path, json=data, headers=headers, **kwargs)

    def patch(self, path: str, data: dict | None = None, **kwargs: Any) -> Any:
        """Make a PATCH request."""
        headers = self._headers(kwargs.pop("headers", None))
        return self._client.patch(path, json=data, headers=headers, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> Any:
        """Make a DELETE request."""
        headers = self._headers(kwargs.pop("headers", None))
        return self._client.delete(path, headers=headers, **kwargs)

    def login(
        self,
        email: str,
        password: str,
        login_url: str = "/api/auth/login",
    ) -> bool:
        """
        Log in a user.

        Args:
            email: User email.
            password: User password.
            login_url: Login endpoint URL.

        Returns:
            True if login successful, False otherwise.
        """
        response = self._client.post(
            login_url,
            json={"email": email, "password": password},
        )

        if response.status_code == 200:
            data = response.json()
            self._token = data.get("access_token") or data.get("token")
            return True
        return False

    def force_login(self, user: Any) -> None:
        """
        Force login as a user (for testing).

        Uses the user's ID to generate a token.

        Args:
            user: User model instance.
        """
        from p8s.auth.security import create_access_token

        self._token = create_access_token(str(user.id))

    def logout(self) -> None:
        """Log out the current user."""
        self._token = None

    @property
    def is_authenticated(self) -> bool:
        """Check if client has auth token."""
        return self._token is not None


class RequestFactory:
    """
    Factory for creating mock requests.

    Example:
        ```python
        from p8s.testing import RequestFactory

        factory = RequestFactory()
        request = factory.get("/api/users")
        request = factory.post("/api/users", {"name": "Test"})
        ```
    """

    def __init__(self, defaults: dict | None = None) -> None:
        """Initialize factory with default values."""
        self.defaults = defaults or {}

    def get(self, path: str, **kwargs: Any) -> dict:
        """Create a mock GET request."""
        return {
            "method": "GET",
            "path": path,
            "query_params": kwargs.get("params", {}),
            "headers": {
                **self.defaults.get("headers", {}),
                **kwargs.get("headers", {}),
            },
        }

    def post(self, path: str, data: dict | None = None, **kwargs: Any) -> dict:
        """Create a mock POST request."""
        return {
            "method": "POST",
            "path": path,
            "body": data,
            "headers": {
                **self.defaults.get("headers", {}),
                **kwargs.get("headers", {}),
            },
        }

    def put(self, path: str, data: dict | None = None, **kwargs: Any) -> dict:
        """Create a mock PUT request."""
        return {
            "method": "PUT",
            "path": path,
            "body": data,
            "headers": {
                **self.defaults.get("headers", {}),
                **kwargs.get("headers", {}),
            },
        }

    def delete(self, path: str, **kwargs: Any) -> dict:
        """Create a mock DELETE request."""
        return {
            "method": "DELETE",
            "path": path,
            "headers": {
                **self.defaults.get("headers", {}),
                **kwargs.get("headers", {}),
            },
        }


# Assertion helpers


def assert_status_code(response: Any, expected: int, msg: str = "") -> None:
    """Assert response has expected status code."""
    actual = response.status_code
    if actual != expected:
        raise AssertionError(
            f"{msg or 'Status code mismatch'}: expected {expected}, got {actual}"
        )


def assert_json_contains(
    response: Any, key: str, value: Any = None, msg: str = ""
) -> None:
    """Assert response JSON contains key (and optionally value)."""
    data = response.json()
    if key not in data:
        raise AssertionError(f"{msg or 'Key not found'}: {key}")
    if value is not None and data[key] != value:
        raise AssertionError(
            f"{msg or 'Value mismatch'}: expected {value}, got {data[key]}"
        )


def assert_redirect(
    response: Any, expected_url: str | None = None, msg: str = ""
) -> None:
    """Assert response is a redirect."""
    if response.status_code not in (301, 302, 303, 307, 308):
        raise AssertionError(
            f"{msg or 'Not a redirect'}: status {response.status_code}"
        )
    if expected_url:
        location = response.headers.get("location", "")
        if expected_url not in location:
            raise AssertionError(
                f"{msg or 'Redirect URL mismatch'}: expected {expected_url}, got {location}"
            )
