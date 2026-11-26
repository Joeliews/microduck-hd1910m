# 第 15 轮

结论：这是官方评估路径的盘点，不是一次评估，也没有跑任何策略。不是通过。没有把任何格子标成已执行。没有发明新的 bench，也没有把任何策略送进 `velstand_bench`。

证据：`/workspace/microduck-loop-evidence/2026-11-26/official-eval-paths-inventory/`。`report.md` SHA256 `6a4a24a76ead51457a18ca64ebc8d25c576871ed5686bf0f5a5200e21fc191f8`。`inventory.json` SHA256 `92e484d991337f9294a9ce112f99ce3e10ad4946e9dce773d081365c851b83c7`。

实际读过的来源：

- 一次性官方检出 `/workspace/repos/microduck_rl-0daab160`，`0daab160d3fb1c2cbaba16a4a19052f36709dd9e`，dirty=0。`develop` 仍是这个提交。`454ddb91` 只是 `improve_velstand2`，没有拿来当这次的树。
- 官方策略的证据盒副本。manifest SHA256 `5c6a73f95f388f131aaef570f6113f0d36b84a72d5755662cd57e67adf7fd24c`。
- 官方 runtime 的证据盒检出 `dec725c`，dirty=0。GitHub `main` `4024f6ee` 没有做树遍历。这是残余，不是已经核对过 runtime `main`。

## 判定

| 策略 | 路径 | 说明 |
| --- | --- | --- |
| velstand | `official_path`，仅 `scripts/velstand_bench.py` | `build_env` 固定 `rough=False`（平地 + all-collisions backlash）。`--seed` 默认 0。`--envs-per-group` 默认 32。这是行为电池，不是 actor 对 ONNX 的通过线。已发布的训练植物仍是 `Mjlab-VelStand-Rough-Backlash-MicroDuck`。不改已经记下的 velstand 格子，也不是重跑。 |
| alpha_walking | partial，记为无官方评估路径 | manifest 没有 `training.task_id`。`velstand_policy.md` 把教师放在速度配方 `441tzs6d` @ 3750，不是 VelStand 植物。不要送进 `velstand_bench`。 |
| alpha_stand | partial，记为无官方评估路径 | manifest 没有 `training.task_id`。文档把教师放在站起环境 `69u48n8l` @ 9750，不是 VelStand 植物。不要送进 `velstand_bench`。 |
| roller | partial，记为无官方评估路径 | manifest `mode=roller`，部署 `action_scale=0.8`。父进程独立解析的 ONNX 元数据：这组里唯一带烘焙 `task_id` 的文件，值为 `Mjlab-Velocity-Swizzle-MicroDuck`，`run_path` `pollen-robotics/mjlab_microduck/598l1d3r`，checkpoint 6000，`export_commit` `bae39f590`，`export_dirty` false，烘焙 `action_scale` 1.0（部署尺度是 0.8）。这是 swizzle，不是 stride rollers 任务。没有专门的 ONNX bench。 |
| alpha_sitstand | partial，记为无官方评估路径 | manifest 钉住 `Mjlab-SitStand-Flat-MicroDuck`。文档引用的 `claude_experiments/sitstand_fallback_eval.py` 在 `0daab160` 里不存在。没有专门的 ONNX bench。 |
| alpha_ground_pick | partial，记为无官方评估路径 | GroundPick 任务存在，周期 4.0。没有 `task_id`，没有 bench。`pickup_eval.py` 是检测器，不是这个策略。`infer_policy --ground-pick` 不是独立的官方评估。 |
| roller_crouch | partial，记为无官方评估路径 | RollerCrouch 任务存在，周期 5.0，rollers XML。manifest `mode=roller`，`action_scale=0.8`。没有 `--crouch`，没有 bench。 |
| roulade | partial，记为无官方评估路径 | 只有 `Mjlab-Roulade-Flat-MicroDuck`，没有 backlash 孪生，没有 `task_id`，没有 bench。`infer_policy` 默认 `--roulade-duration` 2.0，manifest 是 1.0。 |
| ball_kick_left / ball_kick_right | partial，记为无官方评估路径 | 只有一个任务号 `Mjlab-BallKick-Flat-MicroDuck`，模块 `KICK_FOOT` 默认 `"right"`。没有左右分开的任务号，没有 bench。`infer_policy` 默认 `--kick-duration` 3.0，manifest 是 0.5。 |

这九个策略相关的官方任务、文档或排练可能存在，但没有专门的官方 ONNX eval/bench。表上写成「无官方评估路径（未执行，不是通过）」。不要自写包装再把它说成官方路径。

## 不是评估路径的官方入口

- `scripts/infer_policy.py` 是官方的交互式 ONNX 排练，默认 BAM M6。不是专门评估，也不是 `official_path`。
- `uv run play` 和 `play_latest.py` 是 wandb 检查点查看器。
- `duck-body` / `robotd --sim` 是 XML 位置 PD，不是官方策略 bench。

## 残余

- runtime 的 GitHub `main` `4024f6ee` 没有做树遍历。读过的是证据盒检出 `dec725c`，dirty=0。
- 没有 manifest 或 ONNX `task_id` 的策略，已发布产物钉不住具体的 Flat / Rough / Backlash 变体。
- `velstand_bench.py` 默认 32 环境/组，以脚本为准。文档里出现过 64/128，不覆盖这个默认值。
