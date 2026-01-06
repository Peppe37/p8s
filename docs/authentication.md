# Authentication

P8s includes a complete authentication system with JWT tokens.

## Overview

- **JWT-based authentication**
- **User model** with roles (User, Superuser)
- **Secure password hashing** (bcrypt)
- **Access & refresh tokens**
- **Protected routes** via dependencies

## API Endpoints

| Method | Endpoint         | Description          |
| ------ | ---------------- | -------------------- |
| POST   | `/auth/register` | Create new user      |
| POST   | `/auth/login`    | Get JWT tokens       |
| POST   | `/auth/refresh`  | Refresh access token |
| GET    | `/auth/me`       | Get current user     |
| POST   | `/auth/logout`   | Logout (client-side) |

## Registration

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword",
    "username": "johndoe"
  }'
```

Response:
```json
{
  "id": "uuid-here",
  "email": "user@example.com",
  "username": "johndoe",
  "role": "user",
  "is_active": true
}
```

## Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword"
  }'
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

## Using Tokens

Include the access token in the `Authorization` header:

```bash
curl http://localhost:8000/protected-endpoint \
  -H "Authorization: Bearer eyJ..."
```

## Protecting Routes

### Require any authenticated user

```python
from fastapi import Depends
from p8s.auth.dependencies import require_auth
from p8s.auth.models import User

@router.get("/profile")
async def get_profile(user: User = Depends(require_auth)):
    return {"email": user.email, "role": user.role}
```

### Require admin (superuser)

```python
from p8s.auth.dependencies import require_admin

@router.get("/admin-only")
async def admin_endpoint(user: User = Depends(require_admin)):
    return {"message": "Welcome, admin!"}
```

### Optional authentication

```python
from p8s.auth.dependencies import get_current_user

@router.get("/public")
async def public_endpoint(user: User | None = Depends(get_current_user)):
    if user:
        return {"message": f"Hello, {user.email}"}
    return {"message": "Hello, guest!"}
```

## User Roles

```python
from p8s.auth.models import UserRole

class UserRole(str, Enum):
    USER = "user"
    SUPERUSER = "superuser"
```

### Check role in code

```python
if user.role == UserRole.SUPERUSER:
    # Admin-only logic
    pass
```

## Configuration

Configure auth in `.env`:

```env
# Required
SECRET_KEY=your-256-bit-secret-key

# Token expiration (minutes)
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Password hashing
PASSWORD_MIN_LENGTH=8
```

Or in `settings.py`:

```python
class AppSettings(Settings):
    auth: AuthSettings = AuthSettings(
        secret_key="your-secret",
        access_token_expire_minutes=30,
        refresh_token_expire_days=7,
    )
```

## Password Security

Passwords are hashed using bcrypt:

```python
from p8s.auth.security import get_password_hash, verify_password

# Hash a password
hashed = get_password_hash("plaintext")

# Verify a password
is_valid = verify_password("plaintext", hashed)
```

## Creating Superusers

Via CLI:

```bash
p8s createsuperuser
```

Programmatically:

```python
from p8s.auth.models import User, UserRole
from p8s.auth.security import get_password_hash

user = User(
    email="admin@example.com",
    password_hash=get_password_hash("password"),
    role=UserRole.SUPERUSER,
    is_active=True,
    is_verified=True,
)
session.add(user)
await session.commit()
```

## Best Practices

1. **Use strong SECRET_KEY** (at least 256 bits)
2. **Store tokens securely** (HttpOnly cookies in production)
3. **Use HTTPS** in production
4. **Rotate refresh tokens** on use
5. **Log authentication events** for security auditing
