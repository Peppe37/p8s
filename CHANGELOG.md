# CHANGELOG


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
