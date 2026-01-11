# AI Features R&D

> **Status**: Stable\
> **Last Updated**: 2026-01-10

## Overview

P8s provides AI-native features that distinguish it from Django:

- **AIField** - Automatic content generation via LLM
- **VectorField** - Embedding generation for semantic search
- **Vector Search** - Built-in similarity search

## Architecture

```
┌─────────────────────────────────────────┐
│              Application                 │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│           P8s AI Processor               │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
│  │ AIField │  │ Vector  │  │ Hooks   │  │
│  │         │  │ Field   │  │         │  │
│  └─────────┘  └─────────┘  └─────────┘  │
└─────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐
   │ OpenAI  │ │Anthropic│ │ Ollama  │
   │   API   │ │   API   │ │ (local) │
   └─────────┘ └─────────┘ └─────────┘
```

## Supported Providers

| Provider     | Model Examples                 | Status   |
| ------------ | ------------------------------ | -------- |
| OpenAI       | gpt-4o, gpt-4o-mini            | ✅ Stable |
| Anthropic    | claude-3-opus, claude-3-sonnet | ✅ Stable |
| Google       | gemini-pro                     | ✅ Stable |
| Ollama       | llama2, mistral                | ✅ Stable |
| Azure OpenAI | gpt-4                          | ✅ Stable |
| Custom       | Any OpenAI-compatible          | ✅ Stable |

## Configuration

```python
# .env
P8S_AI_ENABLED=true
P8S_AI_PROVIDER=openai
P8S_AI_MODEL=gpt-4o-mini
P8S_AI_OPENAI_API_KEY=sk-...

# Optional
P8S_AI_TEMPERATURE=0.7
P8S_AI_MAX_TOKENS=1000
```

## AIField

Auto-generates content based on other model fields:

```python
from p8s import Model, AIField

class Review(Model, table=True):
    title: str
    content: str
    
    # Auto-generated on save
    sentiment: str = AIField(
        prompt="Analyze the sentiment of this review and return only one word: positive, negative, or neutral",
        source_fields=["content"]
    )
    
    summary: str = AIField(
        prompt="Summarize this review in one sentence",
        source_fields=["title", "content"]
    )
```

### Prompt Best Practices

```python
# ❌ Bad - verbose output
prompt="What is the sentiment?"  # Returns: "The sentiment appears to be..."

# ✅ Good - precise output
prompt="Return ONLY one word: positive, negative, or neutral"
```

## VectorField

Generates embeddings for semantic search:

```python
from p8s import Model, VectorField

class Document(Model, table=True):
    content: str
    
    # Auto-generated embedding
    embedding: list[float] = VectorField(
        source_field="content",
        dimensions=1536,  # OpenAI ada-002
    )
```

## Vector Search

```python
from p8s.ai.vector_search import VectorSearch

# Initialize
search = VectorSearch(
    model=Document,
    vector_field="embedding",
)

# Search
results = await search.similarity_search(
    query="machine learning basics",
    limit=10,
    threshold=0.8,
)
```

---

## Performance Considerations

| Operation             | Latency   | Notes                     |
| --------------------- | --------- | ------------------------- |
| AIField generation    | 500ms-2s  | Depends on model/provider |
| VectorField embedding | 100-300ms | Optimized batching        |
| Vector search         | 10-50ms   | In-memory with fallback   |

### Optimization Tips

1. **Batch processing** - Generate embeddings in bulk
2. **Caching** - AIField cache results where appropriate
3. **Async** - Use async session for non-blocking operations
4. **Local models** - Ollama for development/testing

---

## Future R&D

| Feature                 | Priority | Status   |
| ----------------------- | -------- | -------- |
| RAG Pipeline            | 🔴 High   | Research |
| Function Calling        | 🟡 Medium | Planned  |
| Streaming Responses     | 🟡 Medium | Planned  |
| Multi-modal (Images)    | 🟢 Low    | Future   |
| Fine-tuning Integration | 🟢 Low    | Future   |
