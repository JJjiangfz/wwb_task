from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar


@dataclass(frozen=True)
class TestCase:
    __test__: ClassVar[bool] = False

    instruction: str
    skill: str
    explain: str
    case_id: str
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: dict[str, Any], index: int) -> "TestCase":
        required = ("instruction", "skill", "explain")
        missing = [key for key in required if key not in payload]
        if missing:
            raise ValueError(f"case #{index + 1} missing required field(s): {', '.join(missing)}")

        instruction = _require_text(payload["instruction"], "instruction", index)
        skill = _require_text(payload["skill"], "skill", index)
        explain = _require_text(payload["explain"], "explain", index)
        case_id = payload.get("case_id") or payload.get("id") or f"testcase_{index + 1:04d}"
        case_id = _normalize_case_id(str(case_id), index)

        return cls(
            instruction=instruction,
            skill=skill,
            explain=explain,
            case_id=case_id,
            raw=dict(payload),
        )

    @property
    def workspace_name(self) -> str:
        return f"{self.case_id}_workspace"

    @property
    def session_key(self) -> str:
        return f"eval:{self.case_id}"


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    status: str
    instruction: str
    skill: str
    explain: str
    workspace_path: Path
    trace_path: Path
    session_key: str
    elapsed_seconds: float
    tools_used: list[str] = field(default_factory=list)
    truncated: bool = False
    warning: str | None = None
    error: str | None = None

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "status": self.status,
            "instruction": self.instruction,
            "skill": self.skill,
            "explain": self.explain,
            "workspace_path": str(self.workspace_path),
            "trace_path": str(self.trace_path),
            "session_key": self.session_key,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
            "tools_used": list(self.tools_used),
            "truncated": self.truncated,
            "warning": self.warning,
            "error": self.error,
        }


def _require_text(value: Any, field_name: str, index: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"case #{index + 1} field {field_name!r} must be a non-empty string")
    return value.strip()


def _normalize_case_id(value: str, index: int) -> str:
    normalized = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in value.strip())
    normalized = normalized.strip("_")
    if not normalized:
        raise ValueError(f"case #{index + 1} has an empty case_id")
    return normalized
