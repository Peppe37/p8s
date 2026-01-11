"""
Tests for P8s testing utilities.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestRequestFactory:
    """Test RequestFactory class."""

    def test_get_request(self):
        """Test creating a GET request."""
        from p8s.testing import RequestFactory

        factory = RequestFactory()
        request = factory.get("/api/users")

        assert request["method"] == "GET"
        assert request["path"] == "/api/users"

    def test_get_request_with_params(self):
        """Test GET request with query params."""
        from p8s.testing import RequestFactory

        factory = RequestFactory()
        request = factory.get("/api/users", params={"page": 1, "limit": 10})

        assert request["query_params"]["page"] == 1
        assert request["query_params"]["limit"] == 10

    def test_post_request(self):
        """Test creating a POST request."""
        from p8s.testing import RequestFactory

        factory = RequestFactory()
        request = factory.post("/api/users", {"name": "Test"})

        assert request["method"] == "POST"
        assert request["path"] == "/api/users"
        assert request["body"]["name"] == "Test"

    def test_put_request(self):
        """Test creating a PUT request."""
        from p8s.testing import RequestFactory

        factory = RequestFactory()
        request = factory.put("/api/users/1", {"name": "Updated"})

        assert request["method"] == "PUT"
        assert request["body"]["name"] == "Updated"

    def test_delete_request(self):
        """Test creating a DELETE request."""
        from p8s.testing import RequestFactory

        factory = RequestFactory()
        request = factory.delete("/api/users/1")

        assert request["method"] == "DELETE"
        assert request["path"] == "/api/users/1"

    def test_factory_with_defaults(self):
        """Test factory with default headers."""
        from p8s.testing import RequestFactory

        factory = RequestFactory(defaults={"headers": {"X-Custom": "value"}})
        request = factory.get("/api/users")

        assert request["headers"]["X-Custom"] == "value"

    def test_factory_header_override(self):
        """Test overriding default headers."""
        from p8s.testing import RequestFactory

        factory = RequestFactory(defaults={"headers": {"X-Custom": "default"}})
        request = factory.get("/api/users", headers={"X-Custom": "override"})

        assert request["headers"]["X-Custom"] == "override"


class TestAssertions:
    """Test assertion helper functions."""

    def test_assert_status_code_success(self):
        """Test assert_status_code with matching status."""
        from p8s.testing import assert_status_code

        response = MagicMock()
        response.status_code = 200

        # Should not raise
        assert_status_code(response, 200)

    def test_assert_status_code_failure(self):
        """Test assert_status_code with non-matching status."""
        from p8s.testing import assert_status_code

        response = MagicMock()
        response.status_code = 404

        with pytest.raises(AssertionError) as exc_info:
            assert_status_code(response, 200)

        assert "expected 200" in str(exc_info.value)
        assert "got 404" in str(exc_info.value)

    def test_assert_json_contains_key_exists(self):
        """Test assert_json_contains with existing key."""
        from p8s.testing import assert_json_contains

        response = MagicMock()
        response.json.return_value = {"name": "test", "id": 1}

        # Should not raise
        assert_json_contains(response, "name")

    def test_assert_json_contains_key_missing(self):
        """Test assert_json_contains with missing key."""
        from p8s.testing import assert_json_contains

        response = MagicMock()
        response.json.return_value = {"id": 1}

        with pytest.raises(AssertionError) as exc_info:
            assert_json_contains(response, "name")

        assert "name" in str(exc_info.value)

    def test_assert_json_contains_value_match(self):
        """Test assert_json_contains with value match."""
        from p8s.testing import assert_json_contains

        response = MagicMock()
        response.json.return_value = {"name": "test"}

        # Should not raise
        assert_json_contains(response, "name", "test")

    def test_assert_json_contains_value_mismatch(self):
        """Test assert_json_contains with value mismatch."""
        from p8s.testing import assert_json_contains

        response = MagicMock()
        response.json.return_value = {"name": "test"}

        with pytest.raises(AssertionError) as exc_info:
            assert_json_contains(response, "name", "other")

        assert "expected other" in str(exc_info.value)

    def test_assert_redirect_success(self):
        """Test assert_redirect with redirect status."""
        from p8s.testing import assert_redirect

        response = MagicMock()
        response.status_code = 302
        response.headers = {"location": "/login"}

        # Should not raise
        assert_redirect(response)

    def test_assert_redirect_not_redirect(self):
        """Test assert_redirect with non-redirect status."""
        from p8s.testing import assert_redirect

        response = MagicMock()
        response.status_code = 200

        with pytest.raises(AssertionError) as exc_info:
            assert_redirect(response)

        assert "Not a redirect" in str(exc_info.value)

    def test_assert_redirect_url_match(self):
        """Test assert_redirect with URL matching."""
        from p8s.testing import assert_redirect

        response = MagicMock()
        response.status_code = 302
        response.headers = {"location": "/admin/login"}

        # Should not raise
        assert_redirect(response, "/admin/login")

    def test_assert_redirect_url_mismatch(self):
        """Test assert_redirect with URL mismatch."""
        from p8s.testing import assert_redirect

        response = MagicMock()
        response.status_code = 302
        response.headers = {"location": "/other"}

        with pytest.raises(AssertionError) as exc_info:
            assert_redirect(response, "/admin")

        assert "URL mismatch" in str(exc_info.value)
