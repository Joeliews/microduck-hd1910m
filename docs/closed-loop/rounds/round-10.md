# 第 10 轮

结论：`executed_not_acceptance`。不是通过，也不是 4 秒 XML-PD 的重标。墙钟 20 ms 预算没有达到。这不是板端实时性，也不能写成已经通过 50 Hz 墙钟验收。

本机用 PR HEAD `d3c39dbe0d9e27d3c2d9565dc33a2bf58f898cb7` 跑完官方植物 Rust 短闭环 r3。关节名错误和 r2 的 `topple_push` 错误都没有再出现。`env.reset()` 成功。逻辑 50 Hz 跑完 200 步。200 步的墙钟全部超过 20 ms。

云端虚机读不到本机证据目录。下面是已经独立核对的事实。不要覆盖 r1、r2 或这次的 r3。

## 环境

| 项 | 值 |
| --- | --- |
| 墙钟 | 2026-11-26 20:31:20–20:32:03，Asia/Shanghai（+08:00） |
| 脚本 | rc=0，cargo 15.89 s |
| 机器 | Ubuntu 22.04 |
| Python | `OFFICIAL_RL_PYTHON`，official-rl 的 python3，torch 2.9.1+cu128 |
| 官方检出 | `0daab160d3fb1c2cbaba16a4a19052f36709dd9e`，干净，未改写 |
| BAM | `62bd8ce12154340be97e06f7f41a0ca8f116d967` |
| ONNX 跑前 SHA256 | `ce894d30b3343036d499bfac1102bdaa58d59a21c1b58401ecb70fb6a2f63e0a` |
| Fork | `d3c39dbe` 的全新解包 |

完整 49 MiB GitHub 归档复制两次失败后，改用 slim `scripts/closed_loop` + `microduck/`，SHA256 `bc9cd9047d101c98524df82a0a7c18af19f0b01169c70e606281c5131e4cc290`。解包后 `official_velstand_plant.py` 为 `6f35905375c3f55d573941ef4e5ebc1a0b26c8645a035f2f191207fb41ecff14`，启动脚本为 `51445e245f8c006ab941a1d679862f5b0756ac40112129ead2a9e12862709ff9`，Rust 示例仍是 `8efaed3d8339c7b24b21c6138a084e7267b1b748fd449bc4fd96e62916c4ee0e`。sidecar 没有本地打补丁。

## 植物

`sidecar.log`：

- `[rough terrain] softened 2241 terrain geoms`
- `[BamActuator] model='m6' joints=14 ... device=cuda:0`
- `[BacklashEncoderBamActuator] ... 14/14 joints`
- physics 0.005 / env 0.02
- `ready port=40371 plant=bam_m6_allcollisions_backlash_rough commit=0daab160d3fb1c2cbaba16a4a19052f36709dd9e`

CurriculumManager 有 19 个活跃项，没有 `topple_push_range`。日志里 `topple_push` 出现 0 次，没有 Traceback。hello 被接受。没有 XML-PD、`scene_walk.xml` 或 `body_server` 回退。AgentsDock 未杀。

## 只能从 metrics.json 抄的数

`metrics.json` SHA256 `ca348eb768e19452599d26bb3aeb0e6ee25e2789f3a237b425807e50c0bc941f`。

| 项 | 值 |
| --- | --- |
| steps | 200 |
| exception | false |
| fell | false |
| logical_hz | 50 |
| duration_s | 4.0 |
| wall_clock_ms p50 | 36.9231805 |
| wall_clock_ms p95 | 41.92045814999999 |
| wall_clock_ms p99 | 44.76975451999998 |
| wall_clock_ms max | 347.306114 |
| over_20ms | 200 |
| scope | rust infer plus one official env.step round trip; not the board |
| height_m min / max / final | 0.1139061599969864 / 0.12048380076885223 / 0.11540962755680084 |
| tilt_deg p95 / max / final | 0.9531928178810536 / 1.5433228478071543 / 0.2548778437595286 |
| dropped_frames | 0 |
| timeouts | 没有这个字段 |
| dropped_frame_policy | logical ticks are not skipped; an overrun is a timeout, not a dropped physics step |

逻辑 50 Hz 跑完了。墙钟 20 ms 预算没有达到：200 步全部超过 20 ms。`metrics.json` 只有合计墙钟，没有把 `Policy::infer` 和一次 `env.step` 往返拆开，所以这次不能从原始样本复算分位，也不能指出超时花在推理还是植物步进。

## GPU

5090 D v2，24455 MiB。

| 时刻 | 显存 | 利用率 | 温度 | 功率 |
| --- | --- | --- | --- | --- |
| 跑前 `20:31:22.973150+08:00` | 4334 MiB | 6% | 37.50 C | 66.23 W |
| 循环窗口 | 约 5430–5438 MiB | 48–51% |  | 116–119 W |
| 跑后 csv `20:32:03.286154+08:00` | 5430 MiB | 53% | 41.20 C | 118.64 W |

## 本机证据路径

- `/home/a/microduck-loop/evidence/2026-11-26/official-velstand-rust-official-plant-r3/`
- `C:\Users\A\microduck-loop\evidence\2026-11-26\official-velstand-rust-official-plant-r3\`

r3 `report.md` SHA256 `98d7f55028fc8383d561a3614ec0b4e035d58710fd372424cd9b318efee5f5e8`。r1 的 `report.md` 仍是 `91d3e1d2fc046fa02c546fc554fdf0d59b9761d75fbbb060e3723470fb038075`。r2 仍是 `1d53171ca280d6b7656c701df2045a2589de3eaadf4540c4fba841891417f3e6`。
