# Future Roadmap R&D

> **Status**: Planning\
> **Last Updated**: 2026-01-10\
> **Completed**: 2026-01-10\

## Vision

P8s aims to be the definitive Python framework for AI-native, full-stack applications.

---

## Short-term (Q1 2026)

### Admin Improvements

- [ ] **Admin Inlines** - Edit related models in same form
- [ ] **Admin Filters** - Auto-generated list filters
- [ ] **Admin Export** - CSV/Excel export from list view
- [ ] **Admin Audit Log** - Track changes

### Developer Experience

- [ ] **TypeScript Generation** - Complete type generation from models
- [ ] **Hot Module Reload** - Faster frontend updates
- [ ] **VS Code Extension** - Syntax highlighting, snippets

---

## Medium-term (Q2-Q3 2026)

### Internationalization

- [ ] **i18n** - Translation strings
- [ ] **l10n** - Locale-aware formatting
- [ ] **Timezone handling** - Per-user timezones

### Sessions

- [ ] **Session middleware** - Cookie-based sessions
- [ ] **Redis backend** - High-performance session store
- [ ] **Database backend** - Persistent sessions

### Background Tasks

- [ ] **Task queue integration** - Celery/ARQ
- [ ] **Scheduled tasks** - Cron-like scheduling
- [ ] **Admin task monitoring** - View running tasks

---

## Long-term (2027+)

### AI Enhancements

- [ ] **RAG Pipeline** - Retrieval-augmented generation
- [ ] **Function Calling** - LLM tool use
- [ ] **Multi-modal** - Image/audio processing
- [ ] **Agents** - Autonomous AI workflows

### Scalability

- [ ] **Multi-tenancy** - Shared database with tenant isolation
- [ ] **Sharding support** - Horizontal scaling
- [ ] **Read replicas** - Query routing

### Enterprise

- [ ] **SSO/SAML** - Enterprise authentication
- [ ] **Audit logging** - Compliance features
- [ ] **Role-based access** - Granular permissions
- [ ] **API rate limiting** - Built-in throttling

---

## Community Wishlist

Features requested by community (to be prioritized):

| Feature               | Votes | Status     |
| --------------------- | ----- | ---------- |
| GraphQL support       | 3     | Evaluating |
| WebSocket abstraction | 2     | Planned    |
| Stripe integration    | 2     | Consider   |
| OAuth providers       | 2     | Planned    |
| Docker templates      | 1     | Easy win   |

---

## Contributing

Want to help implement a feature? See [CONTRIBUTING.md](https://github.com/Peppe37/p8s/blob/main/CONTRIBUTING.md).

Priority areas:
1. Documentation improvements
2. Test coverage
3. Bug fixes
4. New middleware/utilities
