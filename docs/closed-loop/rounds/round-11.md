# 第 11 轮

结论：`executed_not_acceptance`。不是通过，也不是 50 Hz 墙钟验收。4 秒短跑没有写成通过线。20 ms 墙钟预算没有放宽。这是主机上的 `Policy::infer` 加上一次官方植物步进，不是板端计时。

本机在 DESKTOP-14410AL 的 Ubuntu 22.04 上，用 PR HEAD `643dccc86e0c58815508225dcff4285aa92890f0` 跑完官方植物 Rust 短闭环 r4。没有本地改 sidecar 或 Rust 示例。没有 XML-PD 回退。这次没有提交运行产物。云端没有重跑 GPU。

云端虚机读不到本机证据目录。下面是已经独立核对的事实。不要覆盖 r1、r2、r3 或这次的 r4。

## 环境

| 项 | 值 |
| --- | --- |
| 机器 | DESKTOP-14410AL，只使用 Ubuntu 22.04 |
| 包装脚本墙钟 | 2026-11-26T20:51:12.553106+08:00 至 2026-11-26T20:51:53.526722+08:00 |
| 脚本 | rc=0，时刻 2026-11-26T20:51:53.354087+08:00，cargo 15.11 s |
| 解包 | slim tarball SHA256 `1e88217585d2e171623bd83c305e2c5ab0ede4d9966b3d4cecce56e982792380`，目录 `/home/a/microduck-loop/repos/microduck-hd1910m-pr1-r4`，HEAD `643dccc` |
| 解包后 plant.py | `3a7467eb0043baddb413cccc482aaa63c84f6b7a47272c85e0090946e2b06f00` |
| 解包后启动脚本 | `acfdd565b6b6e568e4bc9ecd312332e371bbaf1fa70bd6a9ad4cf0a9441f78c1` |
| 解包后 Rust 示例 | `b232f00afb308a457edc6b26ba8ea3112f7bab36cac6bfe865c0ce4cee21efd1` |
| ONNX 跑前 | 2026-11-26T20:51:12.573117+08:00，SHA256 `ce894d30b3343036d499bfac1102bdaa58d59a21c1b58401ecb70fb6a2f63e0a`。不是短训导出 `cf280a27…` |
| 官方检出 | `0daab160d3fb1c2cbaba16a4a19052f36709dd9e`，跑前和跑后 dirty=0 |
| BAM | `62bd8ce12154340be97e06f7f41a0ca8f116d967` |
| Python | official-rl，Python 3.12.16，torch 2.9.1+cu128 |
| Rust | rustc / cargo 1.89.0 |
| ORT SHA256 | `2d518e11c7767f9fdc4413bdbeb45acf30db504ff76a82fc19d9238a3f9f6c24` |
| 种子 / 设备 | seed 0，`cuda:0` |

`metrics.json` 里的 `git_head` 是 `unknown`，因为这份 slim 解包不是 git checkout。

## 植物

`ready port=41733 plant=bam_m6_allcollisions_backlash_rough commit=0daab160d3fb1c2cbaba16a4a19052f36709dd9e`。`env.reset()` 成功。`sidecar.log` 里 `topple_push` 为 0 次，`_joint_names` 为 0 次，Traceback 为 0 次。CurriculumManager 有 19 项，没有 `topple_push_range`。

200 步，`duration_s` 4.0，`logical_hz` 50，`fell=false`，`exception=false`。`dropped_frames` 0。

| 项 | 值 |
| --- | --- |
| height_m min / max / final | 0.1139061599969864 / 0.12048380076885223 / 0.11540709435939787 |
| tilt_deg p95 / max / final | 0.9553395395349402 / 1.5437032025677102 / 0.25868789467819786 |

## 从 step_times.json 复算的分位

父进程用原始数组复算。方法是排序后相邻名次线性插值。`over_20ms` 是 `total_ms` 严格大于 20.0 的个数。200 个样本都在。`env_step_ms` 的 missing 为 0。这些数与 `metrics.json` 的 `wall_clock_ms` 完全一致。

| 数组 | p50 | p95 | p99 | max | 其他 |
| --- | --- | --- | --- | --- | --- |
| total_ms | 35.9374685 | 39.62661729999999 | 42.52731542 | 320.687231 | min 31.506982000000004，over_20ms 200 |
| infer_ms | 0.096796 | 0.13069455 | 0.14343531999999995 | 0.211206 | |
| step_round_trip_ms | 35.8234805 | 39.54004035 | 42.42612071999999 | 320.584128 | |
| env_step_ms | 33.294259454123676 | 36.921131156850606 | 39.28419962059705 | 318.04342300165445 | |

最大的 `total_ms` 320.687231 是第 0 步，几乎全部在 sidecar 的 `env.step`：infer 0.102773，rpc 320.584128，env 318.04342300165445。之后各步合计落在 31.506982 到 43.339157。

残余限制：在这套 Python/mjlab sidecar 下，官方植物 `env.step` 的 p50 已经是 33.294259454123676 ms。20 ms 主机墙钟预算没有达到。预算不放宽。这不是 50 Hz 墙钟验收。Rust `infer` 的 p50 是 0.096796 ms，不是瓶颈。

## GPU

以 csv 为准，不以 nvidia-smi 表为准。

| 时刻 | 显存 | 利用率 | 温度 | 功率 |
| --- | --- | --- | --- | --- |
| 跑前 `20:51:15.185834+08:00` | 4370 MiB | 5% | 52.80 C | 77.57 W |
| 循环后段 | 5467 MiB | 51–54% | | 约 128–131 W |
| 跑后 `20:51:53.354240+08:00` | 5467 MiB | 53% | 55.10 C | 129.58 W |

Windows 的 nvidia-smi 显示 AgentsDock.exe PID 41352 仍在运行。`official-cu` 没有被改。

## 本机证据路径

- `/home/a/microduck-loop/evidence/2026-11-26/official-velstand-rust-official-plant-r4/`
- `C:\Users\A\microduck-loop\evidence\2026-11-26\official-velstand-rust-official-plant-r4\`
- `/workspace/microduck-loop-evidence/2026-11-26/official-velstand-rust-official-plant-r4/`

r4 `report.md` SHA256 `0c57ef705bd4bbf9ca279e836339138bb92fed943c42b09542a78f312f3f3b6e`。证据盒的 `SHA256SUMS` 全部 MATCH。`SHA256SUMS` 文件本身是 `476bf83b6f38e51051799add84a277361e404b0d7060cfb97d2c620a6191f9e7`。

r1、r2、r3 没有被覆盖。三份 `report.md` 仍是 `91d3e1d2fc046fa02c546fc554fdf0d59b9761d75fbbb060e3723470fb038075`、`1d53171ca280d6b7656c701df2045a2589de3eaadf4540c4fba841891417f3e6`、`98d7f55028fc8383d561a3614ec0b4e035d58710fd372424cd9b318efee5f5e8`。
