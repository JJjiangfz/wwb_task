import json

import pytest

from eval_pipeline.dataset import load_dataset


def test_load_dataset_generates_stable_case_ids(tmp_path):
    path = tmp_path / "cases.json"
    path.write_text(
        json.dumps(
            [
                {
                    "instruction": "Use the weather skill.",
                    "skill": "weather",
                    "explain": "Smoke test.",
                }
            ]
        ),
        encoding="utf-8",
    )

    cases = load_dataset(path)

    assert cases[0].case_id == "testcase_0001"
    assert cases[0].workspace_name == "testcase_0001_workspace"
    assert cases[0].session_key == "eval:testcase_0001"


def test_load_dataset_rejects_missing_fields(tmp_path):
    path = tmp_path / "cases.json"
    path.write_text(json.dumps([{"instruction": "hi"}]), encoding="utf-8")

    with pytest.raises(ValueError, match="missing required"):
        load_dataset(path)


def test_load_dataset_rejects_duplicate_ids(tmp_path):
    path = tmp_path / "cases.json"
    payload = [
        {"case_id": "same", "instruction": "a", "skill": "weather", "explain": "x"},
        {"case_id": "same", "instruction": "b", "skill": "weather", "explain": "y"},
    ]
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate case_id"):
        load_dataset(path)
