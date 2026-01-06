# 🔥 P8s Demo Application

A complete demo showcasing all P8s framework features.

## Features Demonstrated

- ✅ **FastAPI async backend** with P8sApp
- ✅ **SQLModel ORM** with UUID, timestamps, soft delete
- ✅ **JWT Authentication** with register, login, refresh
- ✅ **Auto-generated Admin API** endpoints
- ✅ **React frontend** with Vite + TypeScript
- ✅ **Database auto-creation** on startup

## Quick Start

### 1. Setup environment

```bash
# From p8s root
conda activate p8s

# Install p8s in dev mode (if not done)
pip install -e ".[dev]"
```

### 2. Run the demo

```bash
cd demo_p8s

# Copy env file (already done)
cp .env.example .env

# Run backend
uvicorn backend.main:app --reload --port 8000

# In another terminal, run frontend
cd frontend && npm run dev
```

### 3. Access the app

- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:5173

## API Endpoints

### Public
| Method | Endpoint          | Description     |
| ------ | ----------------- | --------------- |
| GET    | `/`               | Welcome message |
| GET    | `/api/health`     | Health check    |
| GET    | `/api/products`   | List products   |
| GET    | `/api/categories` | List categories |
| GET    | `/api/blog`       | List blog posts |

### Auth
| Method | Endpoint             | Description          |
| ------ | -------------------- | -------------------- |
| POST   | `/api/auth/register` | Register new user    |
| POST   | `/api/auth/login`    | Login (get tokens)   |
| POST   | `/api/auth/refresh`  | Refresh access token |
| GET    | `/api/auth/me`       | Get current user     |
| POST   | `/api/auth/logout`   | Logout               |

### Protected (require `Authorization: Bearer <token>`)
| Method | Endpoint          | Description      |
| ------ | ----------------- | ---------------- |
| POST   | `/api/products`   | Create product   |
| POST   | `/api/categories` | Create category  |
| POST   | `/api/blog`       | Create blog post |
| GET    | `/api/me`         | Get profile      |

## Example Usage

### Register a user
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@p8s.dev","password":"password123"}'
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@p8s.dev","password":"password123"}'
```

### Create a product (authenticated)
```bash
TOKEN="your-access-token"
curl -X POST "http://localhost:8000/api/products?name=Test&description=Demo&price=9.99" \
  -H "Authorization: Bearer $TOKEN"
```

## Project Structure

```
demo_p8s/
├── backend/
│   ├── main.py         # Main FastAPI app
│   ├── models.py       # SQLModel models
│   └── settings.py     # App settings
├── frontend/
│   ├── src/
│   │   ├── App.tsx     # React app
│   │   └── index.css   # Styles
│   └── package.json
├── .env                # Environment config
└── pyproject.toml      # Python project
```

## Models

### Product
- `name`, `description`, `price`, `stock`
- `category_id` (foreign key)
- Soft delete support
- Admin configuration

### Category
- `name`, `description`
- Has many Products

### BlogPost
- `title`, `content`, `excerpt`
- `is_published`, `is_featured`
- `author_id` (User foreign key)

### Tag
- `name`, `color`

## AI Fields (Optional)

Uncomment in `models.py` to enable:
- `Product.seo_description` - AI-generated SEO text
- `BlogPost.auto_summary` - AI-generated summary

Requires:
```bash
pip install p8s[ai]
export P8S_AI_OPENAI_API_KEY=sk-...
```

---

Built with 🔥 [P8s Framework](https://github.com/Peppe37/p8s)
