# 第 6 轮

结论：`executed_not_acceptance`。不是通过。

测的是约 100 轮短训导出，不是官方已发布 velstand。行为和零样本格仍是官方权重在种子 0/1/2 上的记录，这次评估不覆盖那两格。

云端虚机读不到本机证据目录。下面的数字是从 `metrics.json` 独立重算的，没有重跑，也没有另编。检查点、tar、教师权重、ONNX 和评估日志都不进入仓库。

4 秒 XML-PD、官方植物零样本（官方权重）、2+2 冒烟、约 100 轮短训，以及这次预留种子评估，都不是通过。

## 测的是哪份权重

| 项 | 值 |
| --- | --- |
| 文件 | `2026-11-26_10-18-49_short-100-resume.onnx` |
| SHA256 | `cf280a273fa7d6bebea0c07104f5396038dfddd470e80339ca9a756a53d889a5` |
| 不是 | 官方 velstand `ce894d30b3343036d499bfac1102bdaa58d59a21c1b58401ecb70fb6a2f63e0a` |

## 环境

| 项 | 值 |
| --- | --- |
| 官方 `microduck_rl` 检出 | `0daab160d3fb1c2cbaba16a4a19052f36709dd9e` |
| BAM | `62bd8ce12154340be97e06f7f41a0ca8f116d967` |
| 任务 | `Mjlab-VelStand-Rough-Backlash-MicroDuck` |
| 环境 | `official-rl`，torch 2.9.1+cu128，`cuda:0` |
| 并行 | 352 环境，16 envs/group。官方默认 32 未用 |
| 地形 | `rough=True`，roller false |
| 控制步长 | 0.02 s |
| 种子 | 只使用 10、11、12 |
| 墙钟 | 2026-11-26 18:38:28–18:45:01，北京时间 |
| 各种子耗时 | 126.6 / 127.2 / 128.8 s |

日志无 traceback。0 条 contact match overflow。seed 10 的 probe 之后有 1 条 `EPA horizon = 24 isn't large enough`。

## 从 metrics.json 重算的数字

站立高度约 0.115 / 0.113 / 0.116 m，fell 93.75% / 87.50% / 93.75%，平均 91.67%。这些高度是 3 秒后幸存者的统计，不是稳定站立。

直行 vx 0.2 / 0.3 / 0.4 的平均 fell 是 93.75% / 100% / 100%。唯一有限速度是 seed 12、命令 0.2 m/s，测得约 0.000 m/s。

body z −2 cm 的平均 fell 是 66.67%。幸存者 dz 约 −4.1 / −9.1 / −4.1 mm。

起身平均 rec / never_rose（百分数）：

| 初态 | rec | never_rose |
| --- | ---: | ---: |
| home face-down | 31.25 | 0.00 |
| home face-up | 0.00 | 100.00 |
| home side | 10.42 | 62.50 |
| rj face-down | 16.67 | 0.00 |
| rj face-up | 2.08 | 77.08 |
| rj side | 4.17 | 64.58 |

推击（走路 vx=0.15）的 pre_push_fell 平均是 93.75% / 91.67% / 93.75%，对应速度 0.8 / 1.0 / 1.2 m/s。三个 `pre_push_fell=100` 的案件，official 的 fell / rec / up_at_end 为 nan：seed10@0.8、seed11@1.2、seed12@1.0。nan 不得当成 0，也不得拿来虚构均值。剩下有限的案例也很差。

`failures.json` 有 87 条。这 3 个 nan 推击案件因为 fell>0 的过滤没有列入，但它们仍是失败，见 `metrics.json`。

## 对照，不是过关线

官方 `velstand.onnx`、种子 0/1/2、同一植物、同样 16/group：站立 fell 0%，测得前向约 0.099 / 0.163 / 0.222 m/s，起身更高，推击平均 fell 47.9% / 87.5% / 87.5%，且 pre_push_fell=0。这是另一份权重、另一组种子，不能把短训导出写成已经追上官方权重，也不能把官方权重那一格改成通过。

## 本机证据路径

- `/home/a/microduck-loop/evidence/2026-11-26/official-velstand-short-ppo-100-eval/`
- `C:\Users\A\microduck-loop\evidence\2026-11-26\official-velstand-short-ppo-100-eval\`

## 为什么不是通过

站立平均跌倒 91.67%，直行几乎全部跌倒，起身和推击都远差于 10% 失败线。状态保持 `executed_not_acceptance`。
