# 第 14 轮

结论：`executed_not_acceptance`。不是通过，也不是 20 ms 墙钟验收，更不是 50 Hz 墙钟验收。绝对误差和相对误差都是 0，只是记录，不是通过。官方 `0daab160` 没有 actor 对 ONNX 的数值通过线。20 ms 预算没有放宽。r4 的计时没有改标。

本机用 `COMPARE=1` 跑了官方植物闭环对照。代码是 `7d6cf0b5db5b203a5662fbca3475b427af48c37a` 的全新 slim 解包，目录 `/home/a/microduck-loop/repos/microduck-hd1910m-pr1-compare`。不是 r4 那棵树，也没有本地打补丁。`metrics.json` 的 `git_head` 是 `unknown`，因为这份解包不是 git checkout。这里不另编一个 HEAD。

云端虚机读不到本机证据目录。下面是已经独立核对的事实。证据包没有提交进仓库。

## 环境

| 项 | 值 |
| --- | --- |
| 包装脚本墙钟 | 2026-11-26T21:56:20.520495+08:00 至 2026-11-26T21:56:57.977462+08:00 |
| 脚本 | `COMPARE=1`，`OUT` 目录名 `official-velstand-rust-onnx-compare`，rc=0 |
| Cargo | `+1.89.0`，编译 15.80 s |
| plant.py | `069ec7a138fb08dd34be36f533f5bfc7641a5117e3faa84be2b6b45b111ef5a6` |
| 启动脚本 | `a2acbfdbbcfc44f82825c1dab7345691dcb4afa6bec49afd505ccd1a183d047b` |
| compare 脚本 | `9855a6d46c7a325765893846f30b7f85ffafb1382829c6e1567e5dd178398fcd` |
| Rust 示例 | `c9860ed672dfd2ad66f83f46ca49cd040fb4841d17f99d819b6abdf31af05e33` |
| 官方检出 | `/home/a/microduck-loop/repos/microduck_rl`，`0daab160d3fb1c2cbaba16a4a19052f36709dd9e`，跑前和跑后 dirty=0。tip `454ddb91` 没有使用 |
| BAM | `62bd8ce12154340be97e06f7f41a0ca8f116d967` |
| ONNX | 跑前 2026-11-26T21:56:20.522000+08:00 的 SHA256 `ce894d30b3343036d499bfac1102bdaa58d59a21c1b58401ecb70fb6a2f63e0a`。不是短训 `cf280a27` |
| ORT | `libonnxruntime.so.1.24.4`，SHA256 `2d518e11c7767f9fdc4413bdbeb45acf30db504ff76a82fc19d9238a3f9f6c24` |
| Python | official-rl，torch 2.9.1+cu128。这次运行没有用 `official-cu`。跑前探测只记下它仍是 2.14.1+cu130，没有改写它 |

## 植物

`ready port=43039 plant=bam_m6_allcollisions_backlash_rough commit=0daab160d3fb1c2cbaba16a4a19052f36709dd9e`。BAM M6，backlash 14/14，`rough=true`，decimation 4，物理步长 0.005，seed 0，`cuda:0`。

`sidecar.log` 里这些字符串都是 0 次：Traceback、`_joint_names`、`topple_push`、ValueError、AttributeError、XML-PD、`body_server`、`scene_walk.xml`。

## 闭环计时

`metrics.json` 的 status 是 `executed_not_acceptance`。`exception=false`，`fell=false`，200 步，4.0 s，`logical_hz` 50。

高度 m：min `0.113906130194664`，max `0.12048380076885223`，final `0.11539871990680696`。

父进程用 `step_times.json` 按排序后相邻名次线性插值复算，与 `metrics.json` 一致。

| 数组 | 值 |
| --- | --- |
| total_ms | min `29.491874000000003`，p50 `32.073696`，p95 `39.12716029999999`，p99 `43.01985879999996`，max `309.383421`，over_20ms `200`。预算仍是 20.0 |
| infer_ms | max `0.167103`，只含 `Policy::infer` |
| env_step_ms | p50 `29.651670018211007`，max `306.94921396207064`，missing 0 |

`COMPARE=1` 的 `total_ms` 含 RPC 之后写 dump 的记账，不是 20 ms 验收，也不是 50 Hz 墙钟验收。预算没有放宽。不要把 r4 的计时改标成这次的数。

## ONNX 对照

`compare_report.json` 的 status 是 `executed_not_acceptance`。`numeric_pass_bar` 为 null。200 步，`shape_mismatches` 0，`resimulated` false，provider 是 `CPUExecutionProvider`。dump SHA256 `f70270baa129573253249c30a240b25f84011ff6d73b222c262298eefa2811fb`。

绝对误差 max 0.0、mean 0.0、count 2800。相对误差 max 0.0、mean 0.0、count 2800。分母是 `max(|python_action|, 1e-12)`。零误差是记录，不是通过。

父进程在证据盒的 CPU 上用 onnxruntime 1.32.0 独立重放了同一份 dump 和同一份官方 ONNX（SHA `ce894d30…`），2800 个数的绝对误差和相对误差也正好是 0.0。原来那次用的是 official-rl 的 onnxruntime 1.24.4。

`wire_vs_rust` 的 max 是 `2.7755575615628914e-17`，这是 JSON 浮点灰，不是 ONNX 误差。`processed_vs_rust` 的 max 是 `0.45790000259876257`，那是 `env.step` 之后的植物项，不是 ONNX 输出，也没有拿来替换任何一边。

## 证据

- `/home/a/microduck-loop/evidence/2026-11-26/official-velstand-rust-onnx-compare/`
- `C:\Users\A\microduck-loop\evidence\2026-11-26\official-velstand-rust-onnx-compare\`
- `/workspace/microduck-loop-evidence/2026-11-26/official-velstand-rust-onnx-compare/`

`SHA256SUMS` 的 26 个文件全部 MATCH。`report.md` SHA256 `006bccd7f2c1c4eac507c279864265f768a45f0522b615554d0a9f9372beb2c6`。`SHA256SUMS` 文件本身是 `3b3769f2f552c9edc9c903921a302d503f461517b3ef9ea524652181369c00ab`。

证据盒上先前的 `report.md` 没有改：r1 `91d3e1d2fc046fa02c546fc554fdf0d59b9761d75fbbb060e3723470fb038075`，r2 `1d53171ca280d6b7656c701df2045a2589de3eaadf4540c4fba841891417f3e6`，r3 `98d7f55028fc8383d561a3614ec0b4e035d58710fd372424cd9b318efee5f5e8`，r4 `0c57ef705bd4bbf9ca279e836339138bb92fed943c42b09542a78f312f3f3b6e`，held-out `d40a7540af541722a53fcc42030b7aa296f48837983db1a44ed7685283be853a`。

AgentsDock 的 PID 25072、30748、41352、53128 在跑前和跑后都在，没有被杀掉。
