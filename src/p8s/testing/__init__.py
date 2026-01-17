"""
P8s Testing Module - Test utilities for P8s applications.

Provides:
- TestClient: Django-style test client
- RequestFactory: Mock request creation
- ModelFactory: Test data factories
- Assertion helpers
"""

# Re-export from client module
from p8s.testing.client import (
    RequestFactory,
    TestClient,
    assert_json_contains,
    assert_redirect,
    assert_status_code,
)

# Re-export from factory module
from p8s.testing.factory import (
    Fake,
    FieldGenerator,
    LazyAttribute,
    ModelFactory,
    lazy,
)

__all__ = [
    # Client
    "TestClient",
    "RequestFactory",
    "assert_status_code",
    "assert_json_contains",
    "assert_redirect",
    # Factory
    "ModelFactory",
    "FieldGenerator",
    "Fake",
    "lazy",
    "LazyAttribute",
]
