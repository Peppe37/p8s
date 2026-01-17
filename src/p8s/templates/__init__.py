"""
P8s Template Engine - Jinja2 integration for server-side rendering.

Provides Django-style template rendering with:
- Template loading from directories
- Context processors
- Fast Jinja2 rendering
- HTML response helpers

Example:
    ```python
    from p8s.templates import render_template, configure

    # Configure template directory
    configure(template_dir="templates/")

    # In a route
    @app.get("/products/")
    async def products(request: Request):
        products = await get_products()
        return render_template(
            "products.html",
            request=request,
            products=products,
        )
    ```
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.responses import HTMLResponse

# Template configuration
_template_dir: Path | None = None
_jinja_env = None
_context_processors: list[Callable[[Request], dict[str, Any]]] = []


def configure(
    template_dir: str | Path,
    auto_reload: bool = True,
    extensions: list[str] | None = None,
) -> None:
    """
    Configure the template engine.

    Args:
        template_dir: Path to template directory
        auto_reload: Auto-reload templates on change (dev mode)
        extensions: Jinja2 extensions to enable

    Example:
        ```python
        from p8s.templates import configure

        configure("templates/", auto_reload=True)
        ```
    """
    global _template_dir, _jinja_env

    try:
        from jinja2 import Environment, FileSystemLoader
    except ImportError:
        raise ImportError("Jinja2 is required. Install with: pip install Jinja2")

    _template_dir = Path(template_dir)

    loader = FileSystemLoader(str(_template_dir))
    _jinja_env = Environment(
        loader=loader,
        auto_reload=auto_reload,
        extensions=extensions or [],
        autoescape=True,
    )


def get_environment():
    """
    Get the Jinja2 environment.

    Returns:
        Configured Jinja2 Environment

    Raises:
        RuntimeError: If not configured
    """
    if _jinja_env is None:
        raise RuntimeError("Template engine not configured. Call configure() first.")
    return _jinja_env


def add_context_processor(processor: Callable[[Request], dict[str, Any]]) -> None:
    """
    Add a context processor to be called for every template.

    Context processors receive the request and return a dict
    of variables to add to the template context.

    Args:
        processor: Function taking Request and returning dict

    Example:
        ```python
        from p8s.templates import add_context_processor

        def user_context(request):
            return {"user": request.state.user}

        add_context_processor(user_context)
        ```
    """
    _context_processors.append(processor)


def get_template(name: str):
    """
    Get a template by name.

    Args:
        name: Template filename relative to template_dir

    Returns:
        Jinja2 Template object

    Raises:
        TemplateNotFound: If template doesn't exist
    """
    env = get_environment()
    return env.get_template(name)


def render_template(
    template_name: str,
    request: Request | None = None,
    **context: Any,
) -> HTMLResponse:
    """
    Render a template to an HTML response.

    Args:
        template_name: Template filename
        request: Optional request for context processors
        **context: Template variables

    Returns:
        HTMLResponse with rendered content

    Example:
        ```python
        return render_template(
            "products.html",
            request=request,
            products=products,
            title="Our Products",
        )
        ```
    """
    # Add request to context
    if request:
        context["request"] = request

        # Run context processors
        for processor in _context_processors:
            try:
                extra = processor(request)
                context.update(extra)
            except Exception:
                pass

    template = get_template(template_name)
    content = template.render(**context)

    return HTMLResponse(content=content)


def render_string(
    template_string: str,
    **context: Any,
) -> str:
    """
    Render a template string.

    Args:
        template_string: Jinja2 template as string
        **context: Template variables

    Returns:
        Rendered string

    Example:
        ```python
        html = render_string(
            "<h1>Hello {{ name }}</h1>",
            name="World",
        )
        ```
    """
    env = get_environment()
    template = env.from_string(template_string)
    return template.render(**context)


# Built-in context processors
def static_url_processor(request: Request) -> dict[str, Any]:
    """Add static URL helper to context."""

    def static(path: str) -> str:
        return f"/static/{path}"

    return {"static": static}


def url_for_processor(request: Request) -> dict[str, Any]:
    """Add url_for helper to context."""

    def url_for(name: str, **kwargs: Any) -> str:
        return request.app.url_path_for(name, **kwargs)

    return {"url_for": url_for}


__all__ = [
    "configure",
    "get_environment",
    "get_template",
    "render_template",
    "render_string",
    "add_context_processor",
    "static_url_processor",
    "url_for_processor",
]
