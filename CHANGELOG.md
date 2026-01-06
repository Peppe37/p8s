# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Django-style settings discovery with `P8S_SETTINGS_MODULE`
- Protected `/docs` and `/redoc` endpoints (admin-only)
- CLI log tags `[backend]` and `[frontend]` with colors
- Django-style admin panel at `/admin/`
- Comprehensive documentation in `docs/`
- GitHub Actions for CI and releases

### Changed
- Admin panel now serves HTML at `/admin/` without auth (frontend handles login)
- Updated README with professional layout

### Fixed
- Settings not being loaded from project's `settings.py`
- Admin login URL path (`/api/auth/login` → `/auth/login`)

## [0.1.0] - 2026-01-06

### Added
- Initial release
- FastAPI-based async backend
- SQLModel ORM integration
- JWT authentication
- Admin panel with React UI
- AIField and VectorField for AI-native features
- CLI tools (`p8s new`, `p8s dev`, `p8s createsuperuser`)
