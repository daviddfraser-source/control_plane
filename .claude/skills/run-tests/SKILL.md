---
name: run-tests
description: Run tests and interpret results
allowed-tools: Bash(pytest *), Bash(npm test *), Bash(go test *), Bash(cargo test *), Read
argument-hint: "[test path or pattern]"
---

# Run Tests

## Commands by Framework

| Framework | Run All | Specific | Coverage |
|-----------|---------|----------|----------|
| pytest | `pytest` | `pytest tests/test_api.py` | `pytest --cov=src` |
| jest/vitest | `npm test` | `npm test -- tests/api.test.js` | `npm test -- --coverage` |
| go | `go test ./...` | `go test ./pkg/api` | `go test -cover ./...` |
| cargo | `cargo test` | `cargo test test_name` | — |

## Interpreting Results

- **Pass**: Proceed
- **Fail**: Read failure, fix code or test
- **Error**: Fix setup issue (missing dep, import)
- **Skip**: Verify skip reason is valid
