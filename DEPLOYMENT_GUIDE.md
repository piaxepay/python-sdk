# SDK Deployment Guide

This document shows how to publish the Piaxis SDKs for JavaScript/TypeScript and Python.

## Release model

Use one release flow per SDK:

- JavaScript/TypeScript SDK from `sdks/typescript`
- Python SDK from `sdks/python`

Recommended versioning:

- keep both SDKs aligned to the same API milestone where possible
- use semantic versioning
- bump major for breaking API or SDK behavior changes
- bump minor for new endpoints and backward-compatible features
- bump patch for fixes and docs-only improvements that do not change runtime behavior

## Before every release

1. Confirm the public `/api` contract you are releasing against.
2. Update version in the package manifest.
3. Update changelog or release notes.
4. Run local verification.
5. Publish to the registry.
6. Tag the release in git.

## JavaScript/TypeScript SDK

Source of truth:

- `sdks/typescript`

This package is implemented in TypeScript but publishes JavaScript artifacts for both JavaScript and TypeScript users.

### Prerequisites

1. Node.js 20+ installed.
2. npm account with publish access to the target package name.
3. `NPM_TOKEN` ready if publishing from CI.

### Local release steps

1. Move into the package directory:

```bash
cd sdks/typescript
```

2. Install dependencies:

```bash
npm install
```

3. Update the package version:

```bash
npm version patch
```

Use `minor` or `major` when appropriate.

4. Build the package:

```bash
npm run build
```

5. Optionally inspect the packed output:

```bash
npm pack --dry-run
```

6. Publish:

```bash
npm publish --access public
```

### CI publishing flow

1. Store `NPM_TOKEN` in your CI secrets.
2. Trigger on a tag like `js-sdk-v0.2.0` or on a manual release workflow.
3. In CI:

```bash
cd sdks/typescript
npm ci
npm run build
npm publish --access public
```

4. Use `.npmrc` or `NODE_AUTH_TOKEN` from CI secrets.

### Recommended checks

```bash
cd sdks/typescript
npm install
npm run build
```

If you add tests later:

```bash
npm test
```

## Python SDK

Source of truth:

- `sdks/python`

### Prerequisites

1. Python 3.10+ installed.
2. PyPI account or organization owner access.
3. `TWINE_USERNAME` and `TWINE_PASSWORD`, or a PyPI API token.

### Local release steps

1. Move into the package directory:

```bash
cd sdks/python
```

2. Create or activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install packaging tools:

```bash
python3 -m pip install --upgrade build twine
```

4. Update the version in `pyproject.toml`.

5. Build source and wheel distributions:

```bash
python3 -m build
```

6. Validate the package metadata:

```bash
python3 -m twine check dist/*
```

7. Publish:

```bash
python3 -m twine upload dist/*
```

### CI publishing flow

1. Store PyPI credentials in CI secrets.
2. Trigger on a tag like `py-sdk-v0.2.0` or on a manual release workflow.
3. In CI:

```bash
cd sdks/python
python3 -m pip install --upgrade build twine
python3 -m build
python3 -m twine check dist/*
python3 -m twine upload dist/*
```

### Recommended checks

```bash
cd sdks/python
python3 -m compileall src
```

If you add tests later:

```bash
pytest
```

## Registry and naming guidance

Recommended public names:

- JavaScript/TypeScript: `@piaxis/sdk`
- Python: `piaxis-sdk`

If these names are already taken, choose names that still clearly map to Piaxis.

## Git tagging

Suggested tag formats:

- `sdk-js-v0.1.0`
- `sdk-py-v0.1.0`

Or if you want one coordinated release:

- `sdk-v0.1.0`

## Post-release checklist

1. Verify the package appears on npm or PyPI.
2. Install it in a clean sample project.
3. Run a real request against sandbox.
4. Confirm the README examples still work.
5. Announce the release with install and upgrade notes.
