# Signals

Django-style signals for model lifecycle events.

## Available Signals

```python
from p8s.db.signals import Signal

Signal.PRE_SAVE      # Before create/update
Signal.POST_SAVE     # After create/update
Signal.PRE_DELETE    # Before delete
Signal.POST_DELETE   # After delete
Signal.POST_INIT     # After model init
Signal.M2M_CHANGED   # Many-to-many change
```

## Connecting Handlers

### Using @receiver Decorator

```python
from p8s.db.signals import Signal, receiver

@receiver(Signal.POST_SAVE, sender=Product)
def on_product_save(sender, instance, created, **kwargs):
    if created:
        print(f"New product: {instance.name}")
    else:
        print(f"Updated: {instance.name}")

@receiver(Signal.PRE_DELETE, sender=Product)
def on_product_delete(sender, instance, **kwargs):
    print(f"Deleting: {instance.name}")
```

### Manual Connection

```python
from p8s.db.signals import connect, disconnect

def my_handler(sender, **kwargs):
    ...

connect(Signal.POST_SAVE, my_handler, sender=Product)
disconnect(Signal.POST_SAVE, my_handler, sender=Product)
```

## Sending Signals

Signals are automatically sent by `CRUDBase` operations. For manual sending:

```python
from p8s.db.signals import send, send_async

# Sync
send(Signal.POST_SAVE, sender=Product, instance=product, created=True)

# Async
await send_async(Signal.POST_SAVE, sender=Product, instance=product, created=True)
```

## Handler Arguments

| Signal      | Arguments                 |
| ----------- | ------------------------- |
| PRE_SAVE    | sender, instance          |
| POST_SAVE   | sender, instance, created |
| PRE_DELETE  | sender, instance          |
| POST_DELETE | sender, instance          |
