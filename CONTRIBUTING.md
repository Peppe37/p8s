# Contributing to P8s

Thank you for your interest in contributing to P8s! 🔥

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Peppe37/p8s.git
   cd p8s
   ```

2. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

3. Run tests:
   ```bash
   pytest tests/
   ```

## Commit Guidelines

We use **Conventional Commits** for automatic semantic versioning.

### Commit Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type       | Description                  | Version Bump  |
| ---------- | ---------------------------- | ------------- |
| `feat`     | New feature                  | MINOR (0.X.0) |
| `fix`      | Bug fix                      | PATCH (0.0.X) |
| `docs`     | Documentation                | None          |
| `style`    | Code style (no logic change) | None          |
| `refactor` | Code refactoring             | None          |
| `perf`     | Performance improvement      | PATCH         |
| `test`     | Add/modify tests             | None          |
| `chore`    | Maintenance                  | None          |
| `ci`       | CI/CD changes                | None          |
| `build`    | Build system                 | None          |

### Breaking Changes

For breaking changes, add `!` after the type:

```
feat!: remove deprecated API endpoints
```

Or add `BREAKING CHANGE:` in the footer:

```
feat: change authentication flow

BREAKING CHANGE: JWT tokens now require email instead of username
```

### Examples

```bash
# Bug fix (PATCH)
git commit -m "fix: resolve admin login redirect issue"

# New feature (MINOR)
git commit -m "feat(admin): add bulk export functionality"

# Breaking change (MAJOR)
git commit -m "feat!: change settings module discovery"

# Documentation
git commit -m "docs: update getting started guide"

# With scope and body
git commit -m "feat(ai): add support for Anthropic provider

Add LiteLLM integration for Claude models.
Includes embedding support via text-embedding-3-small."
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Make your changes
4. Run tests: `pytest tests/`
5. Run linting: `ruff check src/`
6. Commit with conventional commit message
7. Push and create a Pull Request

## Code Style

- Use `ruff` for linting and formatting
- Follow PEP 8 guidelines
- Add type hints to all functions
- Write docstrings for public APIs

```bash
# Format code
ruff format src/

# Check linting
ruff check src/

# Fix auto-fixable issues
ruff check --fix src/
```

## Running Tests

```bash
# All tests
pytest tests/

# With coverage
pytest tests/ --cov=src/p8s

# Specific test file
pytest tests/test_core.py -v
```

## Questions?

Open an issue for questions or discussions.
