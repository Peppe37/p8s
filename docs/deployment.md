# Deployment

Guide for deploying P8s applications to production.

## Production Checklist

Before deploying:

- [ ] Set `DEBUG=false`
- [ ] Use strong `SECRET_KEY`
- [ ] Configure production database (PostgreSQL recommended)
- [ ] Set up HTTPS
- [ ] Configure CORS origins
- [ ] Build frontend for production
- [ ] Set up monitoring and logging

## Docker Deployment

### Dockerfile

```dockerfile
# Backend
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install -e ".[all]"

# Copy application
COPY . .

# Run migrations and start server
CMD ["sh", "-c", "p8s migrate && uvicorn backend.main:app --host 0.0.0.0 --port 8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: p8s
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: p8s
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://p8s:secret@db:5432/p8s
      SECRET_KEY: ${SECRET_KEY}
      DEBUG: "false"
    depends_on:
      - db

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

### Frontend Dockerfile

```dockerfile
# Build stage
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

## Nginx Configuration

```nginx
server {
    listen 80;
    server_name example.com;

    # Frontend (static files)
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Admin panel
    location /admin/ {
        proxy_pass http://backend:8000/admin/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Auth endpoints
    location /auth/ {
        proxy_pass http://backend:8000/auth/;
        proxy_set_header Host $host;
    }
}
```

## Environment Variables (Production)

```env
# Core
DEBUG=false
SECRET_KEY=<generate-with-openssl-rand-hex-32>

# Database (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://user:password@db.example.com:5432/p8s

# CORS (your domain)
CORS_ORIGINS=https://example.com,https://www.example.com

# AI (if using)
P8S_AI_ENABLED=true
P8S_AI_OPENAI_API_KEY=sk-...
```

## Cloud Platforms

### Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
railway login
railway init
railway up
```

### Render

Create `render.yaml`:

```yaml
services:
  - type: web
    name: p8s-backend
    env: python
    buildCommand: pip install -e ".[all]"
    startCommand: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: p8s-db
          property: connectionString
```

### Fly.io

```bash
fly launch
fly secrets set SECRET_KEY=$(openssl rand -hex 32)
fly deploy
```

## Database Migrations

Run migrations before starting the app:

```bash
# In Docker
CMD ["sh", "-c", "p8s migrate && uvicorn backend.main:app ..."]

# Manually
p8s migrate
```

## Monitoring

### Health Check

P8s includes a built-in health endpoint:

```bash
curl http://localhost:8000/health
# {"status": "healthy"}
```

### Logging

Configure structured logging:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Security Recommendations

1. **Use HTTPS** - Always use TLS in production
2. **Rotate secrets** - Change SECRET_KEY periodically
3. **Rate limiting** - Add rate limiting middleware
4. **CORS** - Only allow trusted origins
5. **Database** - Use connection pooling
6. **Secrets** - Never commit secrets to git
