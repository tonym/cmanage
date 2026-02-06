# Phase 3 Observational Emission & Historical Awareness — Context Summary

## Goal

Add optional, write-only observational emission from CManage to an explicitly
provided target without changing CManage behavior, adding memory, or introducing
runtime coupling to CGraph.

## Outcome

* Added an optional observation emitter with injected transport, preserving
  target opacity and fire-and-forget semantics.
* CManage emits `intent.offered` on submit and `intent.claimed` on claim when
  emission is enabled; no other lifecycle events are emitted.
* Emission is best-effort, non-blocking, and failure-isolated from inbox
  behavior.
* Added `parse_emit_target` to support a required `--emit <target>` flag.
* Tests cover optional emission, emit + claim, and `--emit` parsing.

## Invariants (Must Remain True)

* CManage remains in-memory, append-only, and JSON-first.
* No persistence, deduplication, retries, buffering, or reconciliation logic.
* Emission is write-only; CManage never reads from CGraph.
* Emission does not affect intake, visibility, claims, or downstream execution.

## Key Decisions

* Treat the emit target as opaque; resolve delivery via injected transport.
* Emit only catalog-level events: `intent.offered` and `intent.claimed`.
* Default to a missing-transport handler that raises (and is swallowed) to keep
  flag semantics without introducing coupling.

## System Constraints

* Runtime dependencies remain standard library only.
* No new network services, workers, or persistence layers.
* Emission can be enabled only at initialization and is immutable for process
  lifetime.

## Failure Modes (Now Explicit)

* Transport failures are swallowed; emission never blocks inbox behavior.
* Missing transport results in attempted emission that safely fails.
* Async thread launch may drop events under extreme resource pressure, without
  affecting inbox semantics.

## What Is Explicitly Out of Scope

* Any CGraph changes or assumptions about CGraph internals.
* Event deduplication, retries, buffering, reconciliation, or analytics.
* Execution lifecycle events (start/completion/success/failure).
* Runtime coupling or read-back from any target.

## Open Questions / Inputs to Next Phase

* (none)

* Source handoffs: memory/handoff/2026-02-03-142048-cmanage-gate-b-correction-pass.md, memory/handoff/2026-02-03-150419-repo-test-scaffolding.md

## Implementation Notes (Optional)

* Emission transport is injected to keep the target opaque and avoid file-path
  semantics.

## End State

Phase 3 adds optional observational emission from CManage that is write-only,
best-effort, and isolated from inbox behavior, while preserving all prior
architectural invariants and leaving CGraph untouched.
