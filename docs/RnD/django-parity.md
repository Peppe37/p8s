# P8s Django Parity: R&D Documentation

> **Status**: Active Development\
> **Created**: 2026-01-07\
> **Last Updated**: 2026-01-07

## Panoramica

Questo documento traccia lo sviluppo delle funzionalità necessarie per raggiungere la parità con Django, escludendo le funzionalità AI-specific che sono già implementate.

## Principio Fondamentale

> [!IMPORTANT]
> Tutte le funzionalità core (migrazioni, auth, admin, etc.) devono funzionare **senza AI**.
> L'AI (`AIField`, `VectorField`) è un'aggiunta opzionale.

---

## Feature Comparison

### ✅ Già Implementate

| Feature     | Django              | P8s               | File               |
| ----------- | ------------------- | ----------------- | ------------------ |
| ORM/Models  | Django ORM          | SQLModel          | `db/base.py`       |
| UUID PKs    | Manuale             | Auto              | `db/base.py`       |
| Timestamps  | Manuale             | Auto              | `db/base.py`       |
| Soft Delete | Manuale             | Built-in          | `db/base.py`       |
| Migrazioni  | manage.py           | p8s CLI + Alembic | `db/migrations.py` |
| Admin Panel | Django Admin        | React Admin       | `admin/`           |
| Auth/JWT    | django.contrib.auth | p8s.auth          | `auth/`            |
| User Model  | AbstractUser        | User              | `auth/models.py`   |
| Settings    | settings.py         | Pydantic          | `core/settings.py` |
| CLI         | manage.py           | Typer             | `cli/main.py`      |

### ❌ Da Implementare

| Feature              | Priorità | Status  | Target                |
| -------------------- | -------- | ------- | --------------------- |
| Permissions/Groups   | 🔴 Alta   | Planned | `auth/permissions.py` |
| Signals              | 🔴 Alta   | Planned | `db/signals.py`       |
| FileField/ImageField | 🔴 Alta   | Planned | `storage/`            |
| Admin Actions        | 🟡 Media  | Planned | `admin/`              |
| Admin Inlines        | 🟡 Media  | Planned | `admin/`              |
| Email Backend        | 🟡 Media  | Future  | `email/`              |
| Cache Framework      | 🟡 Media  | Future  | `cache/`              |

---

## Implementation Roadmap

### Fase 1: Permissions & Groups (v0.3.0)

Implementare sistema permessi Django-style:

```python
# Nuovi modelli
Permission(codename, name, content_type)
Group(name, permissions)

# Estensioni User
User.groups
User.user_permissions
User.has_perm(perm)
User.has_perms(perms)
```

**Files**:
- `src/p8s/auth/permissions.py` - Nuovi modelli
- `src/p8s/auth/models.py` - Aggiornare User

### Fase 2: Signals (v0.3.0)

Sistema hooks per model lifecycle:

```python
from p8s.db.signals import Signal, receiver

@receiver(Signal.POST_SAVE, sender=Product)
def on_product_save(sender, instance, created):
    ...
```

**Files**:
- `src/p8s/db/signals.py` - Nuovo modulo

### Fase 3: File Uploads (v0.4.0)

Storage e campi file:

```python
from p8s.storage import FileField, ImageField

class Document(Model, table=True):
    file: str = FileField(upload_to="documents/")
    thumbnail: str = ImageField(upload_to="thumbs/")
```

**Files**:
- `src/p8s/storage/__init__.py`
- `src/p8s/storage/base.py`
- `src/p8s/storage/fields.py`

---

## Testing Strategy

```bash
# Verificare che le feature esistenti funzionino senza AI
pytest tests/ -v -k "not ai"

# Test specifici per nuove feature
pytest tests/test_permissions.py
pytest tests/test_signals.py
pytest tests/test_storage.py
```

---

## Changelog

### v0.2.x (Current)
- ✅ ORM completo
- ✅ Migrazioni Alembic
- ✅ Admin Panel
- ✅ JWT Auth
- ✅ AI Fields (opzionali)

### v0.3.0 (Planned)
- 🔲 Permissions/Groups
- 🔲 Signals

### v0.4.0 (Planned)
- 🔲 FileField/ImageField
- 🔲 Admin Actions
