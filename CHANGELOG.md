# CHANGELOG


## v1.3.0 (2026-01-17)

### Documentation

- Update roadmap, status reports and core project configuration
  ([`e2ca422`](https://github.com/Peppe37/p8s/commit/e2ca42270d9323e2fb05f039c571bb9ad0655717))

- Roadmap jenuary 2026
  ([`b0252c8`](https://github.com/Peppe37/p8s/commit/b0252c89c237ee4ef77dbd7bb58d5bb2bf00e468))

### Features

- Implement oauth2 social login and advanced model fields
  ([`5c5baec`](https://github.com/Peppe37/p8s/commit/5c5baecbafc0268767ca3ae23e78ebc5910319ca))

- Add admin enhancements, CLI system checks, command discovery and multi-db support
  ([`0bc8da6`](https://github.com/Peppe37/p8s/commit/0bc8da6562037d6c0b7a03fa0c11172720c26bf4))

- Implement core framework features including CSRF, MFA, i18n, and sessions
  ([`deecbaa`](https://github.com/Peppe37/p8s/commit/deecbaa4fe94ca0ac0d9dcc12a1375bf7aa1be1d))

- Add seed/types commands, tailwind v4 template, and setup_context utility
  ([`842757f`](https://github.com/Peppe37/p8s/commit/842757f2b9ee0ec9716e4c064825f7ce06eca3dc))


## v1.2.0 (2026-01-12)

### Bug Fixes

- Author surname
  ([`3c98bcb`](https://github.com/Peppe37/p8s/commit/3c98bcbe98e8d0f94617873c266d06ff4646f4cb))

### Features

- Dynamic version loading and MkDocs customization
  ([`e4532d0`](https://github.com/Peppe37/p8s/commit/e4532d039b56101c96eb457ee1098a7f0f3af704))

- Use importlib.metadata for dynamic __version__ from pyproject.toml - Add custom MkDocs theme with
  fire palette colors - Add announcement banner with version display - Add logo, favicon, and social
  links (GitHub + email) - Update PyPI description to be more professional


## v1.1.0 (2026-01-12)

### Bug Fixes

- Update project metadata and remove deprecated action
  ([`68644ff`](https://github.com/Peppe37/p8s/commit/68644ffea8d739f1438fa0797f3f688d3b521094))

### Documentation

- Cleanup and professionalize documentation and usage
  ([`0726edb`](https://github.com/Peppe37/p8s/commit/0726edb0c26590b7c44c6f08d9c4ba350146faa7))

- Remove emojis from README, CLI, and docs for professional tone - Update README with absolute links
  and better formatting - Ensure consistent author attribution - Finalize MkDocs configuration setup

### Features

- Setup documentation site with mkdocs-material
  ([`3fd7ef0`](https://github.com/Peppe37/p8s/commit/3fd7ef025fedd6f982fd77a68a617eb2d408a22c))


## v1.0.3 (2026-01-11)

### Bug Fixes

- Use Trusted Publishing instead of API token for PyPI
  ([`4cc50e3`](https://github.com/Peppe37/p8s/commit/4cc50e3ac3adb7a2e76f907a787bc4d432d4d157))


## v1.0.2 (2026-01-11)

### Bug Fixes

- Trigger first PyPI release
  ([`23a3564`](https://github.com/Peppe37/p8s/commit/23a3564bd28448164dad7102620c99d7c5c221ef))

### Continuous Integration

- Remove duplicate build step (semantic-release handles it)
  ([`7b057db`](https://github.com/Peppe37/p8s/commit/7b057db94d183ea92a78cfa74328959044dcf181))


## v1.0.1 (2026-01-11)

### Bug Fixes

- Clean dist directory before build to avoid permission errors
  ([`25f0044`](https://github.com/Peppe37/p8s/commit/25f0044887d4a3926acbf0baa9a005ed9c3eb4a4))


## v1.0.0 (2026-01-11)

### Bug Fixes

- Linting and build pipeline
  ([`c337a0a`](https://github.com/Peppe37/p8s/commit/c337a0a0a8bcba5282dd6cdb22be18f4ce1f9edb))

- Updated pyproject.toml to use new ruff lint section syntax - Formatted all 50+ source files with
  ruff format - Fixed missing model lookup in admin router get_item - Added node_modules exclusion
  to hatch build config - Updated CI workflow to Python 3.11-3.13 - Added comprehensive lint ignore
  rules for edge cases

- Test suite
  ([`e632d79`](https://github.com/Peppe37/p8s/commit/e632d79f903fad8cd8a3b8d4e21eb1552ad37883))

- Routing
  ([`c12dab1`](https://github.com/Peppe37/p8s/commit/c12dab186028c605c7f2a696ffb1a9eeb776309e))

- Admin update
  ([`ffec28b`](https://github.com/Peppe37/p8s/commit/ffec28be0354e849cb25c5603022e084b946dd56))

### Documentation

- Documentation and readme update
  ([`321b44c`](https://github.com/Peppe37/p8s/commit/321b44c45d4578ec54b65885d3d938d0af09be99))

- Revise README for P8s framework introduction
  ([`4a9df4f`](https://github.com/Peppe37/p8s/commit/4a9df4fe8f58752225c1d88dd530722dbcd75436))

Updated README to reflect new branding and features of P8s framework.

### Features

- Middleware and fields
  ([`79036a9`](https://github.com/Peppe37/p8s/commit/79036a98e2dee1ccd2805eed8b13a2a674dfd83a))

- Debug pages
  ([`c97b698`](https://github.com/Peppe37/p8s/commit/c97b698a40e75ef1c00828a5dcb6b3312dcb8617))

- Favicon
  ([`8521d73`](https://github.com/Peppe37/p8s/commit/8521d733c2c954ba6133ee99ab4cc0be8c0daade))

- Admin page and models fields
  ([`217f8ba`](https://github.com/Peppe37/p8s/commit/217f8baa72f2dc350ab615ea659fe3155fc526b8))

- Update auth and decorators
  ([`a782ad0`](https://github.com/Peppe37/p8s/commit/a782ad04e9a8e7989c7354eaa47500415d5e3fc9))

- Docs and refinements
  ([`fbfc104`](https://github.com/Peppe37/p8s/commit/fbfc104144a73b89e332fc0b2c314e36152f4fd3))

- First structure need updates
  ([`6360458`](https://github.com/Peppe37/p8s/commit/6360458f38b9057ca4f3474ee4b91a1b031383ae))
