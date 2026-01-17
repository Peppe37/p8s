# P8s Feature Roadmap v4.0

> **Goal**: Content & Ecosystem Expansion
> **Created**: 2026-01-17
> **Completed**: 2026-01-17
> **Target**: Q3 2026

Questa roadmap si concentra sul colmare il gap dell'ecosistema (Social Login) e dei contenuti (Rich Text Editor), portando P8s verso capacità CMS-like.

---

## Feature Status Overview

| #   | Feature                 | Priority | Status     |
| --- | ----------------------- | -------- | ---------- |
| 1   | **OAuth2 Social Login** | 🔴 P0     | ✅ Complete |
| 2   | **Rich Text Field**     | 🔴 P0     | ✅ Complete |
| 3   | **Slug Field**          | 🟡 P1     | ✅ Complete |
| 4   | **JSON Field**          | 🟡 P1     | ✅ Exists   |
| 5   | **Tag Field**           | 🟢 P2     | ✅ Complete |
| 6   | **Color Field**         | 🟢 P2     | ✅ Complete |
| 7   | **Code Field**          | ⚪ P3     | ✅ Complete |

---

## 🔴 P0: Critical Features

### 1. OAuth2 / Social Login Support

**Goal**: Supporto nativo per login con Google, GitHub, Microsoft, ecc.

**Integrazione**: Estendere `p8s.auth` per supportare flow OAuth2 standard e OIDC.

**Implementation Plan**:
- Integrare libreria `httpx-oauth`.
- Aggiungere modelli `SocialAccount` linkati a `User`.
- Endpoint API `/auth/login/google`, `/auth/callback/google`.
- Frontend Admin update per configurare provider.

```python
# p8s/auth/social.py
class GoogleProvider(OAuth2Provider):
    client_id = settings.GOOGLE_CLIENT_ID
    client_secret = settings.GOOGLE_CLIENT_SECRET
    authorize_url = "https://accounts.google.com/o/oauth2/v2/auth"
```

---

### 2. Rich Text / Block Editor Field ("WordPress-style")

**Goal**: Un'esperienza di scrittura moderna e potente direttamente nell'Admin, simile a Notion o Gutenberg.

**Tecnologia**: Implementazione Frontend React usando **Tiptap** (Headless WYSIWYG) o **Editor.js** (Block-based).
**Backend**: Storage come JSON (per Block Editor) o HTML sanitizzato.

**Implementation Plan**:
- **Backend**: `RichTextField` (stores JSON/HTML).
- **Admin UI**: Componente `RichTextEditor` integrato nel sistema di form.
- Supporto per immagini, embedding, tabelle.

```python
# Backend
from p8s.fields import RichTextField

class Article(Model, table=True):
    title: str
    content: dict = RichTextField(editor="tiptap")  # Stores API-ready JSON
```

---

## 🟡 P1: High Priority (Advanced Fields)

### 3. Slug Field

**Goal**: Generazione automatica di URL-friendly slugs da altri campi (es. Titolo).

```python
class Article(Model, table=True):
    title: str
    slug: str = SlugField(populate_from="title", unique=True)
```

### 4. JSON Field (con Editor Visuale)
**Goal**: Editing visuale di strutture JSON complesse, non solo text area.

```python
class PageConfig(Model, table=True):
    config: dict = JSONField(schema=MyPydanticSchema)
```

---

## 🟢 P2: Medium Priority (UX Enhancements)

### 5. Tag Field / Array Field
**Goal**: Input multiplo con "Chips" UI per tag, categorie, keyword.
Backend: `ARRAY` (Postgres) o JSON list (SQLite/MySQL).

### 6. Color Field
**Goal**: Picker colore visivo nell'Admin.
`color: str = ColorField(format="hex")` -> Renderizza `<input type="color">`.

---

## ⚪ P3: Nice to Have

### 7. Code Field
**Goal**: Editor con syntax highlighting (Monaco/CodeMirror) per campi che contengono codice CSS/JS/Python.

### 8. GeoLocation Field
**Goal**: Selezione coordinate su mappa (Google Maps / OpenStreetMap integration).

---

## Suggerimenti per il Futuro

Per competere davvero con Django nell'ambito CMS:
1.  **StreamField (Wagtail-like)**: Definire blocchi strutturati misti (Titolo + Immagine + Quote) lato backend.
2.  **Asset Management**: Gestione avanzata media centralizzata (non solo upload su campo).
