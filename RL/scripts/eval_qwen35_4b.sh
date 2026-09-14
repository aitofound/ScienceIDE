#!/usr/bin/env bash
# Evaluate a Qwen3.5-4B GRPO checkpoint on the ScienceIDE RL repair tasks. No training.
#
# `val_only=True` returns after the initial validation, so no optimizer step runs.
# `EVAL_BASE=True` scores the untrained weights instead, leaving CKPT_PATH unused.

set -xeuo pipefail

export CUDA_DEVICE_MAX_CONNECTIONS=1
export VLLM_WORKER_MULTIPROC_METHOD=spawn
export VLLM_ALLREDUCE_USE_SYMM_MEM=0
# Expand allocator segments to reduce fragmentation from uneven activation sizes.
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export RAY_prestart_worker_first_driver=false
export RAY_num_workers_soft_limit=0
export RAY_memory_monitor_refresh_ms=0

# Keep Ray sockets within the Unix path limit and off the shared filesystem.
export TMPDIR=${SCIENCEIDE_TMPDIR:-/tmp}
mkdir -p "${TMPDIR}"

RL_ROOT=${RL_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}

# --- Model and data ---

# The 4B model leaves more activation memory for long contexts.
HF_MODEL_PATH=${HF_MODEL_PATH:-${PSRL_WORKSPACE:-}/models/Qwen3.5-4B}
# `L1` adds file, line, and defect note, `L2` drops the line, `L3` is the unhinted control.
HINT_LEVEL=${HINT_LEVEL:-L1}
# Built by `prepare/prepare_all.sh`, one directory per (env, category, tier).
DATA_DIR=${DATA_DIR:-${RL_ROOT}/scienceide_rl/data/mitgcm-biogeo/repair_easy}
# Score the untrained `HF_MODEL_PATH` weights instead of a checkpoint, which is the
# step-0 baseline for that model on this split.
EVAL_BASE=${EVAL_BASE:-True}
# Must be a `global_step_N` directory holding `actor/`, because `resume_path` asserts on
# that prefix to recover the step number. Unused when EVAL_BASE=True.
CKPT_PATH=${CKPT_PATH:-${RL_ROOT}/scienceide_rl/ckpts/scienceide_rl/<experiment>/global_step_30}
# Required by the config schema even though no training runs, and only read for it.
train_files=${DATA_DIR}/train/${HINT_LEVEL}.parquet
# Hinted eval, matching the training distribution. `L3` is the unhinted control, so
# its in-distribution eval set IS the unhinted one.
if [ "${HINT_LEVEL}" = "L3" ]; then
    val_files=${VAL_FILES:-${DATA_DIR}/eval/unhinted.parquet}
else
    val_files=${VAL_FILES:-${DATA_DIR}/eval/${HINT_LEVEL}.parquet}
fi

if [[ ! -d "${HF_MODEL_PATH}" ]]; then
    echo "ERROR: model directory not found: ${HF_MODEL_PATH}" >&2
    exit 1
fi
if [ "${EVAL_BASE}" != "True" ]; then
    if [[ ! -d "${CKPT_PATH}/actor" ]]; then
        echo "ERROR: checkpoint actor directory not found: ${CKPT_PATH}/actor" >&2
        echo "Pass CKPT_PATH=<...>/global_step_N pointing at a saved step, or EVAL_BASE=True." >&2
        exit 1
    fi
    if [[ "${CKPT_PATH}" != *global_step_* ]]; then
        echo "ERROR: CKPT_PATH must contain 'global_step_': ${CKPT_PATH}" >&2
        exit 1
    fi
fi
for f in "${train_files}" "${val_files}"; do
    if [[ ! -f "${f}" ]]; then
        echo "ERROR: parquet not found: ${f}" >&2
        echo "Build it: bash scienceide_rl/prepare/prepare_all.sh --repo <task-bank> --envs <env>" >&2
        exit 1
    fi
done

# --- Experiment ---
project_name=scienceide_rl
# The dataset and the scored step are part of the identity, so an eval never collides
# with the training run it came from. A base eval is tagged `base`, not `global_step_0`.
if [ "${EVAL_BASE}" = "True" ]; then
    eval_tag=base
else
    eval_tag=$(basename "${CKPT_PATH}")
fi
experiment_name=EVAL-Qwen35-4B-$(basename "${DATA_DIR}")-${HINT_LEVEL}-${eval_tag}
OUTPUT_DIR=${OUTPUT_DIR:-${RL_ROOT}/scienceide_rl}
# Deliberately NOT the training run's checkpoint directory, which `save_freq` could
# then write into. `resume_path` reads the checkpoint from `CKPT_PATH` instead.
CKPTS_DIR=${OUTPUT_DIR}/eval_ckpts/${project_name}/${experiment_name}
PSRL_LOG_DIR=${OUTPUT_DIR}/psrl_logs/${experiment_name}
mkdir -p "${CKPTS_DIR}" "${PSRL_LOG_DIR}"

# --- Agent loop config ---
agent_loop_config_path=${RL_ROOT}/scienceide_rl/config/agent_config.yaml
reward_path=${RL_ROOT}/scienceide_rl/reward.py

# --- Batch and sequence lengths ---

# Batch size controls requests and packed sequences per step.
train_batch_size=${TRAIN_BATCH_SIZE:-16}
rollout_N=8
# Keep prompts large enough for the longest task instruction.
max_prompt_length=2048
# Long terminal output requires most of the context budget.
max_response_length=${MAX_RESPONSE_LENGTH:-65536}
# NOTE(lhy): Must equal the training budget, never exceed it. This reaches terminus-2 as
# `max_input_tokens`, so any headroom is budget the agent spends, and TITO then hands the
# trainer a response longer than `max_response_length`.
max_model_len=$(( max_prompt_length + max_response_length ))
# The packing budget must cover the longest sequence without exceeding the window.
max_tokens_per_gpu=${MAX_TOKENS_PER_GPU:-${max_model_len}}
if (( max_tokens_per_gpu < max_model_len )); then
    echo "ERROR: max_tokens_per_gpu (${max_tokens_per_gpu}) must be >= max_model_len (${max_model_len})." >&2
    echo "rearrange_micro_batches requires max_token_len >= max_seq_len." >&2
    exit 1
fi
max_num_batched_tokens=${max_model_len}
# Bounded by the response budget, not by taste: at ~1104 response tokens per turn, 50
# turns already spends 55k of 65536. Raising it needs `max_response_length` raised too.
max_turns=${MAX_TURNS:-50}

# Nodes allowed to host agent loop workers, and therefore Docker containers. A node
# with a degraded daemon accepts actors and then hangs. Empty means every alive node.
AGENT_NODE_IPS=${AGENT_NODE_IPS:-}

# One worker per allowed node. Placement is round-robin, so more workers than nodes
# stacks them and multiplies the container count `max_concurrent_episodes` bounds.
if [ -n "${AGENT_NODE_IPS}" ]; then
    AGENT_LOOP_WORKERS=${AGENT_LOOP_WORKERS:-$(awk -F, '{print NF}' <<< "${AGENT_NODE_IPS}")}
else
    AGENT_LOOP_WORKERS=${AGENT_LOOP_WORKERS:-3}
fi

# Bound admitted sequences to the rollout engine's KV capacity.
# Revisit this value when batch size, context length, or engine count changes.
MAX_CONCURRENT_SEQS_PER_INSTANCE=${MAX_CONCURRENT_SEQS_PER_INSTANCE:-32}

# Keep HTTP concurrency above the KV-aware admission gate.
SERVER_MAX_CONCURRENCY=${SERVER_MAX_CONCURRENCY:-64}

# --- Chain-of-thought handling across turns ---

# `multi_thinking` needs the accumulating template, so derive the path here.
thinking_template=${thinking_template:-multi_thinking}
if [ "${thinking_template}" = "multi_thinking" ]; then
    chat_template_path=${RL_ROOT}/scienceide_rl/config/qwen35_acc_thinking.jinja2
    chat_template_arg="+gen_actor_rollout_ref.rollout.chat_template=${chat_template_path}"
else
    chat_template_arg=""
fi

# --- Deployment: 3 nodes x 8 GPU = 24 (8 generation + 16 training) ---

# Validation overlays training GPUs because generation and training consume all devices.
NNODES=3
NGPUS_PER_NODE=8

# Split generation GPUs across tensor-parallel rollout instances.
GEN_TP=2
GEN_PP=1
GEN_NNODES=1
GEN_NGPUS_PER_NODE=8
GEN_INSTANCES=$(((GEN_NNODES * GEN_NGPUS_PER_NODE) / (GEN_TP * GEN_PP)))
GEN_NGPUS_PER_NODE_PER_INSTANCE=$((GEN_TP * GEN_PP))

# Sequence parallelism keeps long-context activations within device memory.
TRAIN_SP=${TRAIN_SP:-4}
# Hybrid sharding keeps all-gathers within each training node.
TRAIN_FSDP=${TRAIN_FSDP:-8}
TRAIN_NNODES=2
TRAIN_NGPUS_PER_NODE=8

# Keep validation engines modest because they share training GPUs.
VAL_TP=2
VAL_PP=1
VAL_INSTANCES=2
VAL_NGPUS_PER_NODE_PER_INSTANCE=$((VAL_TP * VAL_PP))

# --- Checkpoint loading ---
# NOTE(lhy): 'auto' would silently score the base model, so a base eval uses `disable`.
if [ "${EVAL_BASE}" = "True" ]; then
    resume_args=(trainer.resume_mode=disable)
else
    resume_args=(trainer.resume_mode=resume_path "trainer.resume_from_path=${CKPT_PATH}")
fi

# --- GRPO and optimizer ---
# Never stepped, but constructed during init_workers, so kept equal to training.
actor_lr=1e-6
use_kl_loss=False
kl_loss_coef=0.0
clip_ratio_low=0.2
clip_ratio_high=0.3
total_training_steps=${TOTAL_TRAINING_STEPS:-200}

PYTHONUNBUFFERED=1 python3 -m psrl.trainer.main_ppo \
    psrl.ps_manager_ip=${LOCAL_IP:-127.0.0.1} \
    psrl.ps_mode=nixl_cpu \
    psrl.rollout_n=${rollout_N} \
    `# Overlaps rollout for step N+1 with training for step N. Requests in flight are` \
    `# rollout_n * staleness_buffer_entries * (staleness + 1), which the admission gate bounds.` \
    psrl.staleness=${STALENESS:-1} \
    psrl.staleness_buffer_entries=${train_batch_size} \
    psrl.rollout_gateway.trajectory_id_strategy=auto \
    psrl.rollout_gateway.server_max_concurrency=${SERVER_MAX_CONCURRENCY} \
    psrl.rollout_coordination.routing_strategy.max_concurrent_seqs_per_instance=${MAX_CONCURRENT_SEQS_PER_INSTANCE} \
    psrl.agentic_rl.batch_agg_mode=request \
    psrl.agentic_rl.thinking_template=${thinking_template} \
    psrl.agentic_rl.trajectory_output.enable=True \
    psrl.agentic_rl.turn_output.enable=True \
    psrl.logging_path=${PSRL_LOG_DIR} \
    psrl.log_prob.enable_rollout_engine_log_prob=True \
    psrl.deployment.n_rollout_instances=${GEN_INSTANCES} \
    psrl.deployment.rollout_nnodes_per_instance=1 \
    psrl.deployment.rollout_ngpus_per_node_per_instance=${GEN_NGPUS_PER_NODE_PER_INSTANCE} \
    psrl.deployment.n_validate_instances=${VAL_INSTANCES} \
    psrl.deployment.validate_nnodes_per_instance=1 \
    psrl.deployment.validate_ngpus_per_node_per_instance=${VAL_NGPUS_PER_NODE_PER_INSTANCE} \
    psrl.deployment.train_nnodes=${TRAIN_NNODES} \
    psrl.deployment.train_ngpus_per_node=${TRAIN_NGPUS_PER_NODE} \
    psrl.deployment.total_nnodes=${NNODES} \
    `# Drops zero-variance GRPO groups, which contribute no gradient. Off by default` \
    `# because the measured solve rate leaves only ~37% of groups surviving.` \
    psrl.group_post_process.enable=${GROUP_FILTER:-False} \
    psrl.group_post_process.name=dynamic_sampling_filter \
    algorithm.filter_groups.metric=seq_final_reward \
    `# Validation shares the training GPUs rather than reserving its own, which is what` \
    `# the 3 node topology assumes. With it on, fuse_rollout_with_validate is free to` \
    `# stay on too, and config validation only forces the fused path when it is off.` \
    psrl.colocate_validate_and_train=True \
    `# Dispatch validation requests across both the rollout and validate engines. During` \
    `# an eval the generation engines are otherwise idle, so this is the difference` \
    `# between scoring 14 tasks on 2 engines and on all 6.` \
    psrl.fuse_rollout_with_validate=True \
    \
    gen_actor_rollout_ref.rollout.name=vllm \
    gen_actor_rollout_ref.rollout.tensor_model_parallel_size=${GEN_TP} \
    gen_actor_rollout_ref.rollout.pipeline_model_parallel_size=${GEN_PP} \
    gen_actor_rollout_ref.rollout.gpu_memory_utilization=0.85 \
    gen_actor_rollout_ref.rollout.max_model_len=${max_model_len} \
    gen_actor_rollout_ref.rollout.max_num_batched_tokens=${max_num_batched_tokens} \
    ${chat_template_arg} \
    gen_actor_rollout_ref.rollout.n=${rollout_N} \
    gen_actor_rollout_ref.rollout.temperature=1.0 \
    gen_actor_rollout_ref.rollout.top_p=1.0 \
    gen_actor_rollout_ref.rollout.top_k=-1 \
    gen_actor_rollout_ref.rollout.multi_turn.enable=True \
    gen_actor_rollout_ref.rollout.multi_turn.max_turns=${max_turns} \
    gen_actor_rollout_ref.rollout.agent.agent_loop_config_path=${agent_loop_config_path} \
    gen_actor_rollout_ref.rollout.agent.default_agent_loop=scienceide \
    gen_actor_rollout_ref.rollout.agent.num_workers=${AGENT_LOOP_WORKERS} \
    `# Restrict which nodes host agent loop workers, and therefore Docker containers.` \
    `# Set AGENT_NODE_IPS='' to fall back to every alive node.` \
    ${AGENT_NODE_IPS:+gen_actor_rollout_ref.rollout.agent.node_ips=[${AGENT_NODE_IPS}]} \
    gen_actor_rollout_ref.rollout.agent.traj_reward_mode=traj \
    `# Masks budget-truncated episodes out of the gradient while keeping their reward in` \
    `# the GRPO baseline. Without it, token-mean rewards shorter turns.` \
    gen_actor_rollout_ref.rollout.agent.overlong_filtering=${OVERLONG_FILTERING:-True} \
    \
    train_actor_rollout_ref.model.path=${HF_MODEL_PATH} \
    train_actor_rollout_ref.actor.optim.lr=${actor_lr} \
    `# Short warmup. At 10 steps the first 10 updates ran at 10% to 90% of the target lr,` \
    `# so a run that only reached step 14 had barely trained and its reward curve was` \
    `# almost pure sampling noise. 3 steps still eases in the first updates.` \
    train_actor_rollout_ref.actor.optim.lr_warmup_steps=${LR_WARMUP_STEPS:-3} \
    train_actor_rollout_ref.actor.optim.weight_decay=0.1 \
    train_actor_rollout_ref.actor.ppo_mini_batch_size=${train_batch_size} \
    train_actor_rollout_ref.actor.ppo_micro_batch_size_per_gpu=1 \
    train_actor_rollout_ref.actor.use_dynamic_bsz=True \
    train_actor_rollout_ref.actor.ppo_max_token_len_per_gpu=${max_tokens_per_gpu} \
    train_actor_rollout_ref.actor.rollout_n=${rollout_N} \
    train_actor_rollout_ref.actor.clip_ratio_low=${clip_ratio_low} \
    train_actor_rollout_ref.actor.clip_ratio_high=${clip_ratio_high} \
    train_actor_rollout_ref.actor.use_kl_loss=${use_kl_loss} \
    train_actor_rollout_ref.actor.kl_loss_coef=${kl_loss_coef} \
    train_actor_rollout_ref.actor.entropy_coeff=0 \
    train_actor_rollout_ref.actor.loss_agg_mode=token-mean \
    train_actor_rollout_ref.actor.grad_clip=1.0 \
    train_actor_rollout_ref.actor.strategy=fsdp2 \
    train_actor_rollout_ref.actor.fsdp_config.fsdp_size=${TRAIN_FSDP} \
    `# Required by validate_config unless TMS covers the training workers.` \
    train_actor_rollout_ref.actor.fsdp_config.optimizer_offload=True \
    `# Chunks the log-prob computation, and is needed IN ADDITION to SP: the engine gathers` \
    `# before the head, so lm_head sees the full sequence. Unfused logits over Qwen3.5's` \
    `# 248,320 vocab are 45.5 GiB bf16, against 10.8 GiB chunked.` \
    train_actor_rollout_ref.model.use_fused_kernels=True \
    train_actor_rollout_ref.model.fused_kernel_options.impl_backend=torch \
    `# Shards activations for a ~98k-token packed sequence. See TRAIN_SP above.` \
    train_actor_rollout_ref.actor.ulysses_sequence_parallel_size=${TRAIN_SP} \
    +train_actor_rollout_ref.actor.use_rollout_log_probs=True \
    \
    train_actor_rollout_ref.rollout.tensor_model_parallel_size=${VAL_TP} \
    train_actor_rollout_ref.rollout.pipeline_model_parallel_size=${VAL_PP} \
    train_actor_rollout_ref.rollout.gpu_memory_utilization=0.6 \
    train_actor_rollout_ref.rollout.max_model_len=${max_model_len} \
    train_actor_rollout_ref.rollout.max_num_batched_tokens=${max_num_batched_tokens} \
    train_actor_rollout_ref.rollout.val_kwargs.n=1 \
    train_actor_rollout_ref.rollout.log_prob_use_dynamic_bsz=True \
    train_actor_rollout_ref.rollout.log_prob_micro_batch_size_per_gpu=1 \
    train_actor_rollout_ref.rollout.log_prob_max_token_len_per_gpu=${max_tokens_per_gpu} \
    \
    reward.launch_reward_fn_async=True \
    reward.active_managers='[dapo]' \
    reward.managers.dapo.reward_fn.0.path=${reward_path} \
    reward.managers.dapo.reward_fn.0.name=compute_score \
    `# Off. Length is a symptom of failing to localize the defect, not a cause worth shaping.` \
    reward.managers.dapo.reward_kwargs.overlong_buffer_cfg.enable=False \
    reward.managers.dapo.reward_kwargs.max_resp_len=${max_response_length} \
    \
    data.train_files=${train_files} \
    data.val_files=${val_files} \
    data.train_batch_size=${train_batch_size} \
    `# The bank is grouped by category on disk and verl's vendored default is shuffle=False.` \
    data.shuffle=True \
    data.seed=${DATA_SEED:-1} \
    data.prompt_key=prompt \
    data.max_prompt_length=${max_prompt_length} \
    data.max_response_length=${max_response_length} \
    data.return_raw_chat=True \
    data.filter_overlong_prompts=False \
    data.truncation=error \
    data.reward_model_dicts.0.reward_loop_type=dapo \
    data.reward_model_dicts.0.reward_fn=compute_score \
    \
    algorithm.adv_estimator=grpo \
    algorithm.use_kl_in_reward=False \
    `# Dr. GRPO: center advantages within the group, do NOT divide by the group std.` \
    `# Dividing amplifies noise in near-degenerate groups, and this task is close to bimodal.` \
    algorithm.norm_adv_by_std_in_grpo=False \
    `# TIS, matching the dapo_trainer convention. Load-bearing rather than optional because` \
    `# staleness=1 means the rollout and training policies genuinely differ.` \
    algorithm.rollout_correction.rollout_is=token \
    algorithm.rollout_correction.rollout_is_threshold=2.0 \
    trainer.critic_warmup=0 \
    trainer.logger='["console","wandb"]' \
    trainer.project_name=${project_name} \
    trainer.experiment_name=${experiment_name} \
    trainer.default_local_dir=${CKPTS_DIR} \
    trainer.n_gpus_per_node=${NGPUS_PER_NODE} \
    trainer.nnodes=${NNODES} \
    `# Never write a checkpoint. -1 disables periodic saves, which an eval must not do` \
    `# anyway, and keeps this run from depositing anything into the training tree.` \
    trainer.save_freq=-1 \
    `# No in-training validation, because there is no training. The single scoring pass` \
    `# comes from val_before_train below.` \
    trainer.test_freq=-1 \
    `# Score the checkpoint once, before any update.` \
    trainer.val_before_train=True \
    `# Return immediately after that first validation. fit() exits before starting the` \
    `# data processor, so no rollout for training is ever requested and the optimizer is` \
    `# never stepped. This is what makes the script an eval rather than a 1-step run.` \
    trainer.val_only=True \
    `# Still required by the schema. Unused because fit() returns first, but the actor` \
    `# optimizer schedule is constructed from it during init.` \
    trainer.total_training_steps=${total_training_steps} \
    `# resume_mode=resume_path for a checkpoint, resume_mode=disable for a base eval.` \
    `# See the EVAL_BASE block above.` \
    "${resume_args[@]}" \
    "$@" 2>&1 | tee "${OUTPUT_DIR}/${experiment_name}.log"
