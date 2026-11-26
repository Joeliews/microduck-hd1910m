# 可执行验收标准

门槛写在这里，供以后的格子打分。本轮没有任何一格达到「通过」。推理数值对照通过，不得写成 MuJoCo 动作成功或板端 50 Hz 验收。仿真逻辑上的 50 Hz（控制周期 0.02 s）也不得写成板端实时。

## 1. 必须留在报告里的字段

每次行为评估、重训复评、导出对照、Rust 环，都要能按下面几项对回同一份记录：

- 源码 commit：官方 `pollen-robotics/microduck`、官方 `pollen-robotics/microduck_rl`、本 Fork HEAD。飞特适配树单独标出，不冒充官方训练栈。
- 模型 SHA256。
- 关节顺序、HOME、动作缩放、归一化由谁做（图内 Sub/Div，还是图外再做一次）。
- 循环状态与重置：上一步动作、策略 reset、仿真 keyframe / 随机化是否清掉。
- 控制步长与物理步长，以及它们是仿真逻辑时间还是墙钟。
- 地形（平地 / rough）和轮滑模式（`roller`、`roller_crouch` 必须用带滑轮的物理，不能用无轮的 walk/groundcontact 模型代替）。
- 随机种子。多种子要列出每一颗，不能只写「已随机」。
- 定量指标、运行视频、失败样本。失败样本保留原始步号、状态和动作，不删。

## 2. 连续动作

适用于 `alpha_walking`、`velstand`、`alpha_stand`、`roller`。

- 种子 ≥ 3，彼此独立。每种子 ≥ 16 条 episode。
- 命令至少覆盖：零速度、前进、侧向、偏航。`velstand` 另加站立时的躯干 roll、pitch 与 z。命令幅值写进记录，不临时改口径。
- 扰动至少一种水平速度脉冲，幅值写进记录。官方 develop 上 `scripts/velstand_bench.py`（commit `0daab160d3fb1c2cbaba16a4a19052f36709dd9e`）用 0.8 / 1.0 / 1.2 m/s，统计窗可参照该脚本的 8 s、3 s 后统计。那是参照定义，本轮没有跑该脚本。
- 失败定义：统计窗内躯干倾角 > 60°，或躯干高度 < 0.06 m，或状态非有限值。
- 行为通过：该命令下失败比例 ≤ 10%，并且中位高度、倾角、失败比例都写入报告。10% 是本仓库门槛，不是 Pollen 发布的官方通过线。

## 3. 单次动作

适用于 `alpha_sitstand`、`alpha_ground_pick`、`roller_crouch`、`roulade`、`ball_kick_left`、`ball_kick_right`。

- 相位按官方 manifest：`alpha_sitstand` 用 `twist.vx` 的坐/站旗标，ramp 2 s、unwind 1 s；`alpha_ground_pick` 相位周期 4 s、结束相位 0.7、时长 2.8 s；`roller_crouch` 周期 5 s、结束相位 0.7、时长 3.5 s、`action_scale` 0.8、轮滑模型；`roulade` 时长 1.0 s 且 `chain: true`；左右踢时长各 0.5 s。
- 动作结束后再记一段恢复窗（至少 2 s，零速度命令）。相位段和恢复段都用第 2 节的失败定义。
- 另外记下任务量，不拿别的指标代替：坐站记下躯干高度曲线；拾取记下手端或嘴端相对地面的最低高度；翻滚记下姿态角变化；踢球记下球在存在球模型时的位移。这些量本轮都还没有。

## 4. 零样本失败后的重训

- 先跑原官方 ONNX 的零样本。失败则保留失败样本。
- 针对失败的命令族或初态重训。云端虚机不做长时间 PPO；训练在本机 WSL 上做。
- 复评种子必须独立于选模种子。复评使用同一套失败定义和通过比例。
- 没有重训检查点的格子，重训列写「未执行」。

## 5. 训练 actor 与 ONNX

同一条观测序列上比较训练 actor 与导出 ONNX。通过线沿用已验证对照：逐步 max abs ≤ 1e-5。该对照通过只表示导出数值一致，不表示动作成功。

已验证的 10 个官方 ONNX 在 store 的 `summary.json` 里与 Rust `policy-rehearsal` 比特一致。那次观测是合成的 61 维向量（`x[5] = -1`，`x[34:48]` 为上一步动作），没有走 MuJoCo，也没有走 `Observation::build` 的实机装配。本标准要求以后的对照使用闭环里真实产生的观测序列，而不是把那次合成序列再记一次。

## 6. Rust 核心接入 MuJoCo 后的 50 Hz

- Rust 控制核心必须真正调用 MuJoCo 步进，再读回状态。只测 actor 推理时延不算。
- 逻辑控制周期 20 ms。记录墙钟周期的 p50 / p95 / p99 / max、超过 20 ms 的次数、丢帧次数，以及异常如何处理（继续、跳帧、停机）。
- 墙钟 p99 ≤ 20 ms 且超时次数和丢帧次数都为 0，才可以写「在这台主机上，仿真逻辑 50 Hz 的墙钟没有超出 20 ms 预算」。
- 这句话仍然不是板端实时。板端还要加上传感器与电机总线。已验证的 velstand 推理时延（p50 0.012 ms 量级）只含 actor，明确排除在本条之外。

## 7. 本轮短评估不满足的条目

`scripts/closed_loop/eval_xl330_velstand_cpu.py` 只覆盖 XL330 `velstand` 的一个确定性平地循环：零命令 4 s，以及 1 s 时沿 x 加 0.3 m/s 的一次脉冲。植物是与官方 commit `53fb7d1` blob 一致的 `scene_walk.xml` 位置执行器，不是 BAM，不是 rough，不是 backlash。种子没有抽多颗。Rust 没有进环。因此第 2、4、6 节都不通过。数字见 `evidence/xl330-velstand-cpu-r1/metrics.json`。
