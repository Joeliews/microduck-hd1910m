# 第 2 轮

## 计划

在同一分支上让 Rust 控制核心调用 MuJoCo 的 `mj_step`，对 XL330 `velstand` 记一次可复核的仿真闭环。不重跑第 1 轮的 Python 短评估，不把任一次短跑写成验收通过。官方 BAM + rough + backlash 的多种子零样本留给本机 WSL，云端不安装训练栈。

## 标识

| 项 | 值 |
| --- | --- |
| 分支 | `cursor/xl330-velstand-acceptance-dbeb` |
| PR | https://github.com/Joeliews/microduck-hd1910m/pull/1 |
| 执行 agent | `bc-38c4813c-8721-55a8-89ed-76296786dbeb` |
| 线程 | XL330 velstand criteria |
| 任务 | MH-1。跑的时候 tracker 版本是 2；若协调器随后改过版本，以 tracker 当时的数字为准 |
| 跑之前的 HEAD | `480010239600bdde609456a423479c449b7533dc` |

`metrics.json` 里的 `git_head` 是这次提交之前的 HEAD。

## 接法

`microduck/duck-control/examples/xl330_velstand_mujoco.rs` 使用本 crate 的 `Policy::load`、`Observation::build` 和 `Policy::infer`。每个控制拍调用 `plant_step_n`，C 侧再调用 `mj_step` 四次。特征 `mujoco-plant` 才链接 `libmujoco.so.3.3.7`，普通测试不链接。

官方 ONNX 没有 `joint_snapshot_training`。`ort` 把缺的自定义字段读成空字符串，加载器原先把空字符串当成未知合同。现在空字符串和缺字段一样，走原来的 legacy 路径。未知的非空值仍然拒绝。

## 这次跑了什么

- 权重 SHA256 `ce894d30b3343036d499bfac1102bdaa58d59a21c1b58401ecb70fb6a2f63e0a`。ONNX 元数据 `action_scale` 为 1.0。图内已有 Sub/Div，循环外不再归一化。
- 关节顺序与第 1 轮相同。HOME 取 `STAND` 关键帧，和 `DEFAULT_POSITION` 去掉嘴之后的最大差 4e-5 rad。
- 场景 `scene_walk.xml`，平地，位置 PD。不是 BAM，不是 rough，不是 backlash，不是轮滑。
- 物理步长 0.005 s，4 次子步，逻辑控制周期 0.02 s（50 Hz）。种子没有抽，传感器噪声清零。
- 循环状态：前馈图，`Policy` 没有 reset。每个案例把上一步动作清零，并重新载入 `STAND`。
- 命令为零。两段各 4 s：`stand_zero`，以及 1 s 时 `qvel[0] += 0.3`。
- 工具链：rustc 1.89.0，ONNX Runtime 1.23.2（`ORT_DYLIB_PATH`），MuJoCo 3.3.7。`intra_op` 线程数 1，与 `Policy` 一致。

超时：墙钟超过 20 ms 的控制拍计一次，物理步不跳。丢帧：逻辑拍全部执行，所以丢帧数为 0。异常：推理失败或非有限状态会停下，写入 `failures.json`，进程退出码 2。这次没有走到那条路径。

## 指标

| 案例 | 步数 | 最低高度 m | 最大倾角 ° | \|action\| max | 墙钟 p50 / p95 / p99 / max ms | 超过 20 ms | 丢帧 | MuJoCo 警告 |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| stand_zero | 200 | 0.1153 | 1.08 | 0.212 | 0.162 / 0.196 / 0.222 / 0.235 | 0 | 0 | 0 |
| stand_push_0.3mps | 200 | 0.1153 | 3.67 | 1.073 | 0.162 / 0.194 / 0.233 / 0.363 | 0 | 0 | 0 |

初始观测前 6 维是 `[0, 0, 0, 0, 0, -1]`，相对 HOME 的关节位置最大绝对值为 0。两段都没有跨过 60° / 0.05 m，`failures.json` 是 `{}`。

这台机器上，这次短跑的墙钟 p99 低于 20 ms，超时和丢帧都是 0。这只说明仿真逻辑 50 Hz 在这台云端虚机上没有花满 20 ms。它不是板端实时。第 2 节要求的多种子、多命令和官方植物都没有做，所以 20 格里这一列是「短闭环已记录」，不是通过。

画面是记录下来的 qpos 回放，不是再推一次策略。脚本 `scripts/closed_loop/render_recorded_qpos.py`。

## 产物

| 路径 | 内容 |
| --- | --- |
| `docs/closed-loop/evidence/xl330-velstand-rust-r1/metrics.json` | 指标与合同字段 |
| `docs/closed-loop/evidence/xl330-velstand-rust-r1/failures.json` | 空对象 |
| `docs/closed-loop/evidence/xl330-velstand-rust-r1/*.series.csv` | 高度、倾角、墙钟 |
| `docs/closed-loop/evidence/xl330-velstand-rust-r1/*.qpos.csv` | 每拍的 qpos |
| `docs/closed-loop/evidence/xl330-velstand-rust-r1/*.gif` | qpos 回放 |
| `scripts/closed_loop/run_xl330_velstand_rust.sh` | 重复编译并运行 |
| `scripts/closed_loop/official_velstand_wsl.sh` | 只打印本机 WSL 上官方 bench 的指向，不安装、不开训 |

## 审查

第 1 轮的 Python 证据原样保留。Rust 数字和那次 Python 短跑在同一植物上接近（零命令最大倾角都约 1.08°，脉冲约 3.67°），这只说明两条循环走了同一份 XML PD，不能互相升级成通过。

## 下一步

本机 WSL 上用官方 `pollen-robotics/microduck_rl` 跑 BAM + rough + backlash 的多种子零样本。云端继续不做长时间 PPO。其余 19 格仍是未执行。
