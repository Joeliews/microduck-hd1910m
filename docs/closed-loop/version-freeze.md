# 版本冻结

核对时间：2026-11-26。只读 GitHub API / `git fetch`，没有向官方仓推送，没有改官方工作区。

## 官方 runtime：`pollen-robotics/microduck`

| 角色 | commit | 日期与说明 |
| --- | --- | --- |
| 先前推理对照当时的 HEAD，本轮再次确认该对象存在 | `dec725c67ffbbdde7f1de30f8c936b1bf9c1d70e` | 2026-10-07，Merge PR #380 `duckctl-quack` |
| 本轮冻结的默认分支 `main` HEAD | `4024f6ee4373d38ac0a60a79157bcfb57642be9c` | 2026-11-25，Merge PR #621 `seated-skills` |

`dec725c` 不再是 `main` HEAD。离线推理证据仍挂在 `dec725c` 上，不能改写成「已经在 `4024f6ee` 上重跑过」。

对这两个 commit 做了 `git diff`（仅这几个路径）：

- `duck-control/src/obs.rs`：无差异。61 维观测布局仍是 gyro、重力、相对 HOME 的 14 关节、关节速度、上一步动作、13 维命令。
- `duck-control/src/policy.rs`：无差异。
- `duck-control/src/model.rs`：HOME 与关节表没有改；新增冲击保护和电压补偿 PWM。`CURRENT_LIMIT_MA = 1000`，`MOTOR_MAX_V = 6.0`。
- `robotd/src/control.rs`：站立技能的 scale 选择有改动。行走模式默认 `action_scale` 仍是 0.9，`standing_action_scale` 仍是 1.0（`robotd/src/control.rs` 的 `Tuning::default`，以及 `robotd-params` 里 Walk 0.9 / Roller 0.8）。

本 Fork 的 `microduck/` 是带 HD1910、BNO 和 App 改动的集成快照。它的 git HEAD 不是上面任何一个官方 commit。

## 官方训练栈：`pollen-robotics/microduck_rl`

默认分支是 `develop`，不是 `main`。`main` 停在 `1e79c29c97d8b38aee9eefde77a545860ba7658e`（2026-08-25），不能拿来复现 2026-10 的 velstand。

| 角色 | commit | 说明 |
| --- | --- | --- |
| 默认分支 `develop` HEAD | `0daab160d3fb1c2cbaba16a4a19052f36709dd9e` | 2026-11-10，Merge `velstand_v9_is_v7`。文档写明 Hub v9 的 `velstand.onnx` 就是 v7 文件，训练 run `j4i6yoq2` @ checkpoint 1250 |
| 该 ONNX 的训练 commit | `53fb7d115b1be79c6d07e8fd4eab311285e16f2a` | 2026-10-01，分支 `improve_velstand2`，信息 `velstand: standing-only body control`。与官方 manifest 里的短 SHA `53fb7d1` 一致。当前该分支尖端是更后面的 `454ddb91a95443e054dc749706538fd0d3165ebf`，复现这颗已发布 ONNX 时用 `53fb7d1`，不用分支尖端 |

任务名：`Mjlab-VelStand-Rough-Backlash-MicroDuck`。植物是 all-collisions + backlash + rough，执行器是 BAM M6（`motor_name=xl330`，`model=m6`），不是 XML 里的 position PD。

`pyproject.toml` 在 `53fb7d1` 把 `better-actuator-models` 指到 `https://github.com/Rhoban/bam.git` 分支 `mjlab_frictionloss`，没有钉 SHA。2026-11-26 该分支 HEAD 仍是 `57d13ead53206a6bf0db3d66f86506ae8c2ce01a`（2026-07-16）。训练发生在此之后，分支尖端没有再动，因此这次冻结把 BAM 钉在这个 commit。默认分支上的另一份 `bam/params/xl330/m6.json` 数值不同，不要混用。

## 飞特适配树不是官方训练栈

`microduck_rl/`（本 Fork）含 HD1910 任务、`sts3215` 字段的 JSON、CPU BAM 包装和回放脚本。复现官方策略时不要把这棵树当 `pollen-robotics/microduck_rl`。

例外，且只限于这两个文件：本 Fork 里下列路径的 git blob 与官方 `53fb7d1` 一致，短评估用的是它们。

| 路径 | blob |
| --- | --- |
| `microduck_rl/src/mjlab_microduck/robot/microduck/scene_walk.xml` | `7aa25e52b609da73d759c7adc99233c7e63239bc` |
| `microduck_rl/src/mjlab_microduck/robot/microduck/robot_walk.xml` | `96de481cce278f089145cf07b7088b173a7bbede` |

`robot_allcollisions_backlash.xml` 在官方 `53fb7d1` 存在，本 Fork 这份树里没有。所以短评估没有、也不能声称跑了 velstand 的训练植物。

## 权重

来源：`https://huggingface.co/pollen-robotics/microduck-policies/resolve/main/`。SHA256 沿用 store 里已复核的 `official-policies.sha256`。本轮重新下载了 `velstand.onnx`，SHA256 仍是 `ce894d30b3343036d499bfac1102bdaa58d59a21c1b58401ecb70fb6a2f63e0a`。权重文件被 `.gitignore` 排除，不进本 PR。

官方 manifest（store `manifest.json`，SHA256 `5c6a73f95f388f131aaef570f6113f0d36b84a72d5755662cd57e67adf7fd24c`）写明机器人 `servos: xl330`，`control_hz: 50`，`obs_len: 61`，`action_len: 14`。`velstand` 的训练记录：repo `pollen-robotics/microduck_rl`，commit `53fb7d1`，run `pollen-robotics/mjlab_microduck/j4i6yoq2`，checkpoint 1250，导出时间 `2026-10-05`。
