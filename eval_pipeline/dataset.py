from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from eval_pipeline.models import TestCase


def load_dataset(path: str | Path) -> list[TestCase]:
    dataset_path = Path(path).expanduser().resolve()
    with dataset_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    if not isinstance(payload, list):
        raise ValueError("dataset root must be a JSON list")

    cases = [TestCase.from_mapping(_require_object(item, index), index) for index, item in enumerate(payload)]
    _ensure_unique_case_ids(cases)
    return cases


def _require_object(item: Any, index: int) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise ValueError(f"case #{index + 1} must be a JSON object")
    return item


def _ensure_unique_case_ids(cases: list[TestCase]) -> None:
    seen: set[str] = set()
    duplicates: list[str] = []
    for case in cases:
        if case.case_id in seen:
            duplicates.append(case.case_id)
        seen.add(case.case_id)
    if duplicates:
        joined = ", ".join(sorted(set(duplicates)))
        raise ValueError(f"duplicate case_id value(s): {joined}")
