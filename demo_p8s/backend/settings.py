"""
Application settings for demo_p8s.

Override using environment variables prefixed with P8S_
Example: P8S_DEBUG=true
"""

from p8s.core.settings import Settings


class AppSettings(Settings):
    """
    Extended settings for the demo application.

    All P8s settings are inherited. Add custom settings here.
    """

    # Custom app settings
    app_name: str = "P8s Demo"

    # Enable debug by default for demo
    debug: bool = True

    # Demo-specific
    demo_mode: bool = True
