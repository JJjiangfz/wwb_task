from pathlib import Path

from eval_pipeline.models import CaseResult, TestCase
from eval_pipeline.runner import EvaluationRunner


class FakeClient:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def run_case(self, case: TestCase) -> CaseResult:
        trace_path = self.output_dir / "traces" / f"{case.case_id}.json"
        workspace_path = self.output_dir / "workspaces" / case.workspace_name
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        workspace_path.mkdir(parents=True, exist_ok=True)
        trace_path.write_text('[{"role": "assistant", "content": "ok"}]\n', encoding="utf-8")
        return CaseResult(
            case_id=case.case_id,
            status="success",
            instruction=case.instruction,
            skill=case.skill,
            explain=case.explain,
            workspace_path=workspace_path,
            trace_path=trace_path,
            session_key=case.session_key,
            elapsed_seconds=0.1,
        )


def test_runner_preserves_dataset_order_and_writes_summary(tmp_path):
    cases = [
        TestCase("first", "weather", "x", "a"),
        TestCase("second", "weather", "y", "b"),
    ]
    runner = EvaluationRunner(client=FakeClient(tmp_path), concurrency=2, output_dir=tmp_path)

    results = runner.run(cases)

    assert [result.case_id for result in results] == ["a", "b"]
    assert (tmp_path / "summary.json").exists()
