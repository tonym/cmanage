# cmanage

**Overview**
CManage Phase 1 (Gate B) provides an in-memory, append-only action inbox with cursor-based listing. It is headless and JSON-first.

**Install**
1. `python -m venv .venv`
2. `source .venv/bin/activate` (macOS/Linux) or `.\\.venv\\Scripts\\activate` (Windows)
3. `python -m pip install -U pip`
4. `python -m pip install -e ".[test]"`

**Tests**
1. `pytest`
