# Phase 1: Bug Fixes & Code Quality

**Branch:** `fix/phase1-bug-fixes-code-quality`
**Files changed:** 7 (5 source + 2 tests) | +123 / -195 lines

## Summary

Fixes 8 bugs and code quality issues identified during codebase audit. No new features — purely correctness and cleanup.

## Changes

### Bug Fixes

| # | Issue | Fix | File |
|---|-------|-----|------|
| 1.1 | Port parameter in `RabbitMQConnection.__init__` was immediately overwritten (`port = 5671` on next line). Default was `5617` (typo). | Use passed value, fix default to `5671`. Only set SSL options when `use_tls=True`. | `connection.py` |
| 1.2 | Guideline name `rabbimq_broker_sizing_guide` missing the 't' in rabbitmq. Tool docstring also had the typo, so agents would always use the wrong name. | Fixed to `rabbitmq_broker_sizing_guide` in handler and docstring. | `handlers.py`, `module.py` |
| 1.3 | `rabbitmq_production_deployment_guidelines.md` exists in `doc/` but was never wired up in the handler. | Added to guideline lookup. | `handlers.py`, `module.py` |
| 1.4 | Handler referenced `rabbitmq_check_broker_follow_best_practice_instructions.md` which does not exist in `doc/`. Would crash at runtime. | Removed nonexistent reference. Refactored handler from if/elif chain to dict lookup for maintainability. | `handlers.py` |
| 1.7 | `RabbitMQAdmin` constructed `base_url` without port. Works for Amazon MQ (443 implicit) but fails for local RabbitMQ (15672). Also, `use_tls` was not passed from `initialize_connection`. | Added optional `port` param with smart defaults (443 TLS, 15672 non-TLS). Pass `use_tls` through. | `admin.py`, `module.py` |
| 1.8 | OAuth connection used `username="ignored"` — literal string appears in AMQP URL. | Changed to empty string. | `module.py` |

### Code Quality

| # | Issue | Fix | File |
|---|-------|-----|------|
| 1.5 | Every tool in `module.py` wrapped in `try: ... except Exception as e: raise e`. 18 instances. Adds zero value — no logging, no context, no transformation. | Removed all 18 bare try/except/raise wrappers. | `module.py` |
| 1.6 | `markdownify`, `protego`, `readabilipy` declared as dependencies but never imported. | Removed from `pyproject.toml`. | `pyproject.toml` |

## Testing

- All 44 existing tests pass
- Updated `test_admin.py` to expect port in `base_url` (`:443`)
- Updated `test_handlers.py` to use corrected guideline name
- `ruff check` clean — no lint issues

## Risk

Low. All changes are bug fixes or dead code removal. No new functionality. No API changes (tool names unchanged). The guideline name fix is technically a breaking change for any agent hardcoding the typo `rabbimq_broker_sizing_guide`, but that name was always wrong.
