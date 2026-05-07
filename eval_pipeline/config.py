from __future__ import annotations

import json
import os
from pathlib import Path


def prepare_runtime_config(config_path: str | Path, output_dir: str | Path, max_turns: int) -> Path:
    load_dotenv()

    source = Path(config_path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"NanoBot config not found: {source}")

    with source.open("r", encoding="utf-8") as f:
        config = json.load(f)

    if not isinstance(config, dict):
        raise ValueError("NanoBot config root must be a JSON object")

    agents = config.setdefault("agents", {})
    if not isinstance(agents, dict):
        raise ValueError("NanoBot config field 'agents' must be an object")
    defaults = agents.setdefault("defaults", {})
    if not isinstance(defaults, dict):
        raise ValueError("NanoBot config field 'agents.defaults' must be an object")

    defaults["maxToolIterations"] = max_turns

    runtime_dir = Path(output_dir).expanduser().resolve()
    runtime_dir.mkdir(parents=True, exist_ok=True)
    runtime_config = runtime_dir / "nanobot_runtime_config.json"
    with runtime_config.open("w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)
        f.write("\n")
    return runtime_config


def load_dotenv(path: str | Path = ".env") -> None:
    env_path = Path(path).expanduser()
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
