# P8s Django Parity: R&D Documentation

> **Status**: Active Development\
> **Created**: 2026-01-07\
> **Last Updated**: 2026-01-10

## Panoramica

Questo documento traccia lo sviluppo delle funzionalità necessarie per raggiungere la parità con Django, escludendo le funzionalità AI-specific che sono già implementate.

## Principio Fondamentale

> [!IMPORTANT]
> Tutte le funzionalità core (migrazioni, auth, admin, etc.) devono funzionare **senza AI**.
> L'AI (`AIField`, `VectorField`) è un'aggiunta opzionale.

---

## Feature Comparison

### ✅ Già Implementate

| Feature     | Django              | P8s                              | File                  |
| ----------- | ------------------- | -------------------------------- | --------------------- |
| ORM/Models  | Django ORM          | SQLModel                         | `db/base.py`          |
| UUID PKs    | Manuale             | Auto                             | `db/base.py`          |
| Timestamps  | Manuale             | Auto                             | `db/base.py`          |
| Soft Delete | Manuale             | Built-in (.active(), .deleted()) | `db/base.py`          |
| Migrazioni  | manage.py           | p8s CLI + Alembic (auto-detect)  | `db/migrations.py`    |
| Admin Panel | Django Admin        | React Admin                      | `admin/`              |
| Auth/JWT    | django.contrib.auth | p8s.auth                         | `auth/`               |
| User Model  | AbstractUser        | User                             | `auth/models.py`      |
| Permissions | auth.Permission     | Permission/Group                 | `auth/permissions.py` |
| Signals     | django.dispatch     | p8s.signals                      | `signals.py`          |
| Email       | django.core.mail    | p8s.email                        | `email/`              |
| Cache       | django.cache        | p8s.cache                        | `cache/`              |
| Settings    | settings.py         | Pydantic                         | `core/settings.py`    |
| CLI         | manage.py           | Typer                            | `cli/main.py`         |
| Forms       | django.forms        | p8s.forms                        | `forms/`              |
| CSRF        | CsrfViewMiddleware  | CSRFMiddleware                   | `middleware.py`       |
| FileField   | django.db.models    | p8s.storage                      | `storage/`            |
| Testing     | django.test         | p8s.testing                      | `testing.py`          |

### ✅ Implementato (Gennaio 2026)

| Feature             | Descrizione         | Status |
| ------------------- | ------------------- | ------ |
| `p8s dbshell`       | Open database shell | ✅ Done |
| `p8s check`         | System checks       | ✅ Done |
| `p8s sendtestemail` | Email test          | ✅ Done |
| `p8s dumpdata`      | Export fixtures     | ✅ Done |
| `p8s loaddata`      | Import fixtures     | ✅ Done |
| Forms module        | Pydantic forms      | ✅ Done |
| ModelForm           | Auto-generated      | ✅ Done |
| CSRF Middleware     | Form protection     | ✅ Done |

### 🔄 In Progress / Future

| Feature            | Priorità | Status      | Note               |
| ------------------ | -------- | ----------- | ------------------ |
| Admin Actions bulk | 🟡 Media  | Implemented | `admin/actions.py` |
| Admin Inlines      | 🟡 Media  | Future      | Nested models      |
| i18n/l10n          | 🟢 Bassa  | Future      | Translations       |
| Sessions           | 🟢 Bassa  | Future      | DB/Redis backend   |
| Sitemap/RSS        | 🟢 Bassa  | Future      | SEO tools          |

---

## Test Coverage

```bash
# Run all tests
pytest tests/ -v

# Current status (Jan 2026)
# 186 passed, 31 warnings
```

| Test File           | Tests   | Status |
| ------------------- | ------- | ------ |
| test_admin.py       | 12      | ✅      |
| test_auth.py        | 9       | ✅      |
| test_forms.py       | 17      | ✅      |
| test_middleware.py  | 13      | ✅      |
| test_soft_delete.py | 13      | ✅      |
| test_testing.py     | 16      | ✅      |
| ...                 | ...     | ...    |
| **Total**           | **186** | ✅      |

---

## P8s vs Django: Vantaggi Distintivi

| Feature               | Django | P8s                    | Vantaggio |
| --------------------- | ------ | ---------------------- | --------- |
| AI Fields             | ❌      | ✅ AIField, VectorField | **P8s**   |
| Vector Search         | ❌      | ✅ Built-in             | **P8s**   |
| TypeScript Types      | ❌      | ✅ Auto-generated       | **P8s**   |
| Async by Default      | ❌      | ✅ FastAPI/asyncio      | **P8s**   |
| OpenAPI Schema        | ❌      | ✅ Automatic            | **P8s**   |
| React Admin           | ❌      | ✅ Modern UI            | **P8s**   |
| Full-stack Hot Reload | ❌      | ✅ Backend + Frontend   | **P8s**   |

---

## Changelog

### v0.2.x (Current - Jan 2026)
- ✅ ORM completo con soft delete avanzato
- ✅ Migrazioni Alembic con auto-detect
- ✅ Admin Panel React
- ✅ JWT Auth con permissions/groups
- ✅ AI Fields (opzionali)
- ✅ Forms module (Pydantic-based)
- ✅ CSRF Middleware
- ✅ CLI completo (18+ comandi)
- ✅ 186 tests

### v0.3.0 (Planned)
- 🔲 Admin Inlines
- 🔲 i18n support
- 🔲 Sessions backend

### v0.4.0 (Planned)
- 🔲 Sitemap generator
- 🔲 RSS feeds
