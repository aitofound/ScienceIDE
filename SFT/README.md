# SFT

独立的工具轨迹 LoRA SFT，训练逻辑集中在 **`train.py`**。
模型通过 `--model` 传入，模型类型和聊天模板由 ms-swift 根据模型元数据识别，
也可通过 `--model-type`、`--template` 显式指定。代码不绑定具体模型或模型系列。
可用模型、模板、加速算子的范围以所安装的 ms-swift 及其依赖为准。

流程：JSONL 轨迹 → 数据与标签检查 → LoRA 训练 → adapter checkpoint。
整个目录可以复制到其他仓库，不依赖原仓库的 Python 模块、实验路径或集群地址。

## 文件

| 文件 | 用途 |
| --- | --- |
| `train.py` | `prepare` 数据准备与 `train` 训练；全部 Python 训练实现 |
| `requirements.txt` | 核心依赖版本 |
| `zero3.json` | 可选的 DeepSpeed ZeRO-3 配置 |
| `sample_data/*.jsonl` | 人工编写的 4 条训练、2 条验证样本，仅用于检查流程 |
| `test_train.py` | 标签、任务分区、通用参数和分布式采样的回归检查 |

## 安装

以下命令均在本目录运行，使用 Python 3.11。先安装与驱动兼容的 PyTorch；
下面提供 CUDA 12.4 的依赖安装示例：

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install torch==2.6.0 torchvision==0.21.0 \
  --index-url https://download.pytorch.org/whl/cu124
DS_BUILD_OPS=0 python -m pip install -r requirements.txt
python -m pip check
```

Liger 用于降低长序列 loss 的显存开销；模型不支持该算子时使用 `--no-liger`。
额外的模型架构依赖按所选模型安装。例如需要线性注意力算子时，可安装
`flash-linear-attention==0.4.2`。

脚本包含 ms-swift 4.5.3 分布式采样尾部修正，以及 PyTorch 2.6 / DeepSpeed 0.19.6
的进程内导入兼容处理，不修改已安装的包文件。依赖升级后应重新验证这些行为。

## 最小示例

将 `MODEL_PATH` 换为本地模型目录，也可以传入 Hugging Face 模型 ID。
使用远端模型时可加 `--revision` 固定 commit；准备和训练使用相同 revision。

```bash
export MODEL_PATH=/path/to/model

# 只加载 tokenizer/config，检查并转换数据，不加载训练权重。
CUDA_VISIBLE_DEVICES='' python train.py prepare \
  --model "$MODEL_PATH" \
  --train-file sample_data/train.jsonl \
  --validation-file sample_data/validation.jsonl \
  --max-length 4096 --output-dir data/sft

# 检查数据哈希和 batch 配置，打印训练参数；不加载模型、不训练。
python train.py train --model "$MODEL_PATH" --data-dir data/sft \
  --global-batch-size 2 --max-steps 2 --output-dir outputs/smoke --dry-run

# 单 GPU，两步优化，运行验证并保存 checkpoint-2。
CUDA_VISIBLE_DEVICES=0 python train.py train \
  --model "$MODEL_PATH" --data-dir data/sft \
  --global-batch-size 2 --max-steps 2 --output-dir outputs/smoke
```

自动识别不适用时，为准备命令补充 `--model-type "$MODEL_TYPE" --template "$CHAT_TEMPLATE"`，
其中变量值为所选模型对应的 ms-swift 注册类型。训练默认复用数据准备时解析出的类型和模板。

默认关闭思考模式并启用非思考前缀；可通过 `--enable-thinking`、
`--no-add-non-thinking-prefix` 调整。准备和训练必须保持这些参数一致。
多模态模型默认冻结视觉编码器和对齐模块，可通过 `--no-freeze-vit`、
`--no-freeze-aligner` 调整。这些选项的具体行为由对应模型和模板实现决定。

输出是 `outputs/smoke/checkpoint-2/` 下的 LoRA adapter，使用时需要原始 base model。
checkpoint 同时保存 optimizer/scheduler 状态。`sft_config.json` 保存启动配置，
成功返回后写入 `sft_run.json`。加 `--report-to tensorboard` 可记录本地训练曲线。

4096 是短上下文示例默认值。实际轨迹通常更长，需要按目标模型重新准备数据，
再根据 GPU 容量选择上下文和并行配置。小样本 smoke 不代表完整数据的显存需求。

## 换成自己的训练数据

输入为每行一个 JSON 对象。支持两种结构，不接受原始 ATIF 文件：

```json
{"task_name":"task-a","prompt":[{"role":"user","content":"Fix the function."}],"completion":[{"role":"assistant","content":"The fix is ..."}],"tools":[]}
```

```json
{"task_name":"task-b","messages":[{"role":"user","content":"Fix the function.","loss":false},{"role":"assistant","content":"An earlier failed attempt.","loss":false},{"role":"user","content":"The test still fails.","loss":false},{"role":"assistant","content":"The corrected implementation.","loss":true}],"tools":[]}
```

- `prompt` 整段不监督；`completion` 中只监督 assistant/tool_call，保留显式 `loss=false`。
- `messages` 中未写 `loss` 时，默认监督 assistant/tool_call；历史窗口或失败动作应显式标记。
- system/user/tool/tool_response 不参与 loss。显式给这些消息设置 `loss=true` 会报错。
- 原生 OpenAI `assistant.tool_calls` 转换为 ms-swift 的 `tool_call`；`tools` 可为数组或 JSON 字符串。
- 工具调用须有匹配的 schema；只支持文本消息。片段可以以工具反馈结束，
  但须包含至少一个有效的 assistant/tool_call 监督目标。
- `task_name` 用于检查跨分区泄漏。同一任务的多个片段/尝试须留在同一分区。
  旧消息数据未包含此字段时，可把 `train.audit.jsonl`、`validation.audit.jsonl`
  放在对应数据文件旁，脚本读取其中 `status=kept` 的任务映射。

```bash
python train.py prepare --model "$MODEL_PATH" \
  --train-file /path/to/train.jsonl --validation-file /path/to/validation.jsonl \
  --max-length 32768 --output-dir data/trajectories
```

准备阶段使用真实模板逐条计算 token 数，检查非空监督目标，并用人工哨兵验证
数据预处理器和模板保留 loss mask。超长样本默认报错；显式加 `--drop-overlength`
才会整条排除并记入 audit，不截断工具调用。任务重叠会报错，不自动随机切分，
也不读取 test 分区。失败准备目录没有 `report.json`，不能用于训练；重试时选择新目录。

当前准备报告格式为 v2，记录实际解析出的类型、模板及模板选项；旧版数据需重新执行 `prepare`。
脚本保留输入的监督标记，不自动判断轨迹是否成功，不重新执行工具命令。
verifier 筛选、协议转换和坏动作标注应在生成输入数据时完成。

## 多 GPU 和多节点

下面使用 LoRA rank 32、alpha 64、LR 2e-5、3 epochs、global batch 64。
完整数据训练前，可用独立输出目录和 `--max-steps 2` 检查训练流程。

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 torchrun --standalone --nproc_per_node=4 train.py train \
  --model "$MODEL_PATH" --data-dir data/trajectories \
  --epochs 3 --global-batch-size 64 \
  --report-to tensorboard --output-dir outputs/lora
```

多节点由集群提供 `NNODES`、`NODE_RANK`、`MASTER_ADDR`、`MASTER_PORT` 和 `GPUS_PER_NODE`。
各节点使用一致的工作目录、模型、数据和输出路径，输出需使用共享存储。

```bash
torchrun --nnodes="$NNODES" --nproc_per_node="$GPUS_PER_NODE" --node_rank="$NODE_RANK" \
  --master_addr="$MASTER_ADDR" --master_port="$MASTER_PORT" \
  train.py train --model "$MODEL_PATH" --data-dir data/trajectories \
  --epochs 3 --global-batch-size 64 --deepspeed zero3.json --output-dir outputs/distributed
```

默认 SP=1。仅在所选架构和后端支持序列并行时加 `--sequence-parallel-size`。
脚本检查 SP 整除总卡数、每节点卡数和 KV head 数，并拒绝配置中已声明的非注意力层类型；
这些检查不能替代具体架构的后端支持验证。

`global_batch = (world_size / SP) × per_device_batch × gradient_accumulation`

例如 4 GPU、SP=1、每卡 batch=1 时累积 16 次；32 GPU、SP=4 时累积 8 次。
增加 DDP 卡数不会降低单条长轨迹的激活显存需求。

从中断 checkpoint 恢复时保持原命令参数，补上：

```bash
--resume-from-checkpoint outputs/lora/checkpoint-72
```

恢复会核对原配置和数据哈希。新实验使用新的输出目录，smoke adapter 不会自动带入正式训练。

## 整合范围和验证

训练后端统一为 ms-swift，保留原流程中的 assistant/completion 监督、任务分区检查、
真实 token 审计、LoRA 参数、分布式 batch 计算和兼容处理。原始轨迹采集、专用数据修复、
实验调度及 benchmark 评估留在上游。此脚本实现 SFT，不包含在线 RL 优化器。

```bash
python -m unittest discover -s . -p 'test_*.py' -v
```

18 项标准库回归测试覆盖监督标记、分区泄漏、超长处理、通用模型参数与分布式配置。
本地随机小模型用于检查真实模板、CPU 优化、验证和 checkpoint 保存；多节点 GPU、
NCCL/ZeRO-3 及不同模型架构需要在对应环境验证。流程检查不代表实际能力提升。
