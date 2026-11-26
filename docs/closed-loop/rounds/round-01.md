# 第 1 轮

## 计划

从 Fork `origin/main` 建分支，落盘验收标准、20 格、版本冻结和两套舵机参数，再跑 XL330 `velstand` 的 CPU MuJoCo 短闭环。不训练，不接实物，不把离线推理对照写成动作成功。

任务书里建议的分支名是 `closed-loop/xl330-velstand-acceptance`。本轮实际分支按仓库要求写成 `cursor/xl330-velstand-acceptance-dbeb`。

## 标识

| 项 | 值 |
| --- | --- |
| 分支 | `cursor/xl330-velstand-acceptance-dbeb` |
| 执行 agent | `bc-38c4813c-8721-55a8-89ed-76296786dbeb` |
| Cursor 线程 / 任务 | 待协调器填写 |
| 日期 | 2026-11-26 |

## 日志

环境：云端 Linux，4 核，无 NVIDIA GPU，无本机 private worker。Python 3.12.3。本轮用 pip 安装了 `mujoco==3.3.7`、`onnxruntime==1.23.2`、`pillow`。为了离屏画面安装了系统包 `libosmesa6`。没有租 GPU，没有跑 PPO。

```text
MUJOCO_GL=osmesa python3 scripts/closed_loop/eval_xl330_velstand_cpu.py \
  --out docs/closed-loop/evidence/xl330-velstand-cpu-r1
```

stdout：

```text
stand_zero upright_window height_min 0.1153 tilt_max 1.08 wall_p50_ms 0.21
stand_push_0.3mps upright_window height_min 0.1153 tilt_max 3.67 wall_p50_ms 0.212
```

`MUJOCO_GL=egl` 在没有 EGL 驱动时无法 import。`MUJOCO_GL=disable` 可以步进，但不能出图。最终记录用的是 OSMesa。

## 产物

| 路径 | 内容 |
| --- | --- |
| `docs/closed-loop/evidence/xl330-velstand-cpu-r1/metrics.json` | 指标、植物说明、SHA256 |
| `docs/closed-loop/evidence/xl330-velstand-cpu-r1/failures.json` | `{}`。两段都没跨过 60° / 0.05 m。空对象不是通过 |
| `docs/closed-loop/evidence/xl330-velstand-cpu-r1/stand_zero.npz` | 高度、倾角、墙钟序列 |
| `docs/closed-loop/evidence/xl330-velstand-cpu-r1/stand_push_0.3mps.npz` | 同上，带 0.3 m/s 脉冲 |
| `docs/closed-loop/evidence/xl330-velstand-cpu-r1/stand_zero.gif` | 480×360，每 5 个控制步一帧 |
| `docs/closed-loop/evidence/xl330-velstand-cpu-r1/stand_push_0.3mps.gif` | 同上 |
| `scripts/closed_loop/eval_xl330_velstand_cpu.py` | 可重复脚本 |

`velstand.onnx` 下载到 `/tmp/microduck-policies/velstand.onnx`，SHA256 `ce894d30b3343036d499bfac1102bdaa58d59a21c1b58401ecb70fb6a2f63e0a`。gitignore 排除 ONNX，文件不在分支里。

墙钟（Python ONNX + 4 次 MuJoCo 子步，不是 Rust，不是板端），单位毫秒，超时次数 0：

| 案例 | p50 | p95 | p99 | max |
| --- | ---: | ---: | ---: | ---: |
| stand_zero | 0.210 | 0.268 | 0.637 | 4.285 |
| stand_push_0.3mps | 0.212 | 0.257 | 0.276 | 0.426 |

逻辑控制周期是 20 ms（0.005 s × 4）。上表是这台云端虚机的墙钟，不能写成板端 50 Hz。

## 审查

短评估做了这些事：官方 SHA 的 `velstand.onnx` 读 61 维观测，动作加到 `STAND` 关键帧上，MuJoCo 按 200 Hz 物理、50 Hz 控制步进 4 s。初始重力观测是 `[0, 0, -1]`。零命令最大动作绝对值约 0.212；脉冲段约 1.073。画面里机器人保持站立。

它没有做这些事：BAM M6、rough、backlash、多种子、行走命令、官方 bench 的 0.8–1.2 m/s 推力、部署侧 0.9 行走缩放和 0.5/0.7 低通、Rust 进环。所以 XL330 `velstand` 只标「短评估已记录」。其余 19 格的行为、零样本、重训和 Rust 列是未执行。10 个 XL330 策略的导出列只沿用既有离线对照。

## 下一步

1. 在带官方 mjlab / BAM 的环境里重跑 velstand 零样本（训练植物：rough + backlash + BAM）。云端没有 RTX 5090，这一步留在本机 WSL，仍然不要在云端开长时间 PPO。
2. 多种子、命令组和更大的扰动按验收标准补。失败样本留下来。
3. Rust 控制核心接到 MuJoCo 后，再记 20 ms 墙钟的 p50/p95/p99/max、超时和丢帧。
4. 其余 9 个 XL330 策略，以及全部 HD-1910 格。轮滑两格用滑轮模型。
5. HD-1910 的待实测清单要在实物上做，不能靠改 `sts3215` 字段。
