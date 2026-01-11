"""
P8s Signals - Django-style signals for model lifecycle events.

Provides a way to run custom code when models are saved, deleted, etc.
without modifying the model code directly.

Example:
    ```python
    from p8s.db.signals import Signal, receiver
    from products.models import Product

    @receiver(Signal.POST_SAVE, sender=Product)
    def on_product_created(sender, instance, created, **kwargs):
        if created:
            print(f"New product: {instance.name}")
    ```
"""

import logging
from collections import defaultdict
from collections.abc import Callable
from enum import Enum
from typing import Any, TypeVar

logger = logging.getLogger("p8s.signals")

T = TypeVar("T")


class Signal(Enum):
    """Available signals for model lifecycle events."""

    # Save signals
    PRE_SAVE = "pre_save"
    POST_SAVE = "post_save"

    # Delete signals
    PRE_DELETE = "pre_delete"
    POST_DELETE = "post_delete"

    # Init signals
    POST_INIT = "post_init"

    # M2M signals (for future use)
    M2M_CHANGED = "m2m_changed"


# Signal handler registry
# Format: {Signal: {sender_class: [handlers]}}
_signal_handlers: dict[Signal, dict[type | None, list[Callable]]] = defaultdict(
    lambda: defaultdict(list)
)


class SignalDispatcher:
    """
    Dispatcher for managing and sending signals.

    This is the core engine that connects signals to handlers and
    dispatches events when signals are sent.
    """

    @staticmethod
    def connect(
        signal: Signal,
        receiver: Callable,
        sender: type | None = None,
        dispatch_uid: str | None = None,
    ) -> None:
        """
        Connect a receiver function to a signal.

        Args:
            signal: The signal to connect to.
            receiver: The function to call when signal is sent.
            sender: Optional model class to filter signals.
            dispatch_uid: Optional unique identifier to prevent duplicates.

        Example:
            ```python
            def my_handler(sender, instance, **kwargs):
                print(f"Saved: {instance}")

            SignalDispatcher.connect(Signal.POST_SAVE, my_handler, sender=Product)
            ```
        """
        handlers = _signal_handlers[signal][sender]

        # Check for duplicates using dispatch_uid
        if dispatch_uid:
            for h in handlers:
                if getattr(h, "_dispatch_uid", None) == dispatch_uid:
                    logger.debug(f"Signal handler already connected: {dispatch_uid}")
                    return
            receiver._dispatch_uid = dispatch_uid

        handlers.append(receiver)
        logger.debug(f"Connected {receiver.__name__} to {signal.value} for {sender}")

    @staticmethod
    def disconnect(
        signal: Signal,
        receiver: Callable,
        sender: type | None = None,
    ) -> bool:
        """
        Disconnect a receiver from a signal.

        Args:
            signal: The signal to disconnect from.
            receiver: The function to remove.
            sender: The sender class used when connecting.

        Returns:
            True if handler was removed, False if not found.
        """
        handlers = _signal_handlers[signal][sender]

        try:
            handlers.remove(receiver)
            logger.debug(f"Disconnected {receiver.__name__} from {signal.value}")
            return True
        except ValueError:
            return False

    @staticmethod
    def send(
        signal: Signal,
        sender: type,
        **kwargs: Any,
    ) -> list[tuple[Callable, Any]]:
        """
        Send a signal to all connected receivers.

        Args:
            signal: The signal to send.
            sender: The class sending the signal.
            **kwargs: Additional arguments to pass to receivers.

        Returns:
            List of (receiver, response) tuples.

        Example:
            ```python
            SignalDispatcher.send(
                Signal.POST_SAVE,
                sender=Product,
                instance=product,
                created=True,
            )
            ```
        """
        responses = []

        # Get handlers for this specific sender
        handlers = _signal_handlers[signal][sender].copy()

        # Also get handlers registered for all senders (sender=None)
        handlers.extend(_signal_handlers[signal][None].copy())

        for handler in handlers:
            try:
                response = handler(sender=sender, **kwargs)
                responses.append((handler, response))
            except Exception as e:
                logger.error(
                    f"Error in signal handler {handler.__name__}: {e}",
                    exc_info=True,
                )
                responses.append((handler, e))

        return responses

    @staticmethod
    async def send_async(
        signal: Signal,
        sender: type,
        **kwargs: Any,
    ) -> list[tuple[Callable, Any]]:
        """
        Send a signal to all connected receivers (async version).

        Awaits async handlers, calls sync handlers normally.

        Args:
            signal: The signal to send.
            sender: The class sending the signal.
            **kwargs: Additional arguments to pass to receivers.

        Returns:
            List of (receiver, response) tuples.
        """
        import asyncio

        responses = []

        handlers = _signal_handlers[signal][sender].copy()
        handlers.extend(_signal_handlers[signal][None].copy())

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    response = await handler(sender=sender, **kwargs)
                else:
                    response = handler(sender=sender, **kwargs)
                responses.append((handler, response))
            except Exception as e:
                logger.error(
                    f"Error in async signal handler {handler.__name__}: {e}",
                    exc_info=True,
                )
                responses.append((handler, e))

        return responses


def receiver(
    signal: Signal | list[Signal],
    sender: type | None = None,
    dispatch_uid: str | None = None,
) -> Callable[[T], T]:
    """
    Decorator to connect a function to a signal.

    Args:
        signal: Signal or list of signals to connect to.
        sender: Optional model class to filter signals.
        dispatch_uid: Optional unique ID to prevent duplicate connections.

    Returns:
        Decorator function.

    Example:
        ```python
        from p8s.db.signals import Signal, receiver
        from products.models import Product

        @receiver(Signal.POST_SAVE, sender=Product)
        def on_product_save(sender, instance, created, **kwargs):
            if created:
                send_notification(f"New product: {instance.name}")

        @receiver([Signal.POST_SAVE, Signal.POST_DELETE], sender=Product)
        def log_product_change(sender, instance, **kwargs):
            log_audit_trail(instance)
        ```
    """
    signals = signal if isinstance(signal, list) else [signal]

    def decorator(func: T) -> T:
        for sig in signals:
            SignalDispatcher.connect(sig, func, sender, dispatch_uid)
        return func

    return decorator


# Convenience functions
def connect(
    signal: Signal,
    receiver_func: Callable,
    sender: type | None = None,
    dispatch_uid: str | None = None,
) -> None:
    """
    Connect a receiver function to a signal.

    This is a convenience wrapper around SignalDispatcher.connect.

    Args:
        signal: The signal to connect to.
        receiver_func: The function to call when signal is sent.
        sender: Optional model class to filter signals.
        dispatch_uid: Optional unique identifier.
    """
    SignalDispatcher.connect(signal, receiver_func, sender, dispatch_uid)


def disconnect(
    signal: Signal,
    receiver_func: Callable,
    sender: type | None = None,
) -> bool:
    """
    Disconnect a receiver from a signal.

    Args:
        signal: The signal to disconnect from.
        receiver_func: The function to remove.
        sender: The sender class used when connecting.

    Returns:
        True if handler was removed, False if not found.
    """
    return SignalDispatcher.disconnect(signal, receiver_func, sender)


def send(signal: Signal, sender: type, **kwargs: Any) -> list[tuple[Callable, Any]]:
    """
    Send a signal synchronously.

    Args:
        signal: The signal to send.
        sender: The class sending the signal.
        **kwargs: Arguments to pass to handlers.

    Returns:
        List of (handler, response) tuples.
    """
    return SignalDispatcher.send(signal, sender, **kwargs)


async def send_async(
    signal: Signal,
    sender: type,
    **kwargs: Any,
) -> list[tuple[Callable, Any]]:
    """
    Send a signal asynchronously.

    Args:
        signal: The signal to send.
        sender: The class sending the signal.
        **kwargs: Arguments to pass to handlers.

    Returns:
        List of (handler, response) tuples.
    """
    return await SignalDispatcher.send_async(signal, sender, **kwargs)


# ============================================================================
# Pre-defined signal instances for Django compatibility
# ============================================================================

pre_save = Signal.PRE_SAVE
post_save = Signal.POST_SAVE
pre_delete = Signal.PRE_DELETE
post_delete = Signal.POST_DELETE
post_init = Signal.POST_INIT
m2m_changed = Signal.M2M_CHANGED


__all__ = [
    # Signal enum
    "Signal",
    # Dispatcher
    "SignalDispatcher",
    # Decorator
    "receiver",
    # Functions
    "connect",
    "disconnect",
    "send",
    "send_async",
    # Signal instances
    "pre_save",
    "post_save",
    "pre_delete",
    "post_delete",
    "post_init",
    "m2m_changed",
]
