# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-29

### Added
- Full Python 3.10+ support with modern type hints
- Pydantic v2 support with pydantic-settings
- `py.typed` marker for PEP 561 compliance
- Comprehensive docstrings and documentation
- Modern async/await patterns throughout
- `contextvars` for thread-safe global state
- Proper SSL/TLS handling with `ssl.SSLContext`
- Improved error classes with better messages
- `EmailMultiAlternatives` for HTML emails
- Mass mailing support with `send_mass_mail`

### Changed
- **BREAKING**: Minimum Python version is now 3.10
- **BREAKING**: Pydantic v2 required (v1 no longer supported)
- **BREAKING**: Configuration uses `pydantic-settings`
- Migrated from Black/isort/flake8 to Ruff for linting/formatting
- Updated aiosmtplib to v3.0+
- Improved type safety throughout codebase
- Better exception handling with custom exception classes
- Modernized project structure with `pyproject.toml` (hatchling)

### Removed
- Python 3.6-3.9 support
- Pydantic v1 support
- Legacy configuration patterns
- `setup.cfg`, `pytest.ini`, `tox.ini` (consolidated into `pyproject.toml`)

### Fixed
- Thread-safety issues with global mailman state
- SSL/TLS context handling
- File backend path handling
- Header injection validation

## [0.0.4] - 2021-XX-XX

### Fixed
- Remove the typo of the GPL license name at the end of the README.md file
- Dependency update

## [0.0.3] - 2021-XX-XX

### Changed
- License changed to MIT from GPL3
- Added the patch version of PIP

## [0.0.2] - 2021-XX-XX

### Fixed
- Some typo fixed at README.md
- Some broken link fixed at README.md
- Prevent the log file overlapping issue