# 🔥 P8s (Prometheus)

> **Forge AI‑native, full‑stack applications with the fire of the gods.**

P8s (pronounced *"pates"*) is an **opinionated, batteries‑included framework** that fuses the **architecture and DX of Django** with the **performance and async nature of FastAPI**, plus **first‑class AI/LLM integration** and a **native React frontend**.

It exists to solve a modern problem:

> Django is complete but legacy.
> FastAPI is fast but fragmented.
> AI apps need structure, not glue code.

**P8s brings order.**

---

## 🚀 Badges

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-async-success)
![React](https://img.shields.io/badge/React-Vite-61DAFB)
![AI Native](https://img.shields.io/badge/AI-Native-orange)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-experimental-red)

---

## 🧠 Philosophy

P8s is inspired by **Prometheus**, the titan who stole fire from the gods to give it to humanity.

In the same way, P8s:

* Takes **powerful primitives** (Async, ORM, Admin, React, AI)
* Hides unnecessary complexity
* Gives developers **immediate leverage**

### Core principles

* **Opinionated > Configurable**
* **Convention over glue code**
* **Async by default**
* **AI is not a plugin — it’s a primitive**
* **Backend and Frontend are one system**

---

## ✨ What P8s Is

✅ A **Django‑like framework** built on FastAPI
✅ A **full‑stack monolith**, but modern
✅ An **AI‑native platform**
✅ A **React‑first backend**

## ❌ What P8s Is NOT

❌ A micro‑framework
❌ Just another FastAPI boilerplate
❌ A collection of loosely coupled libraries

---

## 🧩 Features Overview

| Feature      | Description                                |
| ------------ | ------------------------------------------ |
| ⚡ Async Core | Built on FastAPI & Starlette               |
| 🗄️ ORM      | SQLModel (SQLAlchemy + Pydantic)           |
| 🔐 Auth      | Plug‑and‑play authentication & permissions |
| 🧑‍💼 Admin  | Auto‑generated **React Admin Panel**       |
| ⚛️ Frontend  | React + Vite, zero‑config                  |
| 🤖 AI / LLM  | Native AI fields, RAG, vector search       |
| 🧠 Types     | Python → TypeScript auto‑generation        |
| 🛠️ CLI      | `p8s` command like Django’s `manage.py`    |

---

## 🏗️ Architecture

P8s is a **single coherent system**, not a puzzle.

```
project/
├── backend/
│   ├── apps/          # Django‑style apps
│   ├── models.py      # SQLModel + AI fields
│   ├── main.py        # FastAPI entrypoint
│   └── settings.py    # Centralized config
│
├── frontend/
│   ├── src/
│   │   ├── pages/     # Route‑based React pages
│   │   └── components/
│   └── vite.config.ts
│
├── p8s.py              # CLI orchestrator
└── pyproject.toml
```

---

## 🔥 The P8s Stack

### Backend

* **FastAPI** – async routing & OpenAPI
* **SQLModel** – ORM + validation
* **Alembic (wrapped)** – migrations
* **Pydantic v2** – data core

### Frontend

* **React** – UI
* **Vite** – instant dev server
* **TanStack Query** – data fetching
* **Zustand** – admin state

### AI Layer

* **LiteLLM** – provider‑agnostic LLM access
* **Instructor** – structured AI outputs
* **pgvector** – embeddings & RAG

---

## 🤖 AI‑Native Models

AI is a **first‑class citizen** in P8s.

```python
from p8s import models, AIField

class Product(models.Model):
    name: str
    description: str

    seo_description: str = AIField(
        prompt="Generate an SEO description for: {description}"
    )
```

### What happens?

* Field is **generated automatically**
* Cached
* Regenerated on change
* Provider‑agnostic

---

## ⚛️ React Integration (Django‑like)

P8s treats React like Django templates — but modern.

### Zero‑config

```bash
p8s new app
p8s dev
```

Runs:

* FastAPI (Uvicorn)
* React (Vite)
* TypeScript type sync
* Proxy & HMR

No CORS. No manual wiring.

---

## 🧑‍💼 React Admin Panel

Just like Django Admin — but **React**.

* Auto‑generated from models
* Permissions aware
* Extensible with custom components

```python
class Product(models.Model):
    class Admin:
        list_display = ["name", "price"]
        search = ["name"]
```

---

## 🛠️ CLI (The Sacred Fire)

```bash
p8s new project myapp
p8s new app blog
p8s migrate
p8s dev
p8s admin
```

One command. One mental model.

---

## 🧬 Type Safety End‑to‑End

* SQLModel → Pydantic
* Pydantic → TypeScript
* Backend and frontend **never drift**

If Python changes, React breaks **at compile time**.

---

## 📦 Modular but Opinionated

P8s is monolithic **by default**, modular **by design**.

```bash
pip install p8s
pip install p8s-ai
pip install p8s-admin
```

---

## 🧪 Status

⚠️ **Experimental**

* APIs may change
* Not production‑ready (yet)
* Looking for early contributors

---

## 🤝 Contributing

P8s is built for developers who:

* Love structure
* Hate boilerplate
* Believe AI apps deserve real frameworks

PRs, RFCs and discussions are welcome.

---

## 📜 License

MIT — steal the fire, responsibly 🔥

---

## 🏛️ Final Words

> *Where Django brought order to the web,
> P8s brings order to AI‑native applications.*

🔥 **Welcome to Prometheus.**
