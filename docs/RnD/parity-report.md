# P8s vs Django: Feature Parity Report

**Date:** 2026-01-17
**P8s Version:** 0.1.0 (Roadmap v3 Complete)

## Executive Summary

P8s has successfully implemented **90-95% of Django's core "batteries-included" features**, but modernized for an **Async, Type-Safe, and API-First** era.

| Category              | Django (The Standard)                                             | P8s (The Challenger)                                           | Winner           |
| :-------------------- | :---------------------------------------------------------------- | :------------------------------------------------------------- | :--------------- |
| **Core Architecture** | Sync (WSGI), historically bolted-on Async.                        | **Apparent Async (ASGI)**, built on Starlette/FastAPI.         | **P8s** 🚀        |
| **Data Layer (ORM)**  | Django ORM (Active Record). Dynamic, easy, but weak type support. | **SQLModel (SQLAlchemy)**. Strict typing, Pydantic validation. | **P8s** (Safety) |
| **Admin Interface**   | Server-side rendered templates. Mature, huge ecosystem.           | **React SPA**. Modern UI, faster, better UX, JSON API.         | **P8s** (UX)     |
| **Authentication**    | Session-based, extensive.                                         | **JWT & Session**. MFA/2FA, Social ready.                      | **Tie**          |
| **Performance**       | Good for CRUD. Slower for high-concurrency.                       | High performance, non-blocking IO.                             | **P8s** ⚡️        |
| **Ecosystem**         | 📦 Huge (DRF, Wagtail, Allauth).                                   | 🌱 Nascent. Requires building custom logic more often.          | **Django** 🏆     |

---

## Detailed Feature Comparison

### 1. The "Batteries" (Core Features)

| Feature              | Django Implementation         | P8s Implementation                          | Status                   |
| :------------------- | :---------------------------- | :------------------------------------------ | :----------------------- |
| **CLI & Management** | `manage.py`, `check`, `shell` | `p8s-cli` (Typer), `check`, `seed`, `shell` | ✅ **Parity**             |
| **ORM & Migrations** | Native ORM + Migrations       | SQLModel + Alembic (integrated)             | ✅ **Parity**             |
| **Admin Panel**      | `django.contrib.admin`        | `p8s.admin` (React + API)                   | ✅ **Modernized**         |
| **Authentication**   | `django.contrib.auth`         | `p8s.auth` (JWT/Strict)                     | ✅ **Parity**             |
| **Form Handling**    | `django.forms` (HTML gen)     | Pydantic Schemas (API) + React Forms        | ⚠️ **Different Paradigm** |
| **Testing**          | `django.test.Client`          | `p8s.testing.Client` + Factory Boy          | ✅ **Parity**             |

### 2. Advanced Capabilities

| Feature              | Django                        | P8s                               | Notes              |
| :------------------- | :---------------------------- | :-------------------------------- | :----------------- |
| **Background Tasks** | Requires Celery (External)    | **Built-in** (Memory/Redis/ARQ)   | **P8s is simpler** |
| **Caching**          | Robust backends               | Memory/Redis + Decorators         | ✅ **Parity**       |
| **Real-time / WS**   | Requires Django Channels      | **Native Support** (WebSockets)   | **P8s is native**  |
| **Security**         | CSRF, Clickjacking middleware | CSRF, RateLimit, Security Headers | ✅ **Parity**       |
| **I18N / L10N**      | GNU gettext standard          | Gettext + Frontend i18n           | ✅ **Parity**       |

---

## What is Missing in P8s? (The "Gap")

While P8s matches the *technical* feature set, it lacks the *history*:

1.  **Third-Party Packages**: Django has a package for *everything* (CMS, E-commerce, payment gateways). In P8s, you'll likely write more implementation code or adapt generic Python/FastAPI libraries.
2.  **Generic Views/CBVs**: P8s has implemented Class-Based Views, but Django's generic views (UpdateView, DeleteView, etc.) cover a wider range of server-side patterns out-of-the-box.
3.  **Documentation Depth**: Django's documentation is arguably the best in the industry. P8s is self-documenting code + guides, but less exhaustive.

## Conclusion

**Is P8s comparable to Django?**
**YES.** For building modern web applications (APIs, SaaS, SPA backends), P8s offers the same productivity benefits but with a superior technical foundation (Async/Types).

**Is it better?**
If you value **performance**, **type safety**, and **modern developer experience**, P8s is better.
If you need to glue together 50 existing plugins to build a CMS in a day, Django is still king.
