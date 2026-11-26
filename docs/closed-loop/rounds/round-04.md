# 第 4 轮

结论：`executed_not_acceptance`。不是通过，也不声称修复了零样本失败。

云端虚机读不到本机证据目录。下面的数字来自已从证据 zip 独立复核的哈希和日志，没有重跑，也没有另编数字。检查点、zip、教师权重和 28MB 证据包都不进入仓库。

4 秒单种子平地 XML-PD、第 3 轮官方植物零样本，以及这次 2+2 轮短训冒烟，都不是通过。

## 范围

官方 PPO 短训冒烟，任务 `Mjlab-VelStand-Rough-Backlash-MicroDuck`。只证明这条命令能在隔离环境里走出两轮并写出检查点，再从检查点续上。不是验收复评。

## 版本与环境

| 项 | 值 |
| --- | --- |
| 官方 `microduck_rl` 检出 | `0daab160d3fb1c2cbaba16a4a19052f36709dd9e` |
| BAM，以 `uv.lock` 为准 | `62bd8ce12154340be97e06f7f41a0ca8f116d967` |
| 隔离环境 | `official-rl` |
| torch | 2.9.1+cu128 |
| 设备 | `cuda:0` |
| 并行环境数 | 512。官方评注用 4096，本轮未用 |
| 训练种子 | 42 |
| 轮数 | 官方默认 6000 轮并走 wandb。本轮改为 2 轮、`save-interval` 1、tensorboard |
| 独立评估种子 | 10、11、12 仍预留，本轮未评估 |

教师包因 WSL NAT 不能走 Windows 本机代理，在 Windows 下载后本地注入。哈希与各自 `bundle.json` 一致：

| 角色 | 文件 | SHA256 |
| --- | --- | --- |
| expert | `model_9750.pt` | `12bfcfddcdb4270e4cbbfb43554d0b14fbdad01263699cd97424e48e76b302fe` |
| anchor | `model_3750.pt` | `702c01bd02aeda1d7869390342e00298193e7071d475f3776e0a6eedfc5c8209` |

## Fresh

北京时间 2026-11-26 17:42:53–17:43:12，墙钟 18.46 s。

| 轮 | value | surrogate | entropy | expert_bc | mean reward | ep len | 本轮秒 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0/2 | 18.7825 | 0.0041 | 19.8328 | 0.1686 | −8.26 | 20.91 | 8.02 |
| 1/2 | 7.5206 | −0.0110 | 19.8177 | 0.4157 | −16.59 | 41.39 | 2.46 |

| 检查点 | iter | SHA256 |
| --- | ---: | --- |
| `model_0.pt` | 0 | `9b9656e61df9b7c2691d8f143e83eb4e64918cad858cdf293fca097c0787e219` |
| `model_1.pt` | 1 | `900ffc5041e57892087e5322a45d01d060f404fdcad203c1a7f0270a58e2686f` |

## Resume

官方 `--agent.resume --agent.load-checkpoint model_1.pt` 因 Windows CRLF 给文件名留下回车符而失败。改成 LF，并改用 `--init-checkpoint` 的绝对路径后恢复成功。

`learn(max_iterations)` 会从已加载的 iter 往上加，因此 iter 1 被重跑，日志显示 1/3 与 2/3。结束于 18:03:44 北京时间，墙钟 13.50 s。

| 轮 | value | surrogate | entropy | expert_bc | mean reward | ep len | 本轮秒 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1/3 | 13.6958 | −0.0092 | 19.7764 | 0.1175 | −7.37 | 19.91 | 3.58 |
| 2/3 | 7.0821 | 0.0063 | 19.7691 | 0.4121 | −14.95 | 38.35 | 2.51 |

| 检查点 | iter | SHA256 |
| --- | ---: | --- |
| resume `model_1.pt` | 1 | `6823d413442691458525446a84e94a4c3fce8fb23720d39ac46afc8dad973dd6` |
| `model_2.pt` | 2 | `85e693e185545ff26fb2bd1cdc85ab4c0df8ffcacdba8d5bb7ff6e013427cf41` |

resume 的 `model_1.pt` 与 fresh 的 `model_1.pt` 不是同一个哈希。以上哈希已从证据 zip 独立复核。

## GPU

中段峰值没有采到。最高观察到训练环境已构建时约 5270/24455 MiB。

## 本机证据路径

- `/home/a/microduck-loop/evidence/2026-11-26/official-velstand-short-ppo/`
- `C:\Users\A\microduck-loop\evidence\2026-11-26\official-velstand-short-ppo\`

## 为什么不是通过

两轮加续跑两轮只是冒烟。没有用独立种子 10/11/12 做行为复评，也没有把第 3 轮零样本里过不了 10% 失败线的推扰和随机关节面朝上起身重新测过。奖励在这两轮里变差，不能当成策略变好。状态保持 `executed_not_acceptance`。
