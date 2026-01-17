# p8s

<p align="center">
  <img src="assets/logo.svg" alt="P8s Logo" width="200" height="200" />
</p>

**Forge AI-native, full-stack applications with the fire of the gods.**

p8s is a high-performance, async-first Python framework built on top of **FastAPI**, **SQLModel**, and **React**. It brings the "batteries-included" experience of Django to the modern async ecosystem.

## Key Features

- **Async by Default**: Built on Starlette and FastAPI for maximum performance.
- **AI-Native**: First-class support for LLMs, Vector Databases, and RAG.
- **Type Safe**: Fully typed codebase leveraging Pydantic and Python 3.10+ types.
- **Batteries Included**: Auth, Admin Panel, ORM, Migrations, and more out of the box.
- **Modern Admin**: A sleek, React-based Admin Panel that feels premium.

## Installation

```bash
pip install p8s
```

## Quick Start

```python
from p8s.core import P8s

app = P8s()

@app.get("/")
async def root():
    return {"message": "Hello from p8s!"}
```
