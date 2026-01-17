"""
P8s Admin Registry - Model registration for admin panel.
"""

from typing import Any, TypeVar

from sqlmodel import SQLModel

# Global registry of models for admin
_registered_models: dict[str, type[SQLModel]] = {}

ModelType = TypeVar("ModelType", bound=SQLModel)


def pluralize(word: str) -> str:
    """
    Intelligently pluralize a word following English rules.

    Examples:
        Category -> Categories
        Package -> Packages
        Status -> Statuses
        Entity -> Entities
        User -> Users
    """
    if not word:
        return word

    # Common irregular plurals
    irregulars = {
        "person": "people",
        "child": "children",
        "man": "men",
        "woman": "women",
        "foot": "feet",
        "tooth": "teeth",
        "goose": "geese",
        "mouse": "mice",
        "ox": "oxen",
        "datum": "data",
        "medium": "media",
        "analysis": "analyses",
        "basis": "bases",
        "crisis": "crises",
        "thesis": "theses",
    }

    lower = word.lower()
    if lower in irregulars:
        # Preserve original capitalization
        if word[0].isupper():
            return irregulars[lower].capitalize()
        return irregulars[lower]

    # Words ending in consonant + y -> ies
    if len(word) > 1 and word[-1] in "yY" and word[-2].lower() not in "aeiou":
        return word[:-1] + ("ies" if word[-1] == "y" else "Ies")

    # Words ending in s, x, z, ch, sh -> es
    if word.endswith(("s", "x", "z", "S", "X", "Z")):
        return word + "es"
    if word.endswith(("ch", "sh", "Ch", "Sh", "CH", "SH")):
        return word + "es"

    # Words ending in o preceded by consonant -> es (with exceptions)
    o_exceptions = {"photo", "piano", "halo", "auto", "memo", "video", "solo"}
    if word.endswith(("o", "O")) and len(word) > 1:
        if lower not in o_exceptions and word[-2].lower() not in "aeiou":
            return word + "es"

    # Words ending in f or fe -> ves
    f_exceptions = {"roof", "proof", "chief", "chef", "cliff", "belief"}
    if word.endswith(("f", "F")) and lower not in f_exceptions:
        return word[:-1] + ("ves" if word[-1] == "f" else "Ves")
    if word.endswith(("fe", "Fe", "fE", "FE")):
        return word[:-2] + "ves"

    # Default: add s
    return word + "s"


def register_model(model: type[ModelType]) -> type[ModelType]:
    """
    Register a model for the admin panel.

    Can be used as a decorator:

    ```python
    from p8s.admin import register_model

    @register_model
    class Product(Model, table=True):
        name: str
        price: float
    ```

    Args:
        model: The SQLModel class to register.

    Returns:
        The same model class (for decorator use).
    """
    model_name = model.__name__
    _registered_models[model_name] = model
    return model


def get_registered_models() -> dict[str, type[SQLModel]]:
    """
    Get all registered models.

    Returns:
        Dictionary of model name -> model class.
    """
    return _registered_models.copy()


def get_model(name: str) -> type[SQLModel] | None:
    """
    Get a registered model by name.

    Args:
        name: Model class name.

    Returns:
        The model class or None.
    """
    return _registered_models.get(name)


def _get_app_label(model: type[SQLModel]) -> str:
    """
    Get the app label for a model.

    Tries to infer from module name:
    - backend.apps.blog.models -> Blog
    - p8s.auth.models -> Auth
    - other.module -> Other
    """
    module = model.__module__
    parts = module.split(".")

    # Check for backend.apps.X
    if "apps" in parts:
        try:
            apps_index = parts.index("apps")
            if apps_index + 1 < len(parts):
                return parts[apps_index + 1].title()
        except ValueError:
            pass

    # Check for p8s.X
    if parts[0] == "p8s" and len(parts) > 1:
        # Special case for core/auth
        if parts[1] == "auth":
            return "Authentication"
        return parts[1].title()

    # Fallback to module name if it's simple
    if len(parts) > 1:
        # exclude .models if present
        if parts[-1] == "models":
            return parts[-2].title()

    return "Core"


def get_model_metadata(model: type[SQLModel]) -> dict[str, Any]:
    """
    Extract metadata from a model for the admin panel.

    Args:
        model: The model class.

    Returns:
        Metadata dictionary.
    """
    # Get field information
    fields = {}

    # Import PydanticUndefined for comparison
    from pydantic_core import PydanticUndefined

    for field_name, field_info in model.model_fields.items():
        # Handle default value - avoid PydanticUndefined serialization
        default_value = field_info.default
        if default_value is PydanticUndefined:
            default_value = None
        elif not isinstance(
            default_value, str | int | float | bool | list | dict | type(None)
        ):
            default_value = str(default_value) if default_value is not None else None

        # Normalize type for frontend
        type_str = "string"
        annotation = field_info.annotation
        type_name = str(annotation)

        # Check for specific pydantic types via string name to avoid imports if possible
        if "EmailStr" in type_name:
            type_str = "email"
        elif "AnyUrl" in type_name:
            type_str = "url"
        elif annotation in (int, float) or "int" in type_name or "float" in type_name:
            type_str = "number"
            if "Decimal" in type_name:
                type_str = "number"  # Decimal treated as number in frontend
        elif annotation is bool or "bool" in type_name:
            type_str = "boolean"
        elif "datetime" in type_name:
            type_str = "datetime"
        elif "date" in type_name:
            type_str = "date"
        elif annotation in (dict, list) or "dict" in type_name or "list" in type_name:
            type_str = "json"

        field_data = {
            "name": field_name,
            "type": type_str,
            "required": field_info.is_required(),
            "default": default_value,
            "description": field_info.description,
            "label": field_info.title,  # Extracted from verbose_name
        }

        # Check for AI field metadata
        if field_info.json_schema_extra:
            extra = field_info.json_schema_extra
            if isinstance(extra, dict):
                if extra.get("x-p8s-ai-field"):
                    field_data["ai_field"] = True
                    field_data["ai_prompt"] = extra.get("x-p8s-ai-prompt")
                if extra.get("x-p8s-vector-field"):
                    field_data["vector_field"] = True

        fields[field_name] = field_data

    # Get Relationships (SQLAlchemy inspection)
    from sqlalchemy.inspection import inspect
    from sqlalchemy.orm import RelationshipDirection

    try:
        mapper = inspect(model)
        for rel in mapper.relationships:
            target_class = rel.mapper.class_
            target_name = target_class.__name__

            relation_type = "relation"
            rtype = "unknown"

            if rel.direction == RelationshipDirection.MANYTOONE:
                rtype = "many-to-one"  # Foreign Key
            elif rel.direction == RelationshipDirection.MANYTOMANY:
                rtype = "many-to-many"
            elif rel.direction == RelationshipDirection.ONETOMANY:
                rtype = "one-to-many"

            local_field = None
            if rtype == "many-to-one" and rel.local_columns:
                # Try to get the local field name from the column
                # This assumes simple single-column FK
                try:
                    col = list(rel.local_columns)[0]
                    local_field = col.key
                except Exception:
                    pass

            # Only add if relevant (M2O or M2M usually)
            if rtype in ["many-to-one", "many-to-many"]:
                fields[rel.key] = {
                    "name": rel.key,
                    "type": "relation",
                    "required": False,
                    "default": None,
                    "description": f"Relation to {target_name}",
                    "relation": {
                        "model": target_name,
                        "type": rtype,
                        "field": "id",
                        "local_field": local_field,
                    },
                }
    except Exception as e:
        # Fallback if introspection fails
        import logging

        logging.error(f"Introspection failed for {model}: {e}")
        pass

    # Get admin config
    admin_config = {
        "name": model.__name__,
        "plural_name": pluralize(model.__name__),
        "list_display": [],
        "search_fields": [],
        "list_filter": [],
        "ordering": [],
        "readonly_fields": [],
        "hidden_fields": [],
        "inlines": [],  # Support for inline editing
    }

    if hasattr(model, "Admin"):
        # Allow overriding name/plural_name
        if hasattr(model.Admin, "name"):
            admin_config["name"] = model.Admin.name
        if hasattr(model.Admin, "plural_name"):
            admin_config["plural_name"] = model.Admin.plural_name

        # Map direct attributes
        for attr in [
            "list_display",
            "search_fields",
            "list_filter",
            "ordering",
            "readonly_fields",
            "inlines",  # Generic mapping
        ]:
            if hasattr(model.Admin, attr):
                admin_config[attr] = getattr(model.Admin, attr)

        # Map exclude -> hidden_fields
        if hasattr(model.Admin, "exclude"):
            admin_config["hidden_fields"] = model.Admin.exclude
        elif hasattr(model.Admin, "hidden_fields"):
            admin_config["hidden_fields"] = model.Admin.hidden_fields

    # Get registered actions with metadata
    from p8s.admin.actions import DEFAULT_ACTIONS, get_model_actions

    actions_list = []
    model_actions = get_model_actions(model.__name__)

    # Add default actions
    for action_name, func in DEFAULT_ACTIONS.items():
        actions_list.append(
            {
                "name": action_name,
                "description": getattr(func, "_action_description", action_name),
                "confirm": getattr(func, "_action_confirm", False),
            }
        )

    # Add model-specific actions
    for action_name, action_meta in model_actions.items():
        actions_list.append(
            {
                "name": action_name,
                "description": action_meta.get("description", action_name),
                "confirm": action_meta.get("confirm", False),
            }
        )

    # Get inline configurations
    from p8s.admin.inlines import get_model_inlines

    inlines = get_model_inlines(model)

    return {
        "name": model.__name__,
        "app_label": _get_app_label(model),
        "table_name": getattr(model, "__tablename__", model.__name__.lower()),
        "fields": fields,
        "admin": admin_config,
        "actions": actions_list,
        "inlines": inlines,
    }


def auto_discover_models() -> None:
    """
    Auto-discover models from installed apps.

    Imports all models.py files from registered apps
    and registers models that inherit from Model.

    Also imports admin.py to allow site.register() calls.
    """
    import importlib

    from p8s.core.settings import get_settings

    settings = get_settings()

    for app_name in settings.installed_apps:
        # 1. Import models.py (OPTIONAL - now relies on admin.py for registration)
        # We don't auto-register models anymore to allow "opt-in" via admin.py
        # But we still import models to ensure SQLModel knows about them (e.g. for migrations)
        try:
            importlib.import_module(f"{app_name}.models")
        except ImportError as e:
            # Log error if it's not just a missing models module
            # If e.name is the module we tried to import, it's missing -> fine.
            # If e.name is something else, it's a dependency failure -> bad.
            if (
                e.name
                and e.name != f"{app_name}.models"
                and not f"{app_name}.models".endswith(e.name)
            ):
                import logging

                logging.error(f"Failed to import {app_name}.models: {e}")
        except Exception as e:
            import logging

            logging.error(f"Failed to import {app_name}.models: {e}")

        # 2. Import admin.py
        try:
            importlib.import_module(f"{app_name}.admin")
        except ImportError:
            pass
        except Exception as e:
            import logging

            logging.error(f"Failed to import {app_name}.admin: {e}")
