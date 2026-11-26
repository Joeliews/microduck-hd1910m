# 第 13 轮

结论：接线已落地，本机还没有跑。不是通过，也不是 50 Hz 墙钟验收。这次提交没有在云端重跑 GPU，没有开始训练。

官方 `pollen-robotics/microduck_rl` `0daab160` 里没有 actor 对 ONNX 的数值通过线。`scripts/velstand_bench.py` 是行为电池，不是动作误差门限。所以对照脚本只记录绝对误差和相对误差，状态固定为 `executed_not_acceptance`。误差很小也不能写成通过。

## 对照协议

短闭环仍由 Rust `Policy::infer` 驱动官方植物 sidecar。植物仍必须是 `bam_m6_allcollisions_backlash_rough`：BAM M6、all-collisions backlash、rough，XML `robot_allcollisions_backlash.xml`。不是 XML-PD，也不是 `body_server`。

`COMPARE=1` 时，每一步在计时之外写下：

- 送给 `Policy::infer` 的 61 维观测，含 little-endian `f32` 位型
- Rust `Policy::infer` 的 14 维原始输出，含同样的位型
- sidecar 收到的 14 维动作，以及 `env.step` 之后植物项里的 processed 动作（若 mjlab 提供）

`infer_ms` 仍只包住 `Policy::infer`。计时起点仍在观测拼好之后、推理之前。20 ms 预算没有放宽，`over_20ms` 仍是 `total_ms > 20`。processed 动作不是 ONNX 输出，脚本不会拿它替换任何一边。

图内已有 Sub/Div。Rust 不再乘 `action_scale`。已发布 velstand 的 manifest `action_scale` 是 1.0。图是前馈 `obs[1,61] -> actions[1,14]`，输入名 `obs`，没有 LSTM。dump 里没有隐藏状态。Python 若发现 session 不是这一路前馈输入，就不编造 reset，也不编造隐藏状态。

Python 回放只读 `step_compare.json` 和同一份官方 ONNX。权重必须是 `ce894d30b3343036d499bfac1102bdaa58d59a21c1b58401ecb70fb6a2f63e0a`。短训导出 `cf280a27…` 会被拒绝。回放用 CPU ONNX Runtime，不新建植物，不调用 `env.step`。相对误差的分母是 `max(|python_action|, 1e-12)`。

`COMPARE` 默认是 0。不设置时不写 `step_compare.json`，步进请求也不带 echo，计时环的控制语义不变。

## 本机命令

云端没有执行下面的命令。

```bash
export MICRODUCK_RL_OFFICIAL=/home/a/microduck-loop/repos/microduck_rl
export OFFICIAL_RL_PYTHON=/path/to/official-rl/bin/python3
export ORT_DYLIB_PATH=/path/to/libonnxruntime.so
export ONNX=/path/to/verified/velstand.onnx
export OUT="$HOME/microduck-loop/evidence/2026-11-26/official-velstand-rust-onnx-compare"
export COMPARE=1
scripts/closed_loop/run_xl330_velstand_official_plant.sh
```

`ONNX` 必须显式指向已核对的官方副本，脚本不再默认 `/tmp/microduck-policies/velstand.onnx`。`MICRODUCK_RL_OFFICIAL` 必须是干净的 `0daab160`。`OUT` 默认是上面的新目录，并拒绝写入 `official-velstand-rust-official-plant`、`-r2`、`-r3`、`-r4`、`official-velstand-zero-shot`、`official-velstand-official-weight-heldout-10-11-12`。不要覆盖 r1–r4，也不要覆盖种子 0/1/2 或 10/11/12 的证据目录。

跑完后证据目录里应有 `step_compare.json`、`metrics.json` 里的 dump SHA，以及 `compare_report.json`。这些文件都不是通过。主机墙钟不是板端计时。4 秒短跑即使跑完也仍是 `executed_not_acceptance`。
