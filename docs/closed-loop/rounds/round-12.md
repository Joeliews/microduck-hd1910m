# 第 12 轮

结论：`executed_not_acceptance`。不是通过。没有单独写成的数值通过线。16 环境/组和接触匹配溢出为 0 都不能改成通过。种子 0/1/2 的官方权重记录没有被这次覆盖。

本机在 DESKTOP-14410AL 的 Ubuntu 22.04 上，用已发布的官方 XL330 `velstand` ONNX，只跑了预留种子 10、11、12 的官方植物 held-out 零样本。没有提交运行产物。云端没有重跑 GPU。没有改 sidecar、Rust 或评估脚本。

云端虚机读不到本机证据目录。下面是已经独立核对的事实。不要覆盖 r1–r4，也不要覆盖种子 0/1/2 的官方权重目录。

## 环境

| 项 | 值 |
| --- | --- |
| 包装脚本墙钟 | 2026-11-26T21:06:45.775607+08:00 至 2026-11-26T21:12:48.688163+08:00 |
| 脚本 | started_at 21:06:46.668557+08:00，finished_at 21:12:47.409431+08:00，rc=0 |
| 包装脚本 | 复制了已有的官方包装，没有改写。SHA256 `f19a14d65c378993bae0b58b657f92a7c7dc84bff9d7e5f1cfbab10528aa8bbe`，与种子 0/1/2 那份相同 |
| 官方检出 | `/home/a/microduck-loop/repos/microduck_rl`，`0daab160d3fb1c2cbaba16a4a19052f36709dd9e`，跑前和跑后 dirty=0 |
| Python | official-rl，Python 3.12.16，torch 2.9.1+cu128。这次没有用 `official-cu` |
| BAM | `62bd8ce12154340be97e06f7f41a0ca8f116d967` |
| ONNX | 跑前 21:06:45.737955+08:00 的 SHA256 `ce894d30b3343036d499bfac1102bdaa58d59a21c1b58401ecb70fb6a2f63e0a`。新证据目录里的快照是同一个哈希。不是短训导出 `cf280a27…` |

命令是 official-rl 的 python 加上复制来的包装：`--onnx` 官方 `velstand.onnx`，`--seeds 10,11,12`，`--envs-per-group 16`，`--only probe,rise,push`，`--device cuda:0`。没有用官方默认的 32 环境/组。352 个环境。实际跑的种子是 10、11、12。

## 植物

`BamActuator model='m6' joints=14 envs=352 cuda:0`。`BacklashEncoderBamActuator` 14/14。`rough=True`。种子 10 / 11 / 12 对应 softened terrain geoms 1609 / 2333 / 2965。XML 是 `robot_allcollisions_backlash.xml`。物理步长 0.005，环境步长 0.02。没有 XML-PD 回退。

`zero-shot.log` 里接触匹配溢出是 0 行。种子 0/1/2 那次是 2295 行。这里只记录这个计数，不是通过。

## 父进程复算

父进程从 `metrics.json` 的 `results[seed].batteries` 复算了每一项 probe、rise、push。与 `metrics-summary.json` 完全一致，0 处不一致。

Probe 有 21 个已定义工况。coverage 字段写 22 组，是因为官方包装预留 `22*16` 个环境，和种子 0/1/2 那次一样。

### Probe

三个种子的站立跌倒都是 0%。高度 z 约为 0.1158 / 0.1155 / 0.1157 m。

唯一 `fell>0`、也是唯一超过 10% 行为线的 probe 工况，是种子 11 的直行 `vx0.4`，跌倒 12.5%，测得 vx 0.2213。其余直行速度指令都偏慢：指令 0.2 / 0.3 / 0.4，测得大约 0.094–0.096 / 0.151–0.177 / 0.221–0.225 m/s。

### Rise

`rec%` / `never_rose%` 按种子 10 / 11 / 12 列出，然后是平均 rec 和平均 never_rose。

| 家族 | 种子 10 / 11 / 12 | 平均 rec | 平均 never_rose |
| --- | --- | --- | --- |
| home face-down | 100/100/100 | 100 | 0 |
| home face-up | 100/100/100 | 100 | 0 |
| home side | 100/100/93.75 | 97.92 | 2.08 |
| rj face-down | 100/100/87.5 | 95.83 | 4.17 |
| rj face-up | 87.5/87.5/87.5 | 87.50 | 12.50 |
| rj side | 87.5/100/100 | 95.83 | 4.17 |

超过 10% 行为线的是：rj face-up，平均 never_rose 12.50%，三个种子都是 12.5%；种子 12 的 rj face-down 12.5%；种子 10 的 rj side 12.5%。

### Push

三个种子的 `pre_push_fell` 都是 0。`fell`、`rec_of_fell`、`up_at_end` 是数字，不是 nan。独立平均：

| 速度 | fell | rec_of_fell | up_at_end |
| --- | --- | --- | --- |
| 0.8 m/s | 54.1667 | 92.9630 | 93.75 |
| 1.0 m/s | 85.4167 | 87.2727 | 89.5833 |
| 1.2 m/s | 95.8333 | 89.1667 | 89.5833 |

九个种子×速度组的 `fell` 都大于 10，都没有达到 10% 行为线。

## 状态与耗时

`metrics.json` 的 status 是 `executed_not_acceptance`，`blocker` 为 null，`failures` 为 `[]`。没有致命或阶段失败。`failure_samples` 有 16 条，记的是非满分工况，其中包含 home side 6.25%，这条低于 10% 线。三个种子的墙钟是 119.74 / 118.27 / 111.79 s。

残余限制没有变：16 环境/组，不是官方默认的 32；没有单独写成的数值通过线；站立干净或溢出为 0 也不是通过。

## GPU

以 csv 为准。

| 时刻 | 显存 | 利用率 | 温度 | 功率 |
| --- | --- | --- | --- | --- |
| 跑前 `21:06:45.595166+08:00` | 4349 MiB | 6% | 40.10 C | 68.06 W |
| 运行中峰值 | 9391 MiB | 最高 80% | | 最高 154.4 W |
| 跑后 `21:12:48.712340+08:00` | 5081 MiB | 1% | 37.50 C | 91.94 W |

Windows 上 AgentsDock 的 PID 25072、30748、41352、53128 在跑前和跑后都在，没有被杀掉。

## 本机证据路径

- `/home/a/microduck-loop/evidence/2026-11-26/official-velstand-official-weight-heldout-10-11-12/`
- `C:\Users\A\microduck-loop\evidence\2026-11-26\official-velstand-official-weight-heldout-10-11-12\`
- `/workspace/microduck-loop-evidence/2026-11-26/official-velstand-official-weight-heldout-10-11-12/`

这次 `report.md` SHA256 `d40a7540af541722a53fcc42030b7aa296f48837983db1a44ed7685283be853a`。证据盒的 `SHA256SUMS` 全部 MATCH。`SHA256SUMS` 文件本身是 `e322c71a15351b54152d4e10fb0df77ef668542059c3fc39aea2ebff886ab048`。

r1–r4 的 `report.md` 仍是 `91d3e1d2fc046fa02c546fc554fdf0d59b9761d75fbbb060e3723470fb038075`、`1d53171ca280d6b7656c701df2045a2589de3eaadf4540c4fba841891417f3e6`、`98d7f55028fc8383d561a3614ec0b4e035d58710fd372424cd9b318efee5f5e8`、`0c57ef705bd4bbf9ca279e836339138bb92fed943c42b09542a78f312f3f3b6e`。
