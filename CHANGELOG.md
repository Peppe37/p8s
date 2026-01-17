# CHANGELOG


## v1.5.2 (2026-01-17)

### Bug Fixes

- **ci**: Add fetch-tags to resolve semantic-release merge-base error
  ([`1504db5`](https://github.com/Peppe37/p8s/commit/1504db52deb7285d9a97c8862e54ceec4b7c0599))


## v1.5.1 (2026-01-17)

### Bug Fixes

- **security**: Update vite to resolve esbuild vulnerability
  ([`dfc0349`](https://github.com/Peppe37/p8s/commit/dfc0349484cf7206e47279a040ca5f44ba801c83))

- Resolves GHSA-67mh-4wv8-2f99 in esbuild <=0.24.2

- **security**: Replace vulnerable python-jose with PyJWT
  ([`9f98c1c`](https://github.com/Peppe37/p8s/commit/9f98c1c0efe63ae20e7cb8f5ecdd5f1bd08a2de5))

- Removes CVE-2024-23342 (ecdsa) involved in python-jose dependency tree

- Updates auth/security.py to use PyJWT

- Suppress duplicate model warnings and finalize test suite stability
  ([`50df239`](https://github.com/Peppe37/p8s/commit/50df239f04a873dcd331529ba8aa2855305dcf95))

- **admin**: Register advanced field types and update build assets
  ([`b02d659`](https://github.com/Peppe37/p8s/commit/b02d659b60993b920088bb9cee646398455b9594))

- Update registry.py to detect richtext, color, tags, code, and slug fields.

- Update static/index.html with new asset hashes.

- Linting
  ([`d352edf`](https://github.com/Peppe37/p8s/commit/d352edf9923f1b71bd31fce4c218d99bd7a37061))

- Author surname
  ([`e751d5b`](https://github.com/Peppe37/p8s/commit/e751d5b8c5b1232746cb4b45c92f937ab0e8a52f))

- Update project metadata and remove deprecated action
  ([`da9e011`](https://github.com/Peppe37/p8s/commit/da9e011eab81d681c6e992eb6db352e89810af84))

- Use Trusted Publishing instead of API token for PyPI
  ([`25447e9`](https://github.com/Peppe37/p8s/commit/25447e93e4452d49ba3220731f64ca29d3e67dbf))

- Trigger first PyPI release
  ([`451219c`](https://github.com/Peppe37/p8s/commit/451219c698a93c11c68654348e8fb7887387e78d))

- Clean dist directory before build to avoid permission errors
  ([`bd24810`](https://github.com/Peppe37/p8s/commit/bd248105438f3ec43a13767a18cec67d71dbc083))

- Linting and build pipeline
  ([`c8c7eea`](https://github.com/Peppe37/p8s/commit/c8c7eea8d760680ec7bf8a8c8c812869a1862f00))

- Updated pyproject.toml to use new ruff lint section syntax - Formatted all 50+ source files with
  ruff format - Fixed missing model lookup in admin router get_item - Added node_modules exclusion
  to hatch build config - Updated CI workflow to Python 3.11-3.13 - Added comprehensive lint ignore
  rules for edge cases

- Test suite
  ([`4113d97`](https://github.com/Peppe37/p8s/commit/4113d970295a5951ef3efde4c50b1d92ee7a2ac4))

- Routing
  ([`0d4fc98`](https://github.com/Peppe37/p8s/commit/0d4fc98b58b0430ad912f06d513506787765324f))

- Admin update
  ([`cabb9c8`](https://github.com/Peppe37/p8s/commit/cabb9c88d4dc189cfc57c2e3700dc487220c2552))

### Chores

- Finalize project state (CI parity, Tests, Fixes)
  ([`82f5e52`](https://github.com/Peppe37/p8s/commit/82f5e52351bd984f863a7945eedd3bfa22d66998))

- ci: use pre-commit action for linting parity

- test: add integration tests for advanced fields

- fix: resolve Pydantic V2 metadata issues and SAWarning

- docs: add mkdocs-material dependency

### Code Style

- Fix linting and formatting issues
  ([`9a0e757`](https://github.com/Peppe37/p8s/commit/9a0e75765a1ad3afecb2c07e8e320d863e121f45))

### Continuous Integration

- Add pre-commit hooks and fix linting issues
  ([`1e13758`](https://github.com/Peppe37/p8s/commit/1e13758ac6638c051669ac357677cb1570add9a9))

- Remove duplicate build step (semantic-release handles it)
  ([`06c4c9b`](https://github.com/Peppe37/p8s/commit/06c4c9b958640d4f5831fc99f89a373207b56804))

### Documentation

- Add how-to guides and update navigation
  ([`84fbb3c`](https://github.com/Peppe37/p8s/commit/84fbb3c7e20acdda0d77d12cf2ffdaa5856bd0c7))

- Update roadmap, status reports and core project configuration
  ([`4ee83ca`](https://github.com/Peppe37/p8s/commit/4ee83ca742d01c126ceb5c309f3ce3726570614e))

- Roadmap jenuary 2026
  ([`92c26a1`](https://github.com/Peppe37/p8s/commit/92c26a1552b47cc637ca783cb611f974f885f89d))

- Cleanup and professionalize documentation and usage
  ([`58f8ece`](https://github.com/Peppe37/p8s/commit/58f8ece438438527b2af0bf82a15afd1c38e5797))

- Remove emojis from README, CLI, and docs for professional tone - Update README with absolute links
  and better formatting - Ensure consistent author attribution - Finalize MkDocs configuration setup

- Documentation and readme update
  ([`0497a8e`](https://github.com/Peppe37/p8s/commit/0497a8e6db21bca7b4c890fc160bfe0227bedf81))

- Revise README for P8s framework introduction
  ([`008dd00`](https://github.com/Peppe37/p8s/commit/008dd005955f37712d0ad4cb817ae6576ae28d90))

Updated README to reflect new branding and features of P8s framework.

### Features

- **admin**: Enhance RichTextEditor and fix UI spacing
  ([`8d0de83`](https://github.com/Peppe37/p8s/commit/8d0de832d12883962715e093e1d487fa43fa1b16))

- Add Font/Color/Size controls to RichTextEditor.

- Fix content parsing bug in RichTextEditor.

- Implement unified Image popup.

- Fix Admin button spacing.

- Rebuild admin UI assets.

- **admin**: Add advanced field components (richtext, color, tags, code)
  ([`a3e47a3`](https://github.com/Peppe37/p8s/commit/a3e47a34492b94b11da010e04a0c40e1c3573ec1))

- Implement oauth2 social login and advanced model fields
  ([`5ecb0e9`](https://github.com/Peppe37/p8s/commit/5ecb0e949f806770aab488331519341a0974de4f))

- Add admin enhancements, CLI system checks, command discovery and multi-db support
  ([`c42b72f`](https://github.com/Peppe37/p8s/commit/c42b72fd080f9edf1875129e2feb88c14c574eeb))

- Implement core framework features including CSRF, MFA, i18n, and sessions
  ([`13e1fda`](https://github.com/Peppe37/p8s/commit/13e1fda04561c55c3ff98e676e694ffa448294ae))

- Add seed/types commands, tailwind v4 template, and setup_context utility
  ([`4d26441`](https://github.com/Peppe37/p8s/commit/4d26441a8d7ab1c18c2b1480e4ca94a573898361))

- Dynamic version loading and MkDocs customization
  ([`0fd562a`](https://github.com/Peppe37/p8s/commit/0fd562a38ba5afc2efe45b3525192116ed235a14))

- Use importlib.metadata for dynamic __version__ from pyproject.toml - Add custom MkDocs theme with
  fire palette colors - Add announcement banner with version display - Add logo, favicon, and social
  links (GitHub + email) - Update PyPI description to be more professional

- Setup documentation site with mkdocs-material
  ([`3b19423`](https://github.com/Peppe37/p8s/commit/3b194239488ac6d5149d3a698acaa9e59443243d))

- Middleware and fields
  ([`05d97a5`](https://github.com/Peppe37/p8s/commit/05d97a5a5a425e01414c60cec97102042212aff9))

- Debug pages
  ([`6f6e8ef`](https://github.com/Peppe37/p8s/commit/6f6e8efe2ae7440d7d9ea29ddb0a1df44a19cd9a))

- Favicon
  ([`8466f3e`](https://github.com/Peppe37/p8s/commit/8466f3e2d47069de5d8a09895d27a65b7e754205))

- Admin page and models fields
  ([`a831c9f`](https://github.com/Peppe37/p8s/commit/a831c9f9de90ed5cb5367d5c4ac0eb16e899eeb5))

- Update auth and decorators
  ([`9ed4032`](https://github.com/Peppe37/p8s/commit/9ed4032c82100e5f89f78cf33cbb12b7eb3827be))

- Docs and refinements
  ([`41548a9`](https://github.com/Peppe37/p8s/commit/41548a97d25d6293ee3911d324cb4000c1451be0))

- First structure need updates
  ([`9864902`](https://github.com/Peppe37/p8s/commit/98649028578c76fbc8025d19234a42a600b4a101))
