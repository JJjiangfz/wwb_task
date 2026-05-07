# NanoBot Evaluation Pipeline

这是一个 Python 评测流水线，用于并发运行多条 NanoBot 智能体评测用例，并为每条用例保持独立的工作目录和会话。

## 环境配置

本工作区使用位于 `third_party/nanobot` 的本地 NanoBot 源码版本，该版本兼容 Python 3.10。

```bash
conda activate nanobot
pip install -e third_party/nanobot
pip install -e ".[dev]"
```

NanoBot 源码保存在 `third_party/nanobot` 下，便于在本地查看 SDK、配置 schema、hooks 和内置 skills。评测流水线仍然通过 NanoBot 公开的 Python SDK 调用 NanoBot。

## vLLM 示例

启动一个兼容 OpenAI API 的本地 vLLM 服务：

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

运行示例数据集：

```bash
python -m eval_pipeline run \
  --dataset data/sample_cases.json \
  --config configs/nanobot_vllm.example.json \
  --output-dir outputs/run_qwen3 \
  --concurrency 1 \
  --max-turns 20
```

在这台机器上，上面的命令会避开系统 CUDA 11.5 `nvcc` 的 FlashInfer JIT 路径，同时使用 Torch CUDA 12.8 wheels。只有在确认 GPU 显存余量和 vLLM 吞吐能力之后，再提高并发数。

可以使用 `--dry-run` 验证数据集，并打印计划创建的独立工作目录，而不会实际调用 NanoBot。

## OpenRouter 示例

OpenRouter 配置默认使用免费模型路由：

```json
"model": "openrouter/free"
```

OpenRouter 仍然需要 API key 进行身份认证。为了避免在每个 shell 中重复 export，可以创建本地 `.env` 文件：

```bash
cp .env.example .env
# then edit .env and set OPENROUTER_API_KEY
```

运行由 API 支持的评测：

```bash
python -m eval_pipeline run \
  --dataset data/eval_cases.json \
  --config configs/nanobot_openrouter.example.json \
  --output-dir outputs/run_openrouter_eval \
  --concurrency 1 \
  --max-turns 20 \
  --timeout-seconds 300
```

## 输出

每条用例会生成：

- `outputs/<run>/workspaces/<case_id>_workspace/`
- `outputs/<run>/traces/<case_id>.json`
- `outputs/<run>/summary.json` 中的一行记录

trace 文件会以 OpenAI 风格的消息数组形式保存，并使用 `indent=4`。如果 NanoBot 没有返回 SDK messages，流水线会保存一个最小 fallback trace，并在 `summary.json` 中用 warning 标记该结果。

## 数据集格式

输入 JSON 是一个用例列表：

```json
[
    {
        "instruction": "Use the weather skill to tell me the current weather in Tokyo.",
        "skill": "weather",
        "explain": "Checks whether the requested skill is used."
    }
]
```

加载器会让数据集 schema 和执行代码保持隔离。未来如果需要调整字段，应在 `eval_pipeline/models.py` 和 `eval_pipeline/dataset.py` 中处理。
