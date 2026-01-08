# Static & Media Files

Django-style static and media file handling.

## Configuration

In settings.py:
```python
class AppSettings(Settings):
    static_url = "/static/"
    static_root = "staticfiles"
    staticfiles_dirs = ["frontend/dist", "assets"]
    
    media_url = "/media/"
    media_root = "media"
```

## Collecting Static Files

```bash
# Collect all static files
p8s collectstatic

# Clear and recollect
p8s collectstatic --clear

# Dry run (show what would be collected)
p8s collectstatic --dry-run
```

## Mounting in App

```python
from p8s.staticfiles import StaticFilesConfig, mount_static_files

config = StaticFilesConfig(
    static_url="/static/",
    static_root="staticfiles",
    media_url="/media/",
    media_root="media",
)

mount_static_files(app, config)
```

## URL Generation

```python
from p8s.staticfiles import get_static_url, get_media_url

# Get static file URL
css_url = get_static_url("css/main.css")
# -> "/static/css/main.css"

# Get media file URL
image_url = get_media_url("uploads/photo.jpg")
# -> "/media/uploads/photo.jpg"
```

## File Uploads

```python
from p8s.storage import FileField, ImageField

class Document(Model, table=True):
    file: str | None = FileField(upload_to="docs/")
    image: str | None = ImageField(upload_to="images/")
```

Files are stored in `media_root` and served from `media_url`.
