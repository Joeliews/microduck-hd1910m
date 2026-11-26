# 第 5 轮

结论：`executed_not_acceptance`。不是通过，不是 6000 轮全量，没有跑官方 bench，预留种子 10/11/12 未评估，也不声称修复了零样本失败。

云端虚机读不到本机证据目录。下面的数字来自已与 console 独立复核的训练日志，以及已从证据 tar 独立复核的哈希。没有重跑，也没有另编数字。检查点、tar、教师权重和 31MB 证据包都不进入仓库。

4 秒单种子平地 XML-PD、第 3 轮官方植物零样本、第 4 轮 2+2 冒烟，以及这次约 100 轮短训，都不是通过。

## 范围

从第 4 轮冒烟的 `model_2.pt` 续上，大约 100 轮官方 PPO。任务 `Mjlab-VelStand-Rough-Backlash-MicroDuck`。这是训练日志和检查点记录，不是行为评估。

## 版本与环境

| 项 | 值 |
| --- | --- |
| 官方 `microduck_rl` 检出 | `0daab160d3fb1c2cbaba16a4a19052f36709dd9e` |
| BAM，以 `uv.lock` 为准 | `62bd8ce12154340be97e06f7f41a0ca8f116d967` |
| 隔离环境 | `official-rl` |
| torch | 2.9.1+cu128 |
| 设备 | `cuda:0` |
| 并行环境数 | 512 |
| 训练种子 | 42 |
| 起点 | `--init-checkpoint` 指向冒烟 `model_2.pt` |
| 启动前哈希 | `85e693e185545ff26fb2bd1cdc85ab4c0df8ffcacdba8d5bb7ff6e013427cf41`，iter=2 |
| 加载日志 | 有 loading 该绝对路径 |
| 保存间隔 | `save-interval` 20 |

`learn(max_iterations=100)` 从已加载的 iter=2 往上加。实际日志是 Learning iteration 2/102 到 101/102，正好 100 轮且连续，iter 2 被重跑。

墙钟 2026-11-26 18:18:49–18:23:22，北京时间，273.3 s。rsl_rl 的 Time elapsed 在 101/102 为 00:04:21。迭代耗时 min / mean / max / sum = 2.19 / 2.6138 / 3.55 / 261.38 s。

## 选点训练日志

已与 console 独立复核。这是训练回报，不是评估。列顺序为 value、surrogate、entropy、expert_bc、reward、ep len、本轮秒。

| 轮 | value | surrogate | entropy | expert_bc | reward | ep len | 本轮秒 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2/102 | 11.2097 | 0.0724 | 19.7312 | 0.1247 | −7.37 | 20.24 | 3.55 |
| 20/102 | 7.2112 | −0.0152 | 19.477 | 0.1495 | −46.77 | 136.74 | 2.55 |
| 40/102 | 8.1477 | −0.0163 | 19.264 | 0.1272 | −43.32 | 123.52 | 2.64 |
| 60/102 | 10.7848 | −0.0157 | 19.1369 | 0.102 | −26.15 | 74.12 | 2.61 |
| 80/102 | 11.5309 | −0.0162 | 19.0351 | 0.1065 | −33.82 | 98.71 | 2.59 |
| 100/102 | 8.4958 | −0.0159 | 18.9888 | 0.0913 | −38.88 | 114.48 | 2.26 |
| 101/102 | 6.3328 | −0.0158 | 18.987 | 0.0905 | −38.88 | 114.48 | 2.22 |

训练回报变差：最好是开头 −7.37，最差是 iter 31 的 −52.86，结束 −38.88。不能当成策略变好。

## 检查点与导出

哈希已从证据 tar 独立复核。

| 文件 | iter | SHA256 |
| --- | ---: | --- |
| `model_20.pt` | 20 | `cac8d37d2bb6e12f0ee939579300b844aa657f7e9b5b3b43ed8e617ed0b24304` |
| `model_40.pt` | 40 | `7caa865ef04c18fda8723f0f69219a2cd6f57303617a4cb7e0599c94b4aa116f` |
| `model_60.pt` | 60 | `d604acf980746b5d86d1e2076728f8af44b1bb6cc053c36a63b0fe7e605c27b1` |
| `model_80.pt` | 80 | `75af990d6807400aa6e131d93334716ed8d3cbd1453db5336f665a56eeece412` |
| `model_100.pt` | 100 | `180d4eb88cbc0b52e8fb041dbec1d782a861fce5075ab05a7448091cc228c8aa` |
| `model_101.pt` | 101 | `9f9cdf842dfea169768f914188d0e1fe0b22631947f9c59e16a2e7f891d44b28` |

导出 ONNX `2026-11-26_10-18-49_short-100-resume.onnx` 的 SHA256 是 `cf280a273fa7d6bebea0c07104f5396038dfddd470e80339ca9a756a53d889a5`。它不是验收权重，不得写成官方 velstand `ce894d30b3343036d499bfac1102bdaa58d59a21c1b58401ecb70fb6a2f63e0a`。

events SHA256 `b8747623228a33ad040e23d3fa79e4c86667bb0b3eab34a40a86597183d9bb57`。

## GPU

独立解析样本。中段占用 8061–8082 MiB / 24455 MiB，利用率约 71–75%，功率 142–149 W。峰值占用 8082 MiB 在 18:19:43（72%，147 W）。跑前 4360 MiB / 6% / 69 W，跑后 4356 MiB / 6% / 65 W。

## 本机证据路径

- `/home/a/microduck-loop/evidence/2026-11-26/official-velstand-short-ppo-100/`
- `C:\Users\A\microduck-loop\evidence\2026-11-26\official-velstand-short-ppo-100\`

## 为什么不是通过

没有用预留种子 10/11/12 做行为复评，也没有跑官方 bench。第 3 轮零样本里过不了 10% 失败线的项没有用这次权重重测。训练回报从 −7.37 变到结束 −38.88。状态保持 `executed_not_acceptance`。
