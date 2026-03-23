# Python SDK Deployment Guide

This repository publishes the `piaxis-sdk` package to PyPI.

## Prerequisites

1. Python 3.11+ installed locally.
2. PyPI publishing access for `piaxis-sdk`.
3. A clean working tree.

## Release Steps

1. Update the version in `pyproject.toml`.
2. Verify the README and examples reflect the current API.
3. Run local verification:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip build twine
python3 -m pip install -e .
python3 -m compileall src
python3 -m unittest discover -s tests -p "test_*.py"
python3 -m build
python3 -m twine check dist/*
```

4. If you must recover manually, publish once with Twine:

```bash
python3 -m twine upload dist/*
```

5. Configure PyPI trusted publishing on the `piaxis-sdk` project:

- provider: GitHub Actions
- owner: `piaxepay`
- repository: `python-sdk`
- workflow: `release-python.yml`
- environment: `pypi`

6. After trusted publishing is configured, release from GitHub Actions by tag:

```bash
git tag v0.2.0
git push origin v0.2.0
```

## GitHub Actions

- `ci.yml` runs validation on pushes and pull requests.
- `release-python.yml` publishes on tags or by manual dispatch.
- The release job uses the GitHub environment `pypi`.

Recommended tag format:

- `v0.2.0`

## Post-Release Checks

1. Confirm the package version appears on PyPI.
2. Install it in a fresh virtual environment.
3. Run one sandbox call against `https://sandbox.api.gopiaxis.com/api`.
