# 第 9 轮

结论：`failed`。不是通过，也不是 `executed_not_acceptance`。

本机用 PR HEAD `10defeb8dbf558ba4bcb0f140b96ecd4df28fb32` 重跑官方植物 Rust 短闭环。关节名修复已经生效。这次死在 `env.reset()`。没有 `metrics.json`，没有 20 ms 分位，没有高度或倾角。这些数不补造。4 秒 XML-PD 短闭环没有改标。先前 r1 目录没有覆盖，那里的 `report.md` 仍是 `91d3e1d2fc046fa02c546fc554fdf0d59b9761d75fbbb060e3723470fb038075`。

云端虚机读不到本机证据目录。下面是已经独立核对的事实。

## 环境

| 项 | 值 |
| --- | --- |
| 墙钟 | 2026-11-26 19:54:23–19:54:58，Asia/Shanghai（+08:00） |
| 机器 | Ubuntu 22.04 |
| Python | `OFFICIAL_RL_PYTHON`，official-rl 的 python3，torch 2.9.1+cu128 |
| 官方检出 | `0daab160d3fb1c2cbaba16a4a19052f36709dd9e`，干净，未改写 |
| BAM | `62bd8ce12154340be97e06f7f41a0ca8f116d967` |
| ONNX 跑前 SHA256 | `ce894d30b3343036d499bfac1102bdaa58d59a21c1b58401ecb70fb6a2f63e0a` |
| Fork | `10defeb8` 的全新解包 |
| Rust | `cargo +1.89.0` 编译 15.82 s |

## 植物已经 ready

`sidecar.log` 确认：

- `[rough terrain] spec_fn: softened 2241 terrain geoms (solref=0.04)`
- `[BamActuator] model='m6' joints=14 ... device=cuda:0`
- `[BacklashEncoderBamActuator] encoder-through-backlash feedback on 14/14 joints`
- Physics step-size 0.005，Environment step-size 0.02
- `ready port=43791 plant=bam_m6_allcollisions_backlash_rough commit=0daab160d3fb1c2cbaba16a4a19052f36709dd9e`

关节名那处没有再出现。

## reset 崩溃

随后在 `serve()` 的 `env.reset()` 处崩溃。原文：

```text
File ".../official_velstand_plant.py", line 222, in serve
    env.reset()
File ".../mjlab/envs/manager_based_rl_env.py", line 544, in _reset_idx
    self.curriculum_manager.compute(env_ids=env_ids)
File ".../microduck_rl/src/mjlab_microduck/tasks/mdp.py", line 3549, in push_curriculum
    event_cfg = env.event_manager.get_term_cfg(event_name)
ValueError: Event term 'topple_push' not found in active terms.
```

原因：sidecar 的 `build_env()` 仍然 `cfg.events.pop("push_robot" / "topple_push")`，但官方 `make_microduck_velstand_env_cfg` 在 `play=False` 时保留 `cfg.curriculum["topple_push_range"]`，其 `func=push_curriculum`、`params={"event_name": "topple_push", ...}`。reset 时课程项还在找已被删掉的事件。Rust 客户端报 `sidecar closed the connection`。这条错误路径不写 `metrics.json`。0 步。没有 XML-PD 回退。

## 本机证据路径

- `/home/a/microduck-loop/evidence/2026-11-26/official-velstand-rust-official-plant-r2/`
- `C:\Users\A\microduck-loop\evidence\2026-11-26\official-velstand-rust-official-plant-r2\`

`report.md` SHA256 `1d53171ca280d6b7656c701df2045a2589de3eaadf4540c4fba841891417f3e6`。

不要覆盖 r1（`official-velstand-rust-official-plant`）或这次的 r2。
