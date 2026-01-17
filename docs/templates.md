# Template Engine

P8s provides Jinja2 integration for server-side rendering.

## Quick Start

```python
from p8s.templates import configure, render_template

# Configure once at startup
configure(template_dir="templates/")

# In a route
@app.get("/products/")
async def products(request: Request):
    return render_template(
        "products.html",
        request=request,
        products=products,
    )
```

## Configuration

```python
from p8s.templates import configure

configure(
    template_dir="templates/",
    auto_reload=True,  # Reload on change (dev)
    extensions=["jinja2.ext.i18n"],  # Optional extensions
)
```

## Rendering Templates

### From File

```python
from p8s.templates import render_template

return render_template(
    "products.html",
    request=request,
    products=products,
    title="Our Products",
)
```

### From String

```python
from p8s.templates import render_string

html = render_string(
    "<h1>Hello {{ name }}</h1>",
    name="World",
)
```

## Context Processors

Add global variables to all templates:

```python
from p8s.templates import add_context_processor

def user_context(request):
    return {"current_user": request.state.user}

add_context_processor(user_context)
```

### Built-in Processors

```python
from p8s.templates import static_url_processor, url_for_processor

add_context_processor(static_url_processor)
add_context_processor(url_for_processor)
```

## Template Directory Structure

```
templates/
├── base.html
├── products/
│   ├── list.html
│   └── detail.html
└── partials/
    └── header.html
```

## In Templates

```html
{% extends "base.html" %}

{% block content %}
<h1>{{ title }}</h1>

{% for product in products %}
    <div class="product">
        <h2>{{ product.name }}</h2>
        <p>{{ product.price | format_currency }}</p>
    </div>
{% endfor %}

<img src="{{ static('images/logo.png') }}" alt="Logo">
{% endblock %}
```
