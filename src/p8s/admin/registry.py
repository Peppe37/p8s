"""
P8s Admin Registry - Model registration for admin panel.
"""

from typing import Any, TypeVar
from sqlmodel import SQLModel

# Global registry of models for admin
_registered_models: dict[str, type[SQLModel]] = {}

ModelType = TypeVar("ModelType", bound=SQLModel)


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


def get_model_metadata(model: type[SQLModel]) -> dict[str, Any]:
    """
    Extract metadata from a model for the admin panel.
    
    Args:
        model: The model class.
    
    Returns:
        Metadata dictionary.
    """
    # Get field information
    fields = []
    
    for field_name, field_info in model.model_fields.items():
        field_data = {
            "name": field_name,
            "type": str(field_info.annotation),
            "required": field_info.is_required(),
            "default": field_info.default if field_info.default is not None else None,
            "description": field_info.description,
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
        
        fields.append(field_data)
    
    # Get admin config
    admin_config = {}
    if hasattr(model, "Admin"):
        for attr in ["list_display", "search_fields", "list_filter", 
                     "ordering", "readonly_fields", "exclude"]:
            if hasattr(model.Admin, attr):
                admin_config[attr] = getattr(model.Admin, attr)
    
    return {
        "name": model.__name__,
        "table_name": getattr(model, "__tablename__", model.__name__.lower()),
        "fields": fields,
        "admin": admin_config,
    }


def auto_discover_models() -> None:
    """
    Auto-discover models from installed apps.
    
    Imports all models.py files from registered apps
    and registers models that inherit from Model.
    """
    from p8s.core.settings import get_settings
    import importlib
    
    settings = get_settings()
    
    for app_name in settings.installed_apps:
        try:
            module = importlib.import_module(f"{app_name}.models")
            
            # Find all Model subclasses
            for name in dir(module):
                obj = getattr(module, name)
                if (
                    isinstance(obj, type)
                    and issubclass(obj, SQLModel)
                    and obj is not SQLModel
                    and hasattr(obj, "__tablename__")
                ):
                    register_model(obj)
        except ImportError:
            pass
