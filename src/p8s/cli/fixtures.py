"""
P8s Fixtures - Data import/export for development and testing.

Provides Django-style fixture commands:
- dumpdata: Export models to JSON
- loaddata: Import JSON fixtures

Example:
    ```bash
    # Export
    p8s dumpdata products > fixtures/products.json
    p8s dumpdata --all > fixtures/all_data.json

    # Import
    p8s loaddata fixtures/products.json
    ```
"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Sequence
from uuid import UUID


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for SQLModel objects."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        if isinstance(obj, UUID):
            return str(obj)
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        return super().default(obj)


def serialize_model(obj: Any) -> dict[str, Any]:
    """
    Serialize a model object to dict.

    Args:
        obj: SQLModel instance

    Returns:
        Dict representation
    """
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    elif hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    return {}


async def dump_model(
    session,
    model_class: type,
    indent: int = 2,
) -> str:
    """
    Dump all instances of a model to JSON.

    Args:
        session: Database session
        model_class: Model class to dump
        indent: JSON indentation

    Returns:
        JSON string
    """
    from sqlalchemy import select

    query = select(model_class)
    result = await session.execute(query)
    items = result.scalars().all()

    data = {
        "model": model_class.__name__,
        "count": len(items),
        "items": [serialize_model(item) for item in items],
    }

    return json.dumps(data, cls=JSONEncoder, indent=indent)


async def dump_all_models(
    session,
    models: list[type],
    indent: int = 2,
) -> str:
    """
    Dump all models to JSON.

    Args:
        session: Database session
        models: List of model classes
        indent: JSON indentation

    Returns:
        JSON string with all models
    """
    from sqlalchemy import select

    all_data = []

    for model_class in models:
        query = select(model_class)
        result = await session.execute(query)
        items = result.scalars().all()

        all_data.append({
            "model": model_class.__name__,
            "count": len(items),
            "items": [serialize_model(item) for item in items],
        })

    return json.dumps(all_data, cls=JSONEncoder, indent=indent)


def parse_fixture(content: str) -> list[dict[str, Any]]:
    """
    Parse a fixture file.

    Args:
        content: JSON string

    Returns:
        List of fixture data
    """
    data = json.loads(content)

    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return [data]
    return []


async def load_fixture(
    session,
    fixture_path: str | Path,
    models: dict[str, type],
) -> dict[str, int]:
    """
    Load a fixture file into the database.

    Args:
        session: Database session
        fixture_path: Path to fixture file
        models: Dict mapping model names to classes

    Returns:
        Dict of {model_name: count_loaded}
    """
    path = Path(fixture_path)
    content = path.read_text()
    fixtures = parse_fixture(content)

    counts = {}

    for fixture in fixtures:
        model_name = fixture.get("model")
        items = fixture.get("items", [])

        if model_name not in models:
            continue

        model_class = models[model_name]

        for item_data in items:
            # Convert string UUIDs back
            for key, value in item_data.items():
                if isinstance(value, str) and len(value) == 36 and "-" in value:
                    try:
                        item_data[key] = UUID(value)
                    except ValueError:
                        pass

            obj = model_class(**item_data)
            session.add(obj)

        counts[model_name] = len(items)

    await session.flush()
    return counts


def write_fixture(
    data: str,
    output_path: str | Path,
) -> None:
    """
    Write fixture data to file.

    Args:
        data: JSON string
        output_path: Output file path
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data)


__all__ = [
    "dump_model",
    "dump_all_models",
    "load_fixture",
    "parse_fixture",
    "serialize_model",
    "write_fixture",
    "JSONEncoder",
]
