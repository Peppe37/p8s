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

---

## Built-in Middlewares

### Request Timing

```python
from p8s.middleware import RequestTimingMiddleware

add_middleware(app, RequestTimingMiddleware())
# Adds X-Request-Time header with processing duration
```

### Security Headers

```python
from p8s.middleware import SecurityHeadersMiddleware

add_middleware(app, SecurityHeadersMiddleware(
    frame_options="DENY",
    xss_protection="1; mode=block",
    referrer_policy="strict-origin-when-cross-origin",
))
# Adds X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy
```

### Request Logging

```python
from p8s.middleware import RequestLoggingMiddleware

add_middleware(app, RequestLoggingMiddleware())
# Logs: GET /api/users 200 (0.053s)
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

---

## CSRF Protection

Cross-Site Request Forgery protection for form submissions.

```python
from p8s.middleware import CSRFMiddleware, MiddlewareWrapper

app.add_middleware(
    MiddlewareWrapper,
    middleware=CSRFMiddleware(
        exempt_paths=["/api/", "/webhooks/"],
    )
)
```

### Configuration

| Option           | Default                | Description                 |
| ---------------- | ---------------------- | --------------------------- |
| `secret_key`     | From settings          | Secret for token generation |
| `cookie_name`    | `_csrf`                | Cookie name                 |
| `header_name`    | `X-CSRF-Token`         | Header name                 |
| `form_field`     | `csrf_token`           | Form field name             |
| `exempt_paths`   | `["/api/"]`            | Paths to skip CSRF          |
| `exempt_methods` | `["GET", "HEAD", ...]` | Methods to skip             |
| `secure`         | `True`                 | HTTPS-only cookie           |
| `same_site`      | `strict`               | SameSite policy             |

### Usage in Templates

```html
<form method="POST" action="/submit">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <!-- form fields -->
</form>
```

### Getting Token in Code

```python
from p8s.middleware import get_csrf_token

@app.get("/form")
async def show_form(request: Request):
    token = get_csrf_token(request)
    return templates.TemplateResponse("form.html", {
        "request": request,
        "csrf_token": token,
    })
```

### AJAX Requests

```javascript
// Get token from cookie
const csrfToken = document.cookie
    .split('; ')
    .find(row => row.startsWith('_csrf='))
    ?.split('=')[1];

// Include in header
fetch('/submit', {
    method: 'POST',
    headers: {
        'X-CSRF-Token': csrfToken,
        'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
});
```

---

## Middleware Order

Middlewares execute in reverse order of registration:

```python
configure_middlewares(app, [
    RequestTimingMiddleware(),    # Executes 1st (outermost)
    SecurityHeadersMiddleware(),  # Executes 2nd
    CSRFMiddleware(),             # Executes 3rd (innermost)
])
```
