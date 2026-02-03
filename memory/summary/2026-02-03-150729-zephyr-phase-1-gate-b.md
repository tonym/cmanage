# Zephyr Phase 1 Gate B — Context Summary

## Goal

Deliver Zephyr Phase 1 Gate B as a minimal, JSON-first, append-only inbox with predictable submission-order cursoring, and make the repo runnable via standard install + pytest.

## Outcome

* `CManageInbox` returns dict envelopes for `submit`, `list`, and `get`.
* Cursoring is submission-order using an opaque base64(JSON) index (strictly-after semantics).
* Tests assert JSON boundaries, deterministic paging, multi-reader behavior, invalid cursor errors.
* `pyproject.toml` and `README.md` enable `pip install -e ".[test]"` + `pytest` from a clean clone.
* `tests/conftest.py` sys.path hack removed; pytest config handles discovery.

## Invariants (Must Remain True)

* In-memory only; append-only inbox; no persistence across restarts.
* JSON-shaped public surface for `submit`/`list`/`get`.
* Cursor remains opaque and lists items strictly after the cursor in submission order.
* Timestamps use `datetime.now(timezone.utc).isoformat()` with `+00:00`.
* No routing, claiming, acking, retries, or orchestration logic.

* Source handoffs: memory/handoff/2026-02-03-142048-cmanage-gate-b-correction-pass.md, memory/handoff/2026-02-03-150419-repo-test-scaffolding.md

## Key Decisions

* Use submission-order index cursor encoded as base64(JSON) `{"i": <index>}`.
* Keep timestamp format unchanged (ISO-8601 with explicit `+00:00` offset).
* Use setuptools via `pyproject.toml` and configure pytest `pythonpath` to avoid sys.path hacks.
* Keep runtime dependencies at zero; add pytest only as optional `test` dependency.

* Source handoffs: memory/handoff/2026-02-03-142048-cmanage-gate-b-correction-pass.md, memory/handoff/2026-02-03-150419-repo-test-scaffolding.md

## System Constraints

* Python 3 standard library only at runtime.
* No persistence, no network services, no background workers.
* Package install must work via `pip install -e ".[test]"` from repo root.

* Source handoffs: memory/handoff/2026-02-03-142048-cmanage-gate-b-correction-pass.md, memory/handoff/2026-02-03-150419-repo-test-scaffolding.md

## Failure Modes (Now Explicit)

* Invalid cursor input must raise `ValueError("invalid cursor")`.
* Any sorting by timestamp/UUID would break submission-order determinism.
* Editable installs require setuptools availability in the environment.
* Removing pytest `pythonpath` config would reintroduce import errors without install.

* Source handoffs: memory/handoff/2026-02-03-142048-cmanage-gate-b-correction-pass.md, memory/handoff/2026-02-03-150419-repo-test-scaffolding.md

## What Is Explicitly Out of Scope

* Persistence (files/DB/CGraph), routing/dispatch, background workers, CLI.
* Linting/formatting tooling beyond pytest.

## Open Questions / Inputs to Next Phase

* (none)

* Source handoffs: memory/handoff/2026-02-03-142048-cmanage-gate-b-correction-pass.md, memory/handoff/2026-02-03-150419-repo-test-scaffolding.md

## Implementation Notes (Optional)

* (optional)

## End State

Gate B inbox behavior is submission-ordered and JSON-first with deterministic paging; tests pass via standard install flow (`pip install -e ".[test]"` then `pytest`); repo remains minimal and headless.
