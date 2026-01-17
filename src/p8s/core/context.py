"""
P8s Context - Utility for standalone script initialization.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from p8s.core.settings import Settings, get_settings
from p8s.db.session import close_db, init_db

logger = logging.getLogger("p8s.core.context")


@asynccontextmanager
async def setup_context(settings: Settings | None = None) -> AsyncGenerator[None, None]:
    """
    Context manager to initialize the P8s environment for standalone scripts.

    Ensures settings are loaded and database connections are managed.

    Usage:
        import asyncio
        from p8s.core.context import setup_context
        from p8s.db.session import SessionManager

        async def main():
            async with setup_context():
                async with SessionManager() as session:
                    # Use your models here
                    pass

        if __name__ == "__main__":
            asyncio.run(main())
    """
    if settings is None:
        settings = get_settings()

    # Configure minimal logging if not configured
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level="DEBUG" if settings.debug else "INFO",
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    logger.info("Initializing P8s Context...")
    logger.info(f"Using Database: {settings.database.url}")

    # Initialize Database
    await init_db(settings.database)

    try:
        yield
    finally:
        logger.info("Closing P8s Context...")
        await close_db()
