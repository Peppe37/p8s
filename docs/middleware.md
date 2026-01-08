# Middleware

Django-style middleware for request/response processing.

## Creating Middleware

```python
from p8s.middleware import Middleware

class MyMiddleware(Middleware):
    async def process_request(self, request, call_next):
        # Before request processing
        print(f"Request: {request.url}")
        
        response = await call_next(request)
        
        # After response
        response.headers["X-Custom"] = "value"
        return response
```

## Adding to App

```python
from p8s.middleware import add_middleware

add_middleware(app, MyMiddleware())
```

Or multiple:
```python
from p8s.middleware import configure_middlewares

configure_middlewares(app, [
    RequestTimingMiddleware(),
    SecurityHeadersMiddleware(),
])
```

## Built-in Middlewares

### Request Timing
```python
from p8s.middleware import RequestTimingMiddleware

add_middleware(app, RequestTimingMiddleware())
# Adds X-Request-Time header
```

### Security Headers
```python
from p8s.middleware import SecurityHeadersMiddleware

add_middleware(app, SecurityHeadersMiddleware(
    frame_options="DENY",
    xss_protection="1; mode=block",
))
# Adds X-Frame-Options, X-Content-Type-Options, etc.
```

### Maintenance Mode
```python
from p8s.middleware import MaintenanceModeMiddleware

add_middleware(app, MaintenanceModeMiddleware(
    enabled=True,
    allowed_ips=["127.0.0.1"],
    message="Site under maintenance",
))
# Returns 503 for non-allowed IPs
```

### Request Logging
```python
from p8s.middleware import RequestLoggingMiddleware

add_middleware(app, RequestLoggingMiddleware())
# Logs: GET /api/users 200 (0.053s)
```
