"""
Application settings.

Override using environment variables prefixed with P8S_
Example: P8S_DEBUG=true
"""

from p8s.core.settings import Settings

# Extend settings if needed
class AppSettings(Settings):
    installed_apps: list[str] = [
        "backend.apps.products",
    ]
