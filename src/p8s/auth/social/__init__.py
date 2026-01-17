"""
P8s OAuth2 / Social Login - Native social authentication.

Provides OAuth2 providers for:
- Google
- GitHub
- Microsoft

Example:
    ```python
    from p8s.auth.social import GoogleProvider, oauth_router

    # Configure provider
    google = GoogleProvider(
        client_id="your-client-id",
        client_secret="your-client-secret",
    )

    # Add routes
    app.include_router(oauth_router)
    ```
"""

from p8s.auth.social.models import SocialAccount
from p8s.auth.social.providers import (
    GitHubProvider,
    GoogleProvider,
    MicrosoftProvider,
    OAuth2Provider,
    get_provider,
    register_provider,
)
from p8s.auth.social.router import router as oauth_router

__all__ = [
    # Providers
    "OAuth2Provider",
    "GoogleProvider",
    "GitHubProvider",
    "MicrosoftProvider",
    "get_provider",
    "register_provider",
    # Models
    "SocialAccount",
    # Router
    "oauth_router",
]
