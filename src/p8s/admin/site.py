from sqlmodel import SQLModel

from p8s.admin.registry import register_model


class ModelAdmin:
    """
    Base class for ModelAdmin configuration.
    """

    list_display: list[str] = []
    search_fields: list[str] = []
    list_filter: list[str] = []
    ordering: list[str] = []
    readonly_fields: list[str] = []
    exclude: list[str] = []
    actions: list[str] = []


class AdminSite:
    """
    Admin site registry.
    """

    def register(
        self, model: type[SQLModel], admin_class: type[ModelAdmin] | None = None
    ) -> None:
        """
        Register a model with the admin site.
        """
        # Register model in global registry
        register_model(model)

        # If admin_class is provided, attach it to the model as 'Admin' attribute
        # This preserves compatibility with the existing inner-class approach
        if admin_class:
            model.Admin = admin_class

        # Register actions if defined in Admin class (either inner or passed)
        if hasattr(model, "Admin") and hasattr(model.Admin, "actions"):
            from p8s.admin.actions import register_action

            for action_func in model.Admin.actions:
                # If it's a string, it might be a reference to a method (not fully supported yet unless bound)
                # For now we expect callable functions decorated with @admin_action or simple async funcs
                if callable(action_func):
                    action_name = action_func.__name__
                    register_action(model.__name__, action_name, action_func)


# Global site instance
site = AdminSite()
