from __future__ import annotations

import copy
import json
import threading
from typing import Any, Dict, Optional


Observation = Dict[str, Any]


class ObservationEmitter:
    """Best-effort, fire-and-forget observation emitter."""

    def __init__(self, target: str) -> None:
        self._target = target

    def emit(self, observation: Observation) -> None:
        thread = threading.Thread(
            target=_emit_observation,
            args=(self._target, observation),
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


def _emit_observation(target: str, observation: Observation) -> None:
    try:
        payload = json.dumps(observation, separators=(",", ":"), sort_keys=True)
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(payload + "\n")
    except Exception:
        pass
