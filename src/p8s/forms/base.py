"""
P8s Forms Base - Form and ModelForm base classes.

Provides:
- Form: Base class for custom forms
- ModelForm: Auto-generated form from SQLModel
"""

from typing import Any

from pydantic import BaseModel, ValidationError


class FormErrors:
    """Container for form validation errors."""

    def __init__(self):
        self._errors: dict[str, list[str]] = {}

    def add(self, field: str, message: str) -> None:
        """Add an error for a field."""
        if field not in self._errors:
            self._errors[field] = []
        self._errors[field].append(message)

    def get(self, field: str) -> list[str]:
        """Get errors for a field."""
        return self._errors.get(field, [])

    def all(self) -> dict[str, list[str]]:
        """Get all errors."""
        return self._errors.copy()

    def __bool__(self) -> bool:
        """True if there are errors."""
        return bool(self._errors)

    def __iter__(self):
        """Iterate over field names with errors."""
        return iter(self._errors)


class Form(BaseModel):
    """
    Base class for P8s forms.

    Provides Pydantic validation with Django-style API.

    Example:
        class ContactForm(Form):
            name: str
            email: str
            message: str

        # Validate data
        form = ContactForm.from_data(request.form)
        if form.is_valid():
            send_email(form.data)
        else:
            print(form.errors.all())
    """

    model_config = {"extra": "ignore", "arbitrary_types_allowed": True}

    @classmethod
    def from_data(cls, data: dict[str, Any]) -> "Form":
        """
        Create a form instance from raw data.

        The form will be validated and errors will be populated.

        Args:
            data: Form data (e.g., from request.form)

        Returns:
            Form instance (check is_valid() for validation result)
        """
        try:
            instance = cls(**data)
            # Store validation state using object.__setattr__ to bypass Pydantic
            object.__setattr__(instance, "_form_is_valid", True)
            object.__setattr__(instance, "_form_errors", FormErrors())
            object.__setattr__(instance, "_form_raw_data", data)
            return instance
        except ValidationError as e:
            # Create empty instance for error handling
            # Use construct to bypass validation
            try:
                instance = cls.model_construct()
            except Exception:
                # Fallback: create with minimal data
                instance = object.__new__(cls)

            # Store validation state
            object.__setattr__(instance, "_form_is_valid", False)
            errors = FormErrors()

            # Populate errors from Pydantic validation
            for error in e.errors():
                field = error.get("loc", ("__all__",))[0]
                msg = error.get("msg", "Invalid value")
                errors.add(str(field), msg)

            object.__setattr__(instance, "_form_errors", errors)
            object.__setattr__(instance, "_form_raw_data", data)

            return instance

    def is_valid(self) -> bool:
        """Check if form data is valid."""
        return getattr(self, "_form_is_valid", True)

    @property
    def errors(self) -> FormErrors:
        """Get validation errors."""
        if not hasattr(self, "_form_errors"):
            object.__setattr__(self, "_form_errors", FormErrors())
        return self._form_errors

    @property
    def data(self) -> dict[str, Any]:
        """Get cleaned/validated form data as dict."""
        if self.is_valid():
            return self.model_dump()
        return getattr(self, "_form_raw_data", {})

    @classmethod
    def get_fields(cls) -> dict[str, dict[str, Any]]:
        """
        Get field information for rendering.

        Returns:
            Dictionary of field_name -> field metadata
        """
        fields = {}

        for field_name, field_info in cls.model_fields.items():
            # Get type annotation
            annotation = cls.__annotations__.get(field_name, str)

            # Determine input type from annotation and field_info
            input_type = "text"
            if annotation == int:
                input_type = "number"
            elif annotation == float:
                input_type = "number"
            elif annotation == bool:
                input_type = "checkbox"
            elif "email" in field_name.lower():
                input_type = "email"
            elif "password" in field_name.lower():
                input_type = "password"

            # Check for custom field_info
            extra = field_info.json_schema_extra or {}
            custom_info = extra.get("field_info", {})
            if hasattr(custom_info, "input_type"):
                input_type = custom_info.input_type

            fields[field_name] = {
                "name": field_name,
                "label": field_name.replace("_", " ").title(),
                "type": input_type,
                "required": field_info.is_required(),
                "default": field_info.default if field_info.default is not None else "",
                "annotation": str(annotation),
            }

            # Add custom field info if present
            if hasattr(custom_info, "__dict__"):
                for k, v in custom_info.__dict__.items():
                    if v is not None and not k.startswith("_"):
                        fields[field_name][k] = v

        return fields


class ModelForm(Form):
    """
    Auto-generated form from a P8s Model.

    Example:
        class ProductForm(ModelForm):
            class Meta:
                model = Product
                fields = ["name", "price", "description"]
                exclude = ["id", "created_at"]

        form = ProductForm.from_data(request.form)
        if form.is_valid():
            product = Product(**form.data)
            session.add(product)
    """

    class Meta:
        model: type[Any] = None
        fields: list[str] | str = "__all__"
        exclude: list[str] = []

    def __init_subclass__(cls, **kwargs):
        """Dynamically add fields from the model."""
        super().__init_subclass__(**kwargs)

        meta = getattr(cls, "Meta", None)
        if meta is None:
            return

        model = getattr(meta, "model", None)
        if model is None:
            return

        fields_config = getattr(meta, "fields", "__all__")
        exclude_fields = getattr(meta, "exclude", [])

        # Always exclude these by default
        default_exclude = ["id", "created_at", "updated_at", "deleted_at"]
        exclude_fields = list(set(exclude_fields + default_exclude))

        # Get model fields
        if hasattr(model, "model_fields"):
            model_fields = model.model_fields
        else:
            return

        # Determine which fields to include
        if fields_config == "__all__":
            include_fields = [f for f in model_fields.keys() if f not in exclude_fields]
        else:
            include_fields = [f for f in fields_config if f not in exclude_fields]

        # Copy annotations from model to form
        if not hasattr(cls, "__annotations__"):
            cls.__annotations__ = {}

        for field_name in include_fields:
            if field_name in model_fields:
                field_info = model_fields[field_name]

                # Get annotation from model
                if (
                    hasattr(model, "__annotations__")
                    and field_name in model.__annotations__
                ):
                    annotation = model.__annotations__[field_name]
                    cls.__annotations__[field_name] = annotation

    @classmethod
    def from_instance(cls, instance: Any) -> "ModelForm":
        """
        Create a form pre-populated from a model instance.

        Args:
            instance: Model instance

        Returns:
            Form with data from instance
        """
        data = {}

        meta = getattr(cls, "Meta", None)
        if meta and hasattr(meta, "model"):
            model = meta.model
            if hasattr(model, "model_fields"):
                for field_name in model.model_fields.keys():
                    if hasattr(instance, field_name):
                        data[field_name] = getattr(instance, field_name)

        return cls.from_data(data)

    def save(self, session: Any = None, commit: bool = True) -> Any:
        """
        Save the form data to a new model instance.

        Args:
            session: Database session (optional)
            commit: Whether to commit the session

        Returns:
            Created model instance
        """
        if not self.is_valid():
            raise ValueError("Cannot save invalid form")

        meta = getattr(self, "Meta", None)
        if meta is None or not hasattr(meta, "model"):
            raise ValueError("ModelForm must define Meta.model")

        model = meta.model
        instance = model(**self.data)

        if session is not None:
            session.add(instance)
            if commit:
                session.commit()
                session.refresh(instance)

        return instance
