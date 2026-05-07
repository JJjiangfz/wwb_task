# NanoBot Evaluation Pipeline

Python pipeline for running many NanoBot agent evaluation cases concurrently while keeping each case in an isolated workspace and session.

## Setup

This workspace uses a local Python 3.10-compatible NanoBot checkout under
`third_party/nanobot`.

```bash
conda activate nanobot
pip install -e third_party/nanobot
pip install -e ".[dev]"
```

The NanoBot source is kept under `third_party/nanobot` so the SDK, config schema, hooks, and built-in skills can be inspected locally. The evaluation pipeline still calls NanoBot through its public Python SDK.

## vLLM Example

Start a local OpenAI-compatible vLLM server:

```bash
CUDA_VISIBLE_DEVICES=6 \
VLLM_WORKER_MULTIPROC_METHOD=spawn \
VLLM_USE_V1=0 \
VLLM_USE_FLASHINFER_SAMPLER=0 \
VLLM_ATTENTION_BACKEND=XFORMERS \
vllm serve models/Qwen3-8B \
  --served-model-name Qwen/Qwen3-8B \
  --host 127.0.0.1 \
  --port 8000 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.65 \
  --trust-remote-code \
  --enforce-eager \
  --enable-auto-tool-choice \
  --tool-call-parser hermes \
  --reasoning-parser qwen3
```

Run the sample dataset:

```bash
python -m eval_pipeline run \
  --dataset data/sample_cases.json \
  --config configs/nanobot_vllm.example.json \
  --output-dir outputs/run_qwen3 \
  --concurrency 1 \
  --max-turns 20
```

On this machine, the command above avoids the system CUDA 11.5 `nvcc`
FlashInfer JIT path while using Torch CUDA 12.8 wheels. Increase concurrency
only after confirming available GPU memory and vLLM throughput.

Use `--dry-run` to validate the dataset and print the planned isolated workspaces without calling NanoBot.

## OpenRouter Example

The OpenRouter config uses the free model route by default:

```json
"model": "openrouter/free"
```

OpenRouter still requires an API key for authentication. To avoid exporting it
in every shell, create a local `.env` file:

```bash
cp .env.example .env
# then edit .env and set OPENROUTER_API_KEY
```

Run the API-backed evaluation:

```bash
python -m eval_pipeline run \
  --dataset data/eval_cases.json \
  --config configs/nanobot_openrouter.example.json \
  --output-dir outputs/run_openrouter_eval \
  --concurrency 1 \
  --max-turns 20 \
  --timeout-seconds 300
```

## Outputs

Each case gets:

- `outputs/<run>/workspaces/<case_id>_workspace/`
- `outputs/<run>/traces/<case_id>.json`
- one row in `outputs/<run>/summary.json`

Trace files are saved as OpenAI-style message arrays with `indent=4`. If NanoBot returns no SDK messages, the pipeline saves a minimal fallback trace and marks the result with a warning in `summary.json`.

## Dataset Format

Input JSON is a list of cases:

```json
[
    {
        "instruction": "Use the weather skill to tell me the current weather in Tokyo.",
        "skill": "weather",
        "explain": "Checks whether the requested skill is used."
    }
]
```

The loader keeps the dataset schema isolated from execution code. Future field changes should be handled in `eval_pipeline/models.py` and `eval_pipeline/dataset.py`.
