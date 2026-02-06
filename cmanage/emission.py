from __future__ import annotations

import copy
import threading
from typing import Any, Callable, Dict, Optional


Observation = Dict[str, Any]
EmitTransport = Callable[[str, Observation], None]


class ObservationEmitter:
    """Best-effort, fire-and-forget observation emitter."""

    def __init__(self, target: str, transport: EmitTransport) -> None:
        self._target = target
        self._transport = transport

    def emit(self, observation: Observation) -> None:
        thread = threading.Thread(
            target=_emit_observation,
            args=(self._transport, self._target, observation),
            daemon=True,
        )
        thread.start()


def build_observation(
    event: str,
    envelope: Dict[str, Any],
    observed_at: str,
    claim: Optional[Dict[str, Any]] = None,
) -> Observation:
    payload: Observation = {
        "event": event,
        "observedAt": observed_at,
        "envelope": copy.deepcopy(envelope),
    }
    if claim is not None:
        payload["claim"] = copy.deepcopy(claim)
    return payload


def missing_transport(_: str, __: Observation) -> None:
    raise RuntimeError("emit transport not configured")


def _emit_observation(
    transport: EmitTransport,
    target: str,
    observation: Observation,
) -> None:
    try:
        transport(target, observation)
    except Exception:
        pass
