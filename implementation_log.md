# 评测流水线实现精简日志

1. 阅读任务说明
   - 阅读 `task_intro.md`，确认任务目标是实现面向 NanoBot/OpenClaw 智能体的自动化评测流水线。
   - 明确核心要求：并发评测、case 隔离、JSON 数据集输入、完整轨迹保存、最大轮数限制、支持 API key 模型服务和本地 vLLM。

2. 准备 NanoBot 环境
   - 克隆 NanoBot 到 `third_party/nanobot`。
   - 基于 Python 3.10 创建并使用 `nanobot` conda 环境。
   - 调整 NanoBot 本地依赖以适配 Python 3.10，并安装为 editable 包。

3. 实现评测流水线
   - 创建 `eval_pipeline` 包。
   - 实现数据集加载和校验，支持字段 `instruction`、`skill`、`explain`。
   - 实现每个 testcase 独立 workspace 和 session key。
   - 使用 NanoBot SDK 启动 agent，并对每个 case 执行指令。
   - 实现线程池并发 runner，可配置 `--concurrency`。
   - 实现最大轮数控制，默认按任务要求设置为 20。
   - 保存 OpenAI-style message trace，使用 `indent=4`。
   - 生成每轮评测的 `summary.json`。

4. 增加配置和样例
   - 添加 `configs/nanobot_openrouter.example.json`，支持 API key 访问 OpenRouter。
   - 添加 `configs/nanobot_vllm.example.json`，支持本地 OpenAI-compatible vLLM。
   - 添加 `data/sample_cases.json`，用于端到端 smoke test。
   - 编写 README，说明安装、运行和输出结构。

5. 编写并运行测试
   - 增加数据集、trace 和 runner 相关单元测试。
   - 运行 `pytest`，结果为 `7 passed`。
   - 运行 `pip check`，确认依赖无破损。

6. API 模式验证
   - 使用 OpenRouter free API key 验证 API key 模式。
   - 跑通样例评测，输出目录为 `outputs/run_openrouter_free`。
   - 生成完整 trace 和 summary，确认 API 模式可用。

7. 本地 vLLM 模式部署
   - 安装 vLLM 及 CUDA 12.8 兼容版本依赖。
   - 下载 `Qwen/Qwen3-8B` 到 `models/Qwen3-8B`。
   - 使用 GPU 6，即 `NVIDIA GeForce RTX 4090`，启动本地 vLLM 服务。
   - 由于机器系统 `nvcc` 为 CUDA 11.5，禁用 vLLM V1 和 FlashInfer sampler，改用 XFormers/eager 路径。
   - 启动服务地址为 `http://127.0.0.1:8000/v1`，served model name 为 `Qwen/Qwen3-8B`。

8. 本地 vLLM 评测验证
   - 开启 vLLM `auto tool choice`，并使用 `hermes` parser 解析 Qwen 输出的工具调用。
   - 调整 NanoBot 本地 vLLM 配置：`maxTokens=1024`，`contextWindowTokens=8192`。
   - 跑通本地 vLLM 评测，输出目录为 `outputs/run_vllm_local_verified`。
   - 三个样例 case 均成功执行，并产生真实工具调用轨迹。

9. 最终结果
   - 评测流水线主体已完成。
   - 已支持 API key 模型服务和本地 vLLM 两种模式。
   - 已验证输出包括独立 workspace、完整 trace 和 summary。
   - 当前本地 vLLM 服务仍可用于继续运行评测任务。
