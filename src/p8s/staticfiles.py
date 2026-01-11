"""
P8s Static Files - Django-style static and media file serving.

Provides:
- StaticFiles mounting configuration
- collectstatic command
- Media files URL generation
"""

from pathlib import Path
from typing import Any

from starlette.staticfiles import StaticFiles as StarletteStaticFiles


class StaticFilesConfig:
    """
    Configuration for static files serving.

    Example:
        ```python
        from p8s.staticfiles import StaticFilesConfig

        static = StaticFilesConfig(
            static_url="/static/",
            static_root="collected_static",
            staticfiles_dirs=["frontend/dist", "assets"],
        )
        ```
    """

    def __init__(
        self,
        static_url: str = "/static/",
        static_root: str | Path = "staticfiles",
        staticfiles_dirs: list[str | Path] | None = None,
        media_url: str = "/media/",
        media_root: str | Path = "media",
    ) -> None:
        """
        Initialize static files configuration.

        Args:
            static_url: URL prefix for static files.
            static_root: Directory for collected static files.
            staticfiles_dirs: Additional directories to look for static files.
            media_url: URL prefix for user-uploaded files.
            media_root: Directory for user-uploaded files.
        """
        self.static_url = static_url
        self.static_root = Path(static_root)
        self.staticfiles_dirs = [Path(d) for d in (staticfiles_dirs or [])]
        self.media_url = media_url
        self.media_root = Path(media_root)


def mount_static_files(app: Any, config: StaticFilesConfig | None = None) -> None:
    """
    Mount static and media file serving on a FastAPI app.

    Args:
        app: FastAPI application instance.
        config: Static files configuration (uses defaults if None).
    """
    if config is None:
        config = StaticFilesConfig()

    # Mount collected static files
    if config.static_root.exists():
        app.mount(
            config.static_url,
            StarletteStaticFiles(directory=str(config.static_root)),
            name="static",
        )

    # Mount media files
    config.media_root.mkdir(parents=True, exist_ok=True)
    app.mount(
        config.media_url,
        StarletteStaticFiles(directory=str(config.media_root)),
        name="media",
    )


def collectstatic(
    config: StaticFilesConfig,
    clear: bool = False,
) -> dict[str, Any]:
    """
    Collect static files from various locations into STATIC_ROOT.

    Args:
        config: Static files configuration.
        clear: Clear STATIC_ROOT before collecting.

    Returns:
        Dict with collection stats.
    """
    import shutil

    stats = {"copied": 0, "skipped": 0, "errors": []}

    config.static_root.mkdir(parents=True, exist_ok=True)

    if clear:
        for item in config.static_root.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    for source_dir in config.staticfiles_dirs:
        if not source_dir.exists():
            continue

        for source_file in source_dir.rglob("*"):
            if source_file.is_dir():
                continue

            relative = source_file.relative_to(source_dir)
            dest_file = config.static_root / relative

            try:
                dest_file.parent.mkdir(parents=True, exist_ok=True)

                # Check if file needs updating
                if dest_file.exists():
                    if source_file.stat().st_mtime <= dest_file.stat().st_mtime:
                        stats["skipped"] += 1
                        continue

                shutil.copy2(source_file, dest_file)
                stats["copied"] += 1
            except Exception as e:
                stats["errors"].append(f"{source_file}: {e}")

    return stats


def get_static_url(path: str, config: StaticFilesConfig | None = None) -> str:
    """
    Generate URL for a static file.

    Args:
        path: Relative path to static file.
        config: Static files configuration.

    Returns:
        Full URL to the static file.
    """
    if config is None:
        config = StaticFilesConfig()

    url = config.static_url
    if not url.endswith("/"):
        url += "/"
    return f"{url}{path.lstrip('/')}"


def get_media_url(path: str, config: StaticFilesConfig | None = None) -> str:
    """
    Generate URL for a media file.

    Args:
        path: Relative path to media file.
        config: Static files configuration.

    Returns:
        Full URL to the media file.
    """
    if config is None:
        config = StaticFilesConfig()

    url = config.media_url
    if not url.endswith("/"):
        url += "/"
    return f"{url}{path.lstrip('/')}"
