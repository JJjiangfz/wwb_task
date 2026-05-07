from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Protocol

from eval_pipeline.models import CaseResult, TestCase
from eval_pipeline.trace import save_summary


class CaseClient(Protocol):
    def run_case(self, case: TestCase) -> CaseResult:
        ...


class EvaluationRunner:
    def __init__(self, *, client: CaseClient, concurrency: int, output_dir: str | Path) -> None:
        if concurrency < 1:
            raise ValueError("concurrency must be >= 1")
        if concurrency > 32:
            raise ValueError("concurrency must be <= 32")
        self.client = client
        self.concurrency = concurrency
        self.output_dir = Path(output_dir).expanduser().resolve()

    def run(self, cases: list[TestCase]) -> list[CaseResult]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        results_by_id: dict[str, CaseResult] = {}

        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            futures = {executor.submit(self.client.run_case, case): case for case in cases}
            for future in as_completed(futures):
                case = futures[future]
                try:
                    result = future.result()
                except Exception as exc:
                    raise RuntimeError(f"client.run_case leaked an exception for {case.case_id}") from exc
                results_by_id[case.case_id] = result

        ordered = [results_by_id[case.case_id] for case in cases]
        save_summary(self.output_dir / "summary.json", [result.to_json_dict() for result in ordered])
        return ordered
