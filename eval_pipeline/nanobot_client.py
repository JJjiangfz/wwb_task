from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

from eval_pipeline.models import CaseResult, TestCase
from eval_pipeline.trace import normalize_messages, save_trace


class NanoBotClient:
    def __init__(
        self,
        *,
        runtime_config_path: str | Path,
        output_dir: str | Path,
        max_turns: int,
        timeout_seconds: float | None,
    ) -> None:
        self.runtime_config_path = Path(runtime_config_path).expanduser().resolve()
        self.output_dir = Path(output_dir).expanduser().resolve()
        self.max_turns = max_turns
        self.timeout_seconds = timeout_seconds

    def run_case(self, case: TestCase) -> CaseResult:
        started_at = time.perf_counter()
        workspace_path = self.output_dir / "workspaces" / case.workspace_name
        trace_path = self.output_dir / "traces" / f"{case.case_id}.json"
        workspace_path.mkdir(parents=True, exist_ok=True)

        try:
            run_payload = asyncio.run(self._run_nanobot(case, workspace_path))
            messages, warning = normalize_messages(
                run_payload["messages"],
                case.instruction,
                run_payload["content"],
            )
            save_trace(trace_path, messages)
            elapsed = time.perf_counter() - started_at
            return CaseResult(
                case_id=case.case_id,
                status="success",
                instruction=case.instruction,
                skill=case.skill,
                explain=case.explain,
                workspace_path=workspace_path,
                trace_path=trace_path,
                session_key=case.session_key,
                elapsed_seconds=elapsed,
                tools_used=run_payload["tools_used"],
                truncated=run_payload["truncated"],
                warning=warning,
            )
        except Exception as exc:
            elapsed = time.perf_counter() - started_at
            fallback = [
                {"role": "user", "content": case.instruction},
                {"role": "assistant", "content": f"Evaluation failed: {exc!r}"},
            ]
            save_trace(trace_path, fallback)
            return CaseResult(
                case_id=case.case_id,
                status="error",
                instruction=case.instruction,
                skill=case.skill,
                explain=case.explain,
                workspace_path=workspace_path,
                trace_path=trace_path,
                session_key=case.session_key,
                elapsed_seconds=elapsed,
                error=repr(exc),
            )

    async def _run_nanobot(self, case: TestCase, workspace_path: Path) -> dict[str, Any]:
        try:
            from nanobot import Nanobot
            from nanobot.agent import AgentHook, AgentHookContext
        except ImportError as exc:
            raise RuntimeError(
                "NanoBot is not installed. Run: pip install -e third_party/nanobot"
            ) from exc

        max_turns = self.max_turns

        class IterationLimitHook(AgentHook):
            def __init__(self) -> None:
                super().__init__()
                self.max_iteration_seen = 0

            async def after_iteration(self, context: AgentHookContext) -> None:
                self.max_iteration_seen = max(self.max_iteration_seen, int(context.iteration))

        hook = IterationLimitHook()
        bot = Nanobot.from_config(
            config_path=self.runtime_config_path,
            workspace=workspace_path,
        )
        coro = bot.run(case.instruction, session_key=case.session_key, hooks=[hook])
        if self.timeout_seconds is None:
            result = await coro
        else:
            result = await asyncio.wait_for(coro, timeout=self.timeout_seconds)

        return {
            "content": result.content,
            "tools_used": list(result.tools_used),
            "messages": list(result.messages),
            "truncated": hook.max_iteration_seen >= max_turns,
        }
