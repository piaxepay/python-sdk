# Python SDK Architecture

This repository is the standalone Python distribution for the Piaxis partner API.

## Repository Layout

- `src/piaxis_sdk/`: runtime package
- `tests/`: contract-focused tests using the checked-in fixture file
- `contracts/payment-api-fixtures.json`: shared API fixture snapshot for regression coverage
- `examples/`: runnable integration examples
- `.github/workflows/`: CI and release automation

## Design Rules

- Mirror public API resources closely so SDK method names remain predictable.
- Keep transport and response normalization inside the client layer, not in examples.
- Prefer additive changes so existing integrations do not break on minor releases.
- Keep the checked-in fixture file aligned with the public API contract before release.

## Testing Strategy

- Unit-style contract tests run against `contracts/payment-api-fixtures.json`.
- Build validation runs through `python -m build`.
- Metadata validation runs through `python -m twine check dist/*`.

## Release Discipline

- Bump versions with semantic versioning.
- Update README and examples when new endpoints are added.
- Publish only after contract tests and distribution checks pass.
