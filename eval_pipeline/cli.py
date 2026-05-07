from __future__ import annotations

import argparse
from pathlib import Path

from eval_pipeline.config import prepare_runtime_config
from eval_pipeline.dataset import load_dataset
from eval_pipeline.nanobot_client import NanoBotClient
from eval_pipeline.runner import EvaluationRunner


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        return _run(args)
    parser.print_help()
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nanobot-eval")
    subparsers = parser.add_subparsers(dest="command")

    run = subparsers.add_parser("run", help="run an evaluation dataset")
    run.add_argument("--dataset", required=True, help="path to dataset JSON")
    run.add_argument("--config", required=True, help="path to NanoBot config JSON")
    run.add_argument("--output-dir", default="outputs/run", help="directory for workspaces, traces, and summary")
    run.add_argument("--concurrency", type=int, default=16, help="number of concurrent cases, 1-32")
    run.add_argument("--max-turns", type=int, default=20, help="NanoBot max tool iterations per case")
    run.add_argument("--timeout-seconds", type=float, default=None, help="optional per-case wall-clock timeout")
    run.add_argument("--dry-run", action="store_true", help="validate inputs and print planned case isolation only")
    return parser


def _run(args: argparse.Namespace) -> int:
    if args.max_turns < 1:
        raise SystemExit("--max-turns must be >= 1")

    cases = load_dataset(args.dataset)
    output_dir = Path(args.output_dir).expanduser().resolve()

    if args.dry_run:
        print(f"Loaded {len(cases)} case(s).")
        for case in cases:
            workspace = output_dir / "workspaces" / case.workspace_name
            print(f"{case.case_id}: session={case.session_key} workspace={workspace}")
        return 0

    runtime_config = prepare_runtime_config(args.config, output_dir, args.max_turns)
    client = NanoBotClient(
        runtime_config_path=runtime_config,
        output_dir=output_dir,
        max_turns=args.max_turns,
        timeout_seconds=args.timeout_seconds,
    )
    runner = EvaluationRunner(client=client, concurrency=args.concurrency, output_dir=output_dir)
    results = runner.run(cases)
    ok = sum(1 for result in results if result.status == "success")
    failed = len(results) - ok
    print(f"Finished {len(results)} case(s): success={ok}, error={failed}")
    print(f"Summary: {output_dir / 'summary.json'}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
