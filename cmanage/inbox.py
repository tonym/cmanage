from __future__ import annotations

import base64
import copy
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


Action = Dict[str, Any]


@dataclass(frozen=True)
class ActionEnvelope:
    id: str
    ts: str
    action: Action


class CManageInbox:
    """In-memory, append-only action inbox with cursor-based listing."""

    def __init__(self) -> None:
        self._items: List[ActionEnvelope] = []
        self._by_id: Dict[str, ActionEnvelope] = {}

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
        return _envelope_to_dict(envelope)

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
