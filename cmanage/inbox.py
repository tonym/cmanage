from __future__ import annotations

import base64
import copy
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

from .emission import EmitTransport, ObservationEmitter, build_observation


Action = Dict[str, Any]


@dataclass(frozen=True)
class ActionEnvelope:
    id: str
    ts: str
    action: Action


class CManageInbox:
    """In-memory, append-only action inbox with cursor-based listing."""

    def __init__(
        self,
        emit_target: Optional[str] = None,
        emit_transport: Optional[EmitTransport] = None,
    ) -> None:
        self._items: List[ActionEnvelope] = []
        self._by_id: Dict[str, ActionEnvelope] = {}
        if emit_target and emit_transport:
            self._emitter = ObservationEmitter(emit_target, emit_transport)
        else:
            self._emitter = None

    def submit(self, action: Action) -> Dict[str, Any]:
        """Accept an action and return an envelope with id + ts."""
        self._validate_action(action)
        action_copy = copy.deepcopy(action)
        envelope = ActionEnvelope(
            id=str(uuid.uuid4()),
            ts=_utc_iso_now(),
            action=action_copy,
        )
        self._items.append(envelope)
        self._by_id[envelope.id] = envelope
        envelope_dict = _envelope_to_dict(envelope)
        self._emit_observation("intent.offered", envelope_dict)
        return envelope_dict

    def list(
        self,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        List items strictly after the cursor.

        cursor: opaque string encoding (submission index). None starts from the beginning.
        limit: max number of items returned; None returns all remaining.
        """
        start_index = _decode_cursor(cursor) + 1 if cursor is not None else 0
        end_index = start_index + limit if limit is not None else None
        items = self._items[start_index:end_index]
        next_cursor = _encode_cursor(start_index + len(items) - 1) if items else None
        return {"items": [_envelope_to_dict(item) for item in items], "nextCursor": next_cursor}

    def get(self, envelope_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an envelope by id if present."""
        env = self._by_id.get(envelope_id)
        return _envelope_to_dict(env) if env is not None else None

    def claim(self, envelope_id: str) -> Optional[Dict[str, Any]]:
        """Emit a claim observation for an envelope if present."""
        env = self._by_id.get(envelope_id)
        if env is None:
            return None
        envelope_dict = _envelope_to_dict(env)
        self._emit_observation("intent.claimed", envelope_dict)
        return envelope_dict

    def _emit_observation(
        self,
        event: str,
        envelope: Dict[str, Any],
        claim: Optional[Dict[str, Any]] = None,
    ) -> None:
        if self._emitter is None:
            return
        try:
            observation = build_observation(event, envelope, _utc_iso_now(), claim=claim)
            self._emitter.emit(observation)
        except Exception:
            pass

    @staticmethod
    def _validate_action(action: Action) -> None:
        if not isinstance(action, dict):
            raise TypeError("action must be a dict")
        action_type = action.get("type")
        if not isinstance(action_type, str) or not action_type:
            raise ValueError("action.type must be a non-empty string")
        if "payload" in action and not isinstance(action["payload"], dict):
            raise TypeError("action.payload must be a dict if provided")
        if "meta" in action and not isinstance(action["meta"], dict):
            raise TypeError("action.meta must be a dict if provided")


def parse_emit_target(argv: Sequence[str]) -> Optional[str]:
    """
    Parse a required --emit <target> flag from argv.

    Returns the target string if provided, otherwise None.
    """
    emit_targets = []
    idx = 0
    while idx < len(argv):
        if argv[idx] == "--emit":
            if idx + 1 >= len(argv):
                raise ValueError("--emit requires a target")
            emit_targets.append(argv[idx + 1])
            idx += 2
            continue
        idx += 1
    if not emit_targets:
        return None
    if len(emit_targets) > 1:
        raise ValueError("multiple --emit targets are not allowed")
    return emit_targets[0]


def _utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _encode_cursor(index: int) -> str:
    payload = json.dumps({"i": index}, separators=(",", ":"), sort_keys=True)
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")


def _decode_cursor(cursor: str) -> int:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii"))
        data = json.loads(raw.decode("utf-8"))
        index = data["i"]
        if not isinstance(index, int) or isinstance(index, bool) or index < 0:
            raise ValueError
        return index
    except Exception as exc:
        raise ValueError("invalid cursor") from exc


def _envelope_to_dict(envelope: ActionEnvelope) -> Dict[str, Any]:
    return {
        "id": envelope.id,
        "ts": envelope.ts,
        "action": copy.deepcopy(envelope.action),
    }
