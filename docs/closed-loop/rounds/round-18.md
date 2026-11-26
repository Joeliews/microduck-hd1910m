# 第 18 轮

结论：墙钟瓶颈的写法和可重放拆分入口。不是一次新的 4 秒重跑，不是通过，也不是 20 ms 验收。20 ms 预算没有放宽。

## 已经记下的拆分

第 11 轮 r4 的原始数组已经把时间拆开。下面只是把那次记录的 p50 相减，不是新测量。

| 量 | p50 |
| --- | --- |
| total_ms | 35.9374685 |
| infer_ms | 0.096796 |
| step_round_trip_ms | 35.8234805 |
| env_step_ms | 33.294259454123676 |

`step_round_trip_ms` 减去 `env_step_ms` 是 2.529221045876324 ms。这是同一次记录里的 RPC、JSON 和 `sense()`，不是新的计时。官方 `env.step` 的 p50 已经高于 20 ms。Rust `Policy::infer` 不是瓶颈。逻辑 50 Hz（`control_dt` 0.02 s，`Policy::load` 的站立阈值 0.05）不是墙钟通过。主机计时不是板端计时。

`over_20ms=200` 就是超时次数。丢帧按「逻辑拍不跳过」记，r4 的 `dropped_frames` 是 0。超时不是丢帧。

## 不要误用的两条路径

`COMPARE=1` 是把已经记下的观测交给 Python ONNX Runtime 重放。`total_ms` 含 RPC 之后写 dump 的记账。它不是 20 ms 的再试，也不是训练 actor 对 ONNX。

训练 actor 对导出 ONNX 是另一件事。官方 `0daab160` 没有这条数值通过线。本仓库 `acceptance-criteria.md` 第 5 节的逐步 max abs ≤ 1e-5 是项目自定义门槛，只表示导出数值，不表示动作成功，也不表示墙钟通过。证据文件必须和 Rust 重放的 `compare_report.json` 分开。

官方植物不得悄悄退回 XML 位置 PD。

`scripts/closed_loop/analyze_step_times.py` 只读已有的 `step_times.json`，按同一线性插值重算 p50/p95/p99/max。`timeouts` 与 `over_20ms` 都是 `total_ms > 20` 的次数。它不启动植物。下一次 Rust 记录会带上 `timeouts` 字段，和 `over_20ms` 同一计数。训练 actor 对 ONNX 的入口是 `scripts/closed_loop/compare_actor_onnx.py`，证据名应是 `actor_onnx_report.json`，没有 `ACTOR_ONNX_COMPARE_RUN=1` 时不写结果。这两条都还没有在本机跑出新数。
