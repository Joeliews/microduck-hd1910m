# 第 7 轮

结论：`blocked`。不是一次实跑，因此也不是 `executed_not_acceptance`。

官方 BAM M6 + all-collisions backlash + mjlab rough 植物目前无法从 Rust 控制核心步进。没有跑官方植物的 Rust 闭环。4 秒平地 XML-PD 短闭环没有重跑，没有改标，也不是这份官方植物的证据。

云端虚机读不到本机证据目录。下面是已经独立核对的事实，没有另编数字。检查点、tar、ONNX 和大证据包都不进入仓库。

## 已核对

| 项 | 值 |
| --- | --- |
| 官方 `microduck_rl` 检出 | `0daab160d3fb1c2cbaba16a4a19052f36709dd9e` |
| BAM 锁 | `62bd8ce12154340be97e06f7f41a0ca8f116d967` |
| 官方 `body_server.py` SHA256 | `2040c827628c33fee998944bce1fcd456c4b993802bb473f016681688bff7b08` |
| 它的默认 `scene.xml` SHA256 | `9a85461121ba8273083c482c166f27e143ca386993b3ec8f8d97eb09aa257d31` |
| `robot_allcollisions_backlash.xml` SHA256 | `ccee92e435e39eefc64ee99745823751492ae7f948d835c89701710717e71de8` |
| 本机 `report.md` SHA256 | `f32764aa84e720e76701edbbc93e7d82efe5e4d8dad4782cc128299dc4f98bce` |

默认 `scene.xml` 包含 `robot_groundcontact.xml` 和一块平地平面。控制路径写 `data.ctrl`，并用 kp/200 缩放 XML 的 `actuator_gainprm` / `actuator_biasprm`。该文件没有 bam 导入，没有 BacklashEncoder，命令行没有 `--bam`、`--backlash` 或 `--rough`。

不存在 `scene_allcollisions_backlash.xml`。`scene_allcollisions.xml` 是没有 backlash 的平地。`scene_backlash.xml` 是 `robot_groundcontact_backlash.xml` 的平地。把 `--scene` 指到这些 XML 仍然是 XML 位置 PD，不能当成官方植物。

官方 runtime 的 `duck-control` 没有 mujoco 或 bam 依赖。`RemoteIo` 连接的是单独的 `body_server` 进程。`d61f9cb` 的进程内例子仍是平地 `scene_walk.xml` 的 XML-PD。

`0daab160` 上专门的多种子 bench 只有 `scripts/velstand_bench.py`。没有为 `alpha_stand` 或 `alpha_walking` 启动零样本，因为把它们丢进 velstand 植物会变成非正式评估。种子 10、11、12 仍预留。

## 本机证据路径

- `/home/a/microduck-loop/evidence/2026-11-26/official-velstand-rust-plant/`
- `C:\Users\A\microduck-loop\evidence\2026-11-26\official-velstand-rust-plant\`

## 缺的一步

还没有一次由 Rust 控制节拍驱动、植物确认为 BAM M6 + all-collisions backlash + rough 的短闭环。补上接线之后，仍要在本机官方检出上执行；云端没有用户的 RTX 5090，不能把没跑的结果写成已经跑过。
