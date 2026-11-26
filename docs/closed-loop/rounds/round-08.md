# 第 8 轮

结论：`failed`。不是通过，也不是 `executed_not_acceptance`。

本机用 PR HEAD `f3b5cfe4f7e79fd29ad945dd38c85f4d83138ca9` 跑官方植物 Rust 短闭环，在 `ready`、hello 和 `env.step` 之前就停了。Rust 客户端编过，但没有启动。没有 `metrics.json`，没有 20 ms 分位，没有高度或倾角。这些数不补造。4 秒 XML-PD 短闭环没有改标。

云端虚机读不到本机证据目录。下面是已经独立核对的事实。

## 环境

| 项 | 值 |
| --- | --- |
| 墙钟 | 2026-11-26 19:34:50–19:35:32，Asia/Shanghai（+08:00） |
| 机器 | Ubuntu 22.04 |
| Python | official-rl 的 `python3`，torch 2.9.1+cu128 |
| 官方检出 | `0daab160d3fb1c2cbaba16a4a19052f36709dd9e`，干净，未改写 |
| BAM | `62bd8ce12154340be97e06f7f41a0ca8f116d967` |
| ONNX 跑前 SHA256 | `ce894d30b3343036d499bfac1102bdaa58d59a21c1b58401ecb70fb6a2f63e0a` |
| Rust | `cargo +1.89.0` 编译 21.61 s，客户端未启动 |

## sidecar 已经建起植物，然后崩溃

独立从 `sidecar.log` 读到：

- `Setting seed: 0`
- `[rough terrain] spec_fn: softened 2241 terrain geoms (solref=0.04)`
- `[BamActuator] model='m6' joints=14 ... envs=1 device=cuda:0`
- `[BacklashEncoderBamActuator] encoder-through-backlash feedback on 14/14 joints`
- Physics step-size 0.005，Environment step-size 0.02

没有 `ready port=`。

异常原文：

```text
File ".../official_velstand_plant.py", line 157, in serve
    action_names = list(getattr(term, "joint_names", None) or term._joint_names)
AttributeError: 'JointPositionAction' object has no attribute '_joint_names'
```

本机只读检查确认 official-rl 的 `mjlab.envs.mdp.actions.actions.JointPositionAction` 使用 `_target_ids` / `_entity`，没有 `joint_names` 或 `_joint_names`。`f3b5cfe4` 的 sidecar 没有被当场改过再跑。

## 本机证据路径

- `/home/a/microduck-loop/evidence/2026-11-26/official-velstand-rust-official-plant/`
- `C:\Users\A\microduck-loop\evidence\2026-11-26\official-velstand-rust-official-plant\`

`report.md` SHA256 `91d3e1d2fc046fa02c546fc554fdf0d59b9761d75fbbb060e3723470fb038075`。

## 还缺什么

关节名解析修好之后，仍要在本机用 official-rl 的 Python 和同一官方检出重跑。云端没有这次重跑，不能写成已经成功。
