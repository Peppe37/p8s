# Class-Based Views

P8s provides Django-style generic views for common CRUD patterns.

## Quick Start

```python
from p8s.views import ListView, DetailView, CreateView

class ProductListView(ListView):
    model = Product
    paginate_by = 20

class ProductDetailView(DetailView):
    model = Product

class ProductCreateView(CreateView):
    model = Product
    fields = ["name", "price", "category_id"]
```

## Available Views

| View         | Purpose                      |
| ------------ | ---------------------------- |
| `ListView`   | Display list with pagination |
| `DetailView` | Display single object        |
| `CreateView` | Create new object            |
| `UpdateView` | Update existing object       |
| `DeleteView` | Delete object                |

## ListView

```python
class ProductListView(ListView):
    model = Product
    paginate_by = 25  # Items per page
    ordering = "-created_at"  # Default ordering
```

Returns:
```json
{
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 25,
    "pages": 4
}
```

## DetailView

```python
class ProductDetailView(DetailView):
    model = Product
    pk_field = "id"  # Primary key field
```

## CreateView

```python
class ProductCreateView(CreateView):
    model = Product
    fields = ["name", "price"]  # Allowed fields
```

## UpdateView

```python
class ProductUpdateView(UpdateView):
    model = Product
    fields = ["name", "price"]  # Fields that can be updated
```

Supports both PUT and PATCH methods.

## DeleteView

```python
class ProductDeleteView(DeleteView):
    model = Product
    soft_delete = True  # Use soft delete if available
```

## Converting to Routes

Use `as_route` to integrate with FastAPI:

```python
from p8s.views import ListView, as_route

class ProductListView(ListView):
    model = Product

app.get("/products/")(as_route(ProductListView))
```
