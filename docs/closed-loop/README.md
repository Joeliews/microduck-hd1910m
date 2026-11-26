# XL330 / HD-1910 闭环验收

本目录是 Fork `Joeliews/microduck-hd1910m` 上的闭环验收底稿。官方仓只读：`pollen-robotics/microduck`、`pollen-robotics/microduck_rl`。飞特仓里的 `microduck_rl/` 是适配树，不是官方训练栈。

| 文件 | 内容 |
| --- | --- |
| [acceptance-criteria.md](acceptance-criteria.md) | 可执行验收标准 |
| [standing-goals.md](standing-goals.md) | 持续目标、自动推进与约束 |
| [policy-matrix-20.md](policy-matrix-20.md) | 2 舵机 × 10 策略，20 格 |
| [version-freeze.md](version-freeze.md) | 官方 runtime 与官方 `microduck_rl` 版本冻结 |
| [servo-xl330.md](servo-xl330.md) | XL330 参数冻结 |
| [servo-hd1910.md](servo-hd1910.md) | HD-1910 参数冻结、谱系、待实测 |
| [rounds/round-01.md](rounds/round-01.md) | 第 1 轮：Python 短评估 |
| [rounds/round-02.md](rounds/round-02.md) | 第 2 轮：Rust 控制核心接 MuJoCo |
| [rounds/round-03.md](rounds/round-03.md) | 第 3 轮：官方植物多种子零样本，未通过 |
| [rounds/round-04.md](rounds/round-04.md) | 第 4 轮：官方 PPO 短训冒烟，未通过 |
| [rounds/round-05.md](rounds/round-05.md) | 第 5 轮：约 100 轮续训，未通过 |
| [rounds/round-06.md](rounds/round-06.md) | 第 6 轮：短训导出的预留种子评估，未通过 |
| [rounds/round-07.md](rounds/round-07.md) | 第 7 轮：官方植物 Rust 接线被挡住 |
| [rounds/round-08.md](rounds/round-08.md) | 第 8 轮：官方植物在 ready 前失败 |
| [rounds/round-09.md](rounds/round-09.md) | 第 9 轮：官方植物在 env.reset 失败 |
| [rounds/round-10.md](rounds/round-10.md) | 第 10 轮：官方植物短闭环跑完，墙钟 20 ms 未达到 |
| [rounds/round-11.md](rounds/round-11.md) | 第 11 轮：r4 分步计时，瓶颈在官方 env.step |
| [rounds/round-12.md](rounds/round-12.md) | 第 12 轮：官方权重预留种子 10/11/12，未通过 |
| [evidence/xl330-velstand-cpu-r1/](evidence/xl330-velstand-cpu-r1/) | Python CPU MuJoCo 短评估，未重跑 |
| [evidence/xl330-velstand-rust-r1/](evidence/xl330-velstand-rust-r1/) | Rust `Policy::infer` + `mj_step` |

短评估脚本：`scripts/closed_loop/eval_xl330_velstand_cpu.py`。

已核对的离线推理对照在项目 store，路径 `/cursor/stores/bc-b174b37c-5d88-5df4-8c97-7e4424b6d372/internal/verified-evidence/`。那些结果是同一观测序列上的 Rust / Python 动作对照，不是 MuJoCo 动作成功，也不是板端 50 Hz。
