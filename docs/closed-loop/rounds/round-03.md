# 第 3 轮

结论：`executed_not_acceptance`。不是通过。

云端虚机读不到本机证据目录，本文件只记录路径和已经与 `metrics.json` 复核过的数字，没有重跑，也没有另编数字。55MB 的 BAM tarball 不进入仓库。

## 范围

官方植物上的 XL330 `velstand` 多种子零样本：BAM M6，rough，all-collisions backlash。4 秒单种子平地 XML-PD 短评估仍然不是通过，只留作对照，见 `round-01.md` 与 `round-02.md`。

## 版本与合同

| 项 | 值 |
| --- | --- |
| 官方 `microduck_rl` 检出 | `0daab160d3fb1c2cbaba16a4a19052f36709dd9e` |
| 已发布 ONNX 的训练 commit | `53fb7d115b1be79c6d07e8fd4eab311285e16f2a`（只作记录） |
| BAM，以 `uv.lock` 为准 | `62bd8ce12154340be97e06f7f41a0ca8f116d967` |
| 旧文档里的 BAM 分支尖端 | `57d13ead53206a6bf0db3d66f86506ae8c2ce01a`。与 lockfile 不同，以 lockfile 为准 |
| 权重 SHA256 | `ce894d30b3343036d499bfac1102bdaa58d59a21c1b58401ecb70fb6a2f63e0a` |
| 任务 | `Mjlab-VelStand-Rough-Backlash-MicroDuck` |
| 控制 / 物理步长 | 0.02 s / 0.005 s |
| 种子 | 0、1、2 |
| 每组条数 | 16。官方默认 32 未用 |
| 地形开关 | 官方 bench 默认 `rough=False`。本轮 `rough=True`，且未改官方检出 |
| 墙钟 | 2026-11-26 17:12:46–17:18:49，北京时间 |
| 录像 | 无 |

## 本机证据路径

- `/home/a/microduck-loop/evidence/2026-11-26/official-velstand-zero-shot/`
- `C:\Users\A\microduck-loop\evidence\2026-11-26\official-velstand-zero-shot\`

## 独立审查后的指标

站立高度约 0.116 m，跌倒 0%。前进指令 0.2 / 0.3 / 0.4 m/s 的实测约 0.099 / 0.163 / 0.222 m/s。种子 1 的 straight vx 0.3 跌倒 6.25%。body z −2 cm 几乎无跟踪，dz 约 −0.88 mm。

起身恢复率：home face-down 100%，face-up 97.9%，side 100%。随机关节 face-down 93.8%，face-up 83.3%，side 89.6%。

行走中推扰 0.8 / 1.0 / 1.2 m/s：平均跌倒 47.9% / 87.5% / 87.5%，跌倒后恢复 87.0% / 97.9% / 90.7%，结束直立 93.8% / 97.9% / 91.7%。

2295 条 contact match overflow。

## 为什么不是通过

验收失败比例是 ≤10%。推扰跌倒率，以及随机关节面朝上起身（83.3%），都没有落在这条线内。前进速度也明显低于指令。本轮状态保持 `executed_not_acceptance`。
