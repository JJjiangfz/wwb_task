from __future__ import annotations

import json
from pathlib import Path
from typing import Any


OPENAI_ROLES = {"system", "user", "assistant", "tool"}


def normalize_messages(messages: list[dict[str, Any]] | None, instruction: str, final_content: str) -> tuple[list[dict[str, Any]], str | None]:
    if messages:
        normalized = [_normalize_message(message) for message in messages if isinstance(message, dict)]
        if normalized:
            return normalized, None

    fallback = [
        {"role": "user", "content": instruction},
        {"role": "assistant", "content": final_content},
    ]
    return fallback, "NanoBot returned no SDK message trace; saved minimal fallback trace."


def save_trace(path: str | Path, messages: list[dict[str, Any]]) -> None:
    trace_path = Path(path).expanduser().resolve()
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    with trace_path.open("w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=4)
        f.write("\n")


def save_summary(path: str | Path, rows: list[dict[str, Any]]) -> None:
    summary_path = Path(path).expanduser().resolve()
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=4)
        f.write("\n")


def _normalize_message(message: dict[str, Any]) -> dict[str, Any]:
    role = message.get("role")
    if not isinstance(role, str) or role not in OPENAI_ROLES:
        role = "assistant"

    normalized: dict[str, Any] = {"role": role}
    content = message.get("content", "")
    normalized["content"] = _jsonable(content)

    for key, value in message.items():
        if key in {"role", "content"}:
            continue
        normalized[key] = _jsonable(value)
    return normalized


def _jsonable(value: Any) -> Any:
    try:
        json.dumps(value, ensure_ascii=False)
        return value
    except TypeError:
        return repr(value)
