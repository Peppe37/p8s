# P8s Feature Roadmap v3.0

> **Status**: Active Development\
> **Created**: 2026-01-16\
> **Completed**: 2026-01-17\
> **Goal**: Complete Django parity + Enhanced DX

---

## Executive Summary

Roadmap v2.0 completato. Questa v3.0 si concentra su:
1. **Security** - CSRF, password reset, 2FA
2. **Admin UX** - Search, filters, export, audit log
3. **CLI DX** - loaddata/dumpdata, check, auto-discovery
4. **Testing** - Factory, coverage, rich client

---

## Feature Status Overview

| #   | Feature                | Priority | Status     |
| --- | ---------------------- | -------- | ---------- |
| 1   | CSRF Middleware        | 🔴 P0     | ✅ Complete |
| 2   | Admin Search/Filter    | 🔴 P0     | ✅ Complete |
| 3   | Password Reset Flow    | 🔴 P0     | ✅ Complete |
| 4   | Admin Export CSV       | 🟡 P1     | ✅ Complete |
| 5   | Admin Audit Log        | 🟡 P1     | ✅ Complete |
| 6   | Fixtures loaddata      | 🟡 P1     | ✅ Complete |
| 7   | Fixtures dumpdata      | 🟡 P1     | ✅ Complete |
| 8   | Rate Limit per User    | 🟢 P2     | ✅ Complete |
| 9   | Factory Boy            | 🟢 P2     | ✅ Complete |
| 10  | 2FA/MFA Support        | 🟢 P2     | ✅ Complete |
| 11  | CLI Check Command      | ⚪ P3     | ✅ Complete |
| 12  | Command Auto-Discovery | ⚪ P3     | ✅ Complete |

---

## 🔴 P0: Critical

### 1. CSRF Middleware ✅

**Goal**: Protezione Cross-Site Request Forgery

```python
from p8s.csrf import CSRFMiddleware

app.add_middleware(CSRFMiddleware)

# In forms
<input type="hidden" name="csrf_token" value="{{ csrf_token }}">
```

**Files**:
- `src/p8s/csrf.py` ✅ - Token generation/validation

---

### 2. Admin Search/Filter

**Goal**: Ricerca full-text e filtri avanzati

```python
class ProductAdmin:
    search_fields = ["name", "description"]
    list_filter = ["category", "created_at", "is_active"]
    date_hierarchy = "created_at"
```

**Files**:
- `src/p8s/admin/router.py` [MODIFY] - Search/filter endpoints
- `src/p8s/admin/ui/` [MODIFY] - Search/filter UI components

---

### 3. Password Reset Flow ✅

**Goal**: Reset password completo via email

```python
from p8s.auth.password import PasswordResetService

service = PasswordResetService(secret_key="...", email_sender=send_email)
token = service.create_reset_token(user.id)
```

**Files**:
- `src/p8s/auth/password.py` ✅ - Reset logic with tokens

---

## 🟡 P1: High Priority

### 4. Admin Export CSV/Excel ✅

**Goal**: Export dati da admin panel

```python
from p8s.admin.export import export_csv, export_excel

csv_data = export_csv(products, fields=["name", "price"])
```

**Files**:
- `src/p8s/admin/export.py` ✅

---

### 5. Admin Audit Log ✅

**Goal**: Tracciare modifiche admin

```python
from p8s.admin.logs import LogEntry, log_action, ActionFlag

await log_action(session, user_id, "Product", product.id, ActionFlag.CHANGE)
```

**Files**:
- `src/p8s/admin/logs.py` ✅

---

### 6-7. Fixtures (loaddata/dumpdata) ✅

**Goal**: Import/export dati JSON

```python
from p8s.cli.fixtures import dump_model, load_fixture

json_data = await dump_model(session, Product)
await load_fixture(session, "fixtures/products.json", {"Product": Product})
```

**Files**:
- `src/p8s/cli/fixtures.py` ✅

---

## 🟢 P2: Medium Priority

### 8. Rate Limit per User

**Goal**: Throttling per utente autenticato

```python
@rate_limit(user_key="user_id", limit=100, period=3600)
async def api_endpoint():
    pass
```

---

### 9. Factory Boy Integration

**Goal**: Test factories per models

```python
from p8s.testing import ModelFactory

class ProductFactory(ModelFactory):
    class Meta:
        model = Product

    name = factory.Faker("product_name")
```

---

### 10. 2FA/MFA Support

**Goal**: Two-factor authentication

```python
from p8s.auth.mfa import TOTPDevice

# Setup
device = TOTPDevice.create(user)
qr_code = device.get_qr_code()

# Verify
device.verify(otp_code)
```

---

## ⚪ P3: Nice to Have

### 11. CLI Check Command

```bash
p8s check  # Validate configuration
```

### 12. Command Auto-Discovery

Auto-discover commands from `management/commands/`

---

## Implementation Order

1. ~~CSRF Middleware~~ ✅
2. ~~Password Reset~~ ✅
3. Admin Search/Filter
4. ~~Admin Export~~ ✅
5. ~~Fixtures~~ ✅
6. Remaining features

---

## Success Metrics

- [x] 5/7 P0-P1 features complete
- [x] 429 tests passing
- [ ] Full Django parity documentation

