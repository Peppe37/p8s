# AI Features

P8s treats AI as a first-class primitive, not a plugin.

## Overview

- **AIField**: Auto-generate content from prompts
- **VectorField**: Store embeddings for similarity search
- **VectorSearch**: Query by semantic similarity
- **Multi-provider support**: OpenAI, Anthropic, Ollama, etc.

## Configuration

Enable AI in `.env`:

```env
# Enable AI features
P8S_AI_ENABLED=true

# Provider (openai, anthropic, gemini, ollama)
P8S_AI_PROVIDER=openai

# API keys
P8S_AI_OPENAI_API_KEY=sk-...

# For Anthropic
P8S_AI_ANTHROPIC_API_KEY=sk-ant-...

# For local Ollama
P8S_AI_OLLAMA_BASE_URL=http://localhost:11434

# Embeddings
P8S_AI_EMBEDDING_ENABLED=true
P8S_AI_EMBEDDING_PROVIDER=openai
P8S_AI_EMBEDDING_MODEL=text-embedding-3-small
```

## AIField

Automatically generate content when a model is saved:

```python
from p8s import Model
from p8s.ai import AIField
from sqlmodel import Field

class Product(Model, table=True):
    name: str
    description: str

    # Auto-generated SEO description
    seo_description: str | None = AIField(
        prompt="Generate a compelling SEO meta description (max 160 chars) for a product named '{name}' with description: {description}",
        source_fields=["name", "description"],
        max_length=160,
    )
```

### Parameters

| Parameter       | Type        | Description                          |
| --------------- | ----------- | ------------------------------------ |
| `prompt`        | `str`       | Template with `{field}` placeholders |
| `source_fields` | `list[str]` | Fields to inject into prompt         |
| `max_length`    | `int`       | Max output length                    |
| `model`         | `str`       | Override default model               |
| `temperature`   | `float`     | Creativity (0.0-1.0)                 |

### Example: Multiple AI fields

```python
class Article(Model, table=True):
    content: str

    summary: str | None = AIField(
        prompt="Summarize this article in 2 sentences: {content}",
        source_fields=["content"],
    )

    tags: str | None = AIField(
        prompt="Generate 5 relevant tags for: {content}. Return as comma-separated list.",
        source_fields=["content"],
    )
```

## VectorField

Store embeddings for semantic search:

```python
from p8s.ai import VectorField

class Document(Model, table=True):
    title: str
    content: str

    # Auto-generated embedding
    embedding: list[float] | None = VectorField(
        source_field="content",
        dimensions=1536,  # OpenAI embedding size
    )
```

### Parameters

| Parameter      | Type  | Description       |
| -------------- | ----- | ----------------- |
| `source_field` | `str` | Field to embed    |
| `dimensions`   | `int` | Vector dimensions |
| `model`        | `str` | Embedding model   |

## VectorSearch

Query by semantic similarity:

```python
from p8s.ai import VectorSearch

# Create search instance
search = VectorSearch(Document, "embedding")

# Find similar documents
results = await search.similar(
    session,
    query="machine learning basics",
    limit=10,
    threshold=0.7,  # Minimum similarity
)

for doc, score in results:
    print(f"{doc.title}: {score:.2f}")
```

### Parameters

| Parameter   | Type    | Description              |
| ----------- | ------- | ------------------------ |
| `query`     | `str`   | Natural language query   |
| `limit`     | `int`   | Max results              |
| `threshold` | `float` | Minimum similarity (0-1) |
| `filters`   | `dict`  | Additional WHERE filters |

### With filters

```python
results = await search.similar(
    session,
    query="python tutorial",
    limit=5,
    filters={"category": "programming"},
)
```

## Direct AI Client

Access the AI client directly:

```python
from p8s.ai.client import get_ai_client

client = get_ai_client()

# Generate text
response = await client.generate(
    prompt="Explain quantum computing in simple terms",
    max_tokens=500,
)
print(response.text)

# Generate embeddings
embeddings = await client.embed("Hello, world!")
print(len(embeddings))  # 1536 for OpenAI
```

## Supported Providers

### OpenAI (default)

```env
P8S_AI_PROVIDER=openai
P8S_AI_OPENAI_API_KEY=sk-...
P8S_AI_OPENAI_MODEL=gpt-4
```

### Anthropic

```env
P8S_AI_PROVIDER=anthropic
P8S_AI_ANTHROPIC_API_KEY=sk-ant-...
P8S_AI_ANTHROPIC_MODEL=claude-3-sonnet
```

### Ollama (local)

```env
P8S_AI_PROVIDER=ollama
P8S_AI_OLLAMA_BASE_URL=http://localhost:11434
P8S_AI_OLLAMA_MODEL=llama2
```

### Google Gemini

```env
P8S_AI_PROVIDER=gemini
P8S_AI_GEMINI_API_KEY=...
P8S_AI_GEMINI_MODEL=gemini-pro
```

## Database Requirements

For VectorField with PostgreSQL, install pgvector:

```sql
CREATE EXTENSION vector;
```

For SQLite, vector operations are simulated using cosine similarity calculations.

## Best Practices

1. **Cache embeddings** - Don't regenerate on every request
2. **Use appropriate models** - Smaller models for embeddings, larger for generation
3. **Handle failures gracefully** - AI calls can fail or timeout
4. **Set reasonable limits** - Use `max_tokens` and `max_length`
5. **Monitor costs** - Track API usage in production
