# Permissions & Groups

P8s provides a Django-style permissions system for granular access control.

## Models

```python
from p8s.auth.permissions import Permission, Group
```

### Permission

```python
perm = Permission(
    codename="add_product",
    name="Can add product",
    content_type="products.product",
)
```

### Group

```python
editors = Group(name="Editors")
editors.permissions = [edit_perm, view_perm]
```

## Checking Permissions

### On User Model

```python
# Role-based (sync)
if user.has_perm("products.add_product"):
    ...

# Granular with DB query (async)
if await user.has_perm_async("products.add_product", session):
    ...

# Check multiple
if user.has_perms(["products.add", "products.change"]):
    ...
```

### With Dependencies

```python
from p8s.auth import require_perm, require_perms

@app.post("/products")
async def create(user: User = require_perm("products.add_product")):
    ...

@app.post("/publish")
async def publish(user: User = require_perms("articles.add", "articles.publish")):
    ...
```

## Creating Permissions

```python
from p8s.auth.permissions import create_model_permissions

# Auto-create add, change, delete, view permissions
perms = await create_model_permissions(Product, session, "products")
```

## Link Tables

The system uses these tables for many-to-many relationships:

- `p8s_user_permissions` - User ↔ Permission
- `p8s_user_groups` - User ↔ Group
- `p8s_group_permissions` - Group ↔ Permission
