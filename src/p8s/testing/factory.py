"""
P8s Testing Factory - Factory Boy style test data generation.

Provides easy model factories for testing:
- Automatic field generation
- Relationship handling
- Faker integration

Example:
    ```python
    from p8s.testing.factory import ModelFactory

    class ProductFactory(ModelFactory):
        class Meta:
            model = Product

        name = "Test Product"
        price = 9.99

    # Usage
    product = await ProductFactory.create()
    products = await ProductFactory.create_batch(10)
    ```
"""

import random
import string
from datetime import datetime, timedelta
from typing import Any, TypeVar
from uuid import uuid4

T = TypeVar("T")


class FieldGenerator:
    """Generates random field values."""

    @staticmethod
    def string(length: int = 10, prefix: str = "") -> str:
        """Generate random string."""
        chars = string.ascii_letters + string.digits
        random_str = "".join(random.choices(chars, k=length))
        return f"{prefix}{random_str}"

    @staticmethod
    def email() -> str:
        """Generate random email."""
        username = FieldGenerator.string(8).lower()
        domains = ["example.com", "test.com", "mail.org"]
        return f"{username}@{random.choice(domains)}"

    @staticmethod
    def integer(min_val: int = 0, max_val: int = 1000) -> int:
        """Generate random integer."""
        return random.randint(min_val, max_val)

    @staticmethod
    def float_(min_val: float = 0, max_val: float = 1000) -> float:
        """Generate random float."""
        return round(random.uniform(min_val, max_val), 2)

    @staticmethod
    def boolean() -> bool:
        """Generate random boolean."""
        return random.choice([True, False])

    @staticmethod
    def date(days_ago: int = 365) -> datetime:
        """Generate random date within past N days."""
        return datetime.now() - timedelta(days=random.randint(0, days_ago))

    @staticmethod
    def uuid() -> str:
        """Generate UUID string."""
        return str(uuid4())

    @staticmethod
    def choice(options: list) -> Any:
        """Random choice from list."""
        return random.choice(options)

    @staticmethod
    def name() -> str:
        """Generate fake name."""
        first_names = ["John", "Jane", "Bob", "Alice", "Charlie", "Diana"]
        last_names = ["Smith", "Jones", "Brown", "Wilson", "Taylor", "Davis"]
        return f"{random.choice(first_names)} {random.choice(last_names)}"

    @staticmethod
    def phone() -> str:
        """Generate fake phone number."""
        return f"+1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}"


class ModelFactoryMeta(type):
    """Metaclass for ModelFactory."""

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)

        # Extract field definitions
        fields = {}
        for key, value in namespace.items():
            if not key.startswith("_") and key != "Meta":
                if not callable(value) or isinstance(value, LazyAttribute):
                    fields[key] = value

        cls._factory_fields = fields
        return cls


class LazyAttribute:
    """Lazy attribute that calls function to generate value."""

    def __init__(self, func):
        self.func = func

    def evaluate(self, instance: dict) -> Any:
        """Evaluate the lazy attribute."""
        return self.func(instance)


def lazy(func):
    """Decorator to create a lazy attribute."""
    return LazyAttribute(func)


class ModelFactory(metaclass=ModelFactoryMeta):
    """
    Base class for test factories.

    Example:
        ```python
        class UserFactory(ModelFactory):
            class Meta:
                model = User

            name = lazy(lambda _: FieldGenerator.name())
            email = lazy(lambda _: FieldGenerator.email())
            is_active = True

        # Create one
        user = await UserFactory.create(session)

        # Create many
        users = await UserFactory.create_batch(session, 10)

        # Build without saving
        user_data = UserFactory.build()
        ```
    """

    class Meta:
        model = None

    _factory_fields: dict = {}

    @classmethod
    def get_model(cls) -> type:
        """Get the model class."""
        return getattr(cls.Meta, "model", None)

    @classmethod
    def build(cls, **overrides) -> dict:
        """
        Build model data without saving.

        Args:
            **overrides: Field overrides

        Returns:
            Dict of field values
        """
        data = {}

        for key, value in cls._factory_fields.items():
            if isinstance(value, LazyAttribute):
                data[key] = value.evaluate(data)
            else:
                data[key] = value

        data.update(overrides)
        return data

    @classmethod
    async def create(cls, session, **overrides) -> T:
        """
        Create and save a model instance.

        Args:
            session: Database session
            **overrides: Field overrides

        Returns:
            Created model instance
        """
        model = cls.get_model()
        if model is None:
            raise ValueError(f"No model defined in {cls.__name__}.Meta")

        data = cls.build(**overrides)
        instance = model(**data)

        session.add(instance)
        await session.flush()
        await session.refresh(instance)

        return instance

    @classmethod
    async def create_batch(cls, session, count: int, **overrides) -> list[T]:
        """
        Create multiple model instances.

        Args:
            session: Database session
            count: Number of instances to create
            **overrides: Field overrides (applied to all)

        Returns:
            List of created instances
        """
        return [await cls.create(session, **overrides) for _ in range(count)]


# Convenience aliases
Fake = FieldGenerator


__all__ = [
    "ModelFactory",
    "FieldGenerator",
    "Fake",
    "lazy",
    "LazyAttribute",
]
