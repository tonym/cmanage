from __future__ import annotations

import json
import time

import pytest

from cmanage import CManageInbox, parse_emit_target


def _action(t, payload=None, meta=None):
    action = {"type": t}
    if payload is not None:
        action["payload"] = payload
    if meta is not None:
        action["meta"] = meta
    return action


def test_submit_wraps_action_with_id_and_ts():
    inbox = CManageInbox()
    action = _action("alpha", payload={"x": 1}, meta={"source": "test"})
    env = inbox.submit(action)

    assert env["id"]
    assert env["ts"].endswith("+00:00")
    assert env["action"] == action
    assert env["action"] is not action


def test_list_with_cursor_and_limit_is_deterministic():
    inbox = CManageInbox()
    submitted_ids = [inbox.submit(_action(f"t{i}"))["id"] for i in range(5)]

    first = inbox.list(limit=2)
    second = inbox.list(cursor=first["nextCursor"], limit=2)
    third = inbox.list(cursor=second["nextCursor"], limit=2)

    assert len(first["items"]) == 2
    assert len(second["items"]) == 2
    assert len(third["items"]) == 1

    assert [e["id"] for e in first["items"]] == submitted_ids[0:2]
    assert [e["id"] for e in second["items"]] == submitted_ids[2:4]
    assert [e["id"] for e in third["items"]] == submitted_ids[4:5]

    repeat_first = inbox.list(limit=2)
    assert [e["id"] for e in repeat_first["items"]] == submitted_ids[0:2]


def test_multiple_orchestrators_can_read_independently():
    inbox = CManageInbox()
    submitted_ids = [inbox.submit(_action(t))["id"] for t in ["a", "b", "c"]]

    cursor_a = None
    cursor_b = None

    page_a1 = inbox.list(cursor=cursor_a, limit=2)
    cursor_a = page_a1["nextCursor"]
    page_b1 = inbox.list(cursor=cursor_b, limit=1)
    cursor_b = page_b1["nextCursor"]

    page_a2 = inbox.list(cursor=cursor_a, limit=2)
    page_b2 = inbox.list(cursor=cursor_b, limit=2)

    a_ids = [e["id"] for e in page_a1["items"] + page_a2["items"]]
    b_ids = [e["id"] for e in page_b1["items"] + page_b2["items"]]

    assert a_ids == submitted_ids
    assert b_ids == submitted_ids


def test_invalid_cursor_raises_value_error():
    inbox = CManageInbox()
    inbox.submit(_action("alpha"))
    with pytest.raises(ValueError, match="invalid cursor"):
        inbox.list(cursor="not-a-valid-cursor")


def test_new_inbox_has_no_persistence():
    inbox = CManageInbox()
    inbox.submit(_action("alpha"))

    fresh = CManageInbox()
    listed = fresh.list()
    assert listed["items"] == []
    assert listed["nextCursor"] is None


def _read_observations(path, expected_count, timeout=1.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            lines = path.read_text().splitlines()
            if len(lines) >= expected_count:
                return [json.loads(line) for line in lines]
        time.sleep(0.01)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_emit_is_optional(tmp_path):
    target = tmp_path / "observations.jsonl"
    inbox = CManageInbox()
    inbox.submit(_action("alpha"))
    assert not target.exists()


def test_emit_on_submit_and_claim(tmp_path):
    target = tmp_path / "observations.jsonl"
    inbox = CManageInbox(emit_target=str(target))
    env = inbox.submit(_action("alpha", payload={"x": 1}))
    claimed = inbox.claim(env["id"])

    assert claimed is not None

    observations = _read_observations(target, expected_count=2)
    assert len(observations) == 2
    assert {obs["event"] for obs in observations} == {"intent.offered", "intent.claimed"}
    assert all(obs["envelope"]["id"] == env["id"] for obs in observations)


def test_parse_emit_target():
    assert parse_emit_target(["--emit", "target-path"]) == "target-path"
    assert parse_emit_target(["--other", "x"]) is None
    with pytest.raises(ValueError, match="--emit requires a target"):
        parse_emit_target(["--emit"])
    with pytest.raises(ValueError, match="multiple --emit targets"):
        parse_emit_target(["--emit", "a", "--emit", "b"])
