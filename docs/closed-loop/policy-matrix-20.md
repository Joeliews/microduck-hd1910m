# 20 格清单

2 个舵机 × 10 个官方策略。官方策略全部列入。轮滑两格（`roller`、`roller_crouch`）将来必须用带滑轮的物理；本轮没有跑。

状态只用这几个词：

- `摘录`：只抄了已验证的 ONNX SHA 和 manifest 合同，没有新跑仿真。
- `沿用离线对照`：store 里 Rust / Python 合成观测序列比特一致。不是 MuJoCo，不是 50 Hz。
- `短评估已记录`：本轮 CPU MuJoCo 跑过，见证据目录。不是通过。
- `未执行`：没有跑。空着，不填成通过。

通过线在 `acceptance-criteria.md`。本表没有一格是通过。

## 合同摘录（10 个策略共用）

权重目录的 SHA256 见 `version-freeze.md`。manifest：`obs` 61，`action` 14，`servos: xl330`，`control_hz: 50`。图为前馈 `obs[1,61] -> actions[1,14]`，无 LSTM。`roller` 与 `roller_crouch` 的 `action_scale` 为 0.8，且 `mode: roller`。

| 策略 | 种类 | SHA256 |
| --- | --- | --- |
| alpha_walking | perpetual | `e36332d383997d51401897734cd3e79cf5038406feddb18b4d57ecfb141daa6c` |
| velstand | perpetual，walk 槽，站立进入 | `ce894d30b3343036d499bfac1102bdaa58d59a21c1b58401ecb70fb6a2f63e0a` |
| alpha_stand | perpetual | `1569268713e40deea795dd2922dba50d3621e15a872855408b6b1b125b1c094b` |
| roller | perpetual，轮滑，scale 0.8 | `7b581097a9bc4782a695fd7654edb0c565649ad593ae439563ddf4b2b2e8a8c7` |
| alpha_sitstand | scripted | `a6f102d9fd655782ba85bfffe18175c34621da719cffcdd673be7982a06fc254` |
| alpha_ground_pick | episodic 2.8 s | `ffbf5109982ff999b0ba53afe86b9ae731bbec679d67fb7f8ab4c52152c88872` |
| roller_crouch | episodic 3.5 s，轮滑，scale 0.8 | `a1a084be240469c76ac9d3fa44d4792f16d4b1da60398b3ecd3cfc5e2244d990` |
| roulade | episodic 1.0 s，chain | `3d60da08fc13f29c1b57f41977aa898132c0d60042100149d8e775affcbca32b` |
| ball_kick_left | episodic 0.5 s | `d6928284dccd3dd61e08bf2f760effa74309fbefd97b2b31afb2a60f526d196a` |
| ball_kick_right | episodic 0.5 s | `147a32c388c6b19111b3ac3b550a9a6dc8b8bf267118af4d8c3712522eedb5af` |

## XL330

| 策略 | 物理要求 | ONNX / 合同 | MuJoCo 行为 | 零样本 | 重训检查点 | 导出数值对照 | Rust×MuJoCo 50 Hz |
| --- | --- | --- | --- | --- | --- | --- | --- |
| alpha_walking | 行走模型 | 摘录 | 未执行 | 未执行 | 未执行 | 沿用离线对照 | 未执行 |
| velstand | 训练植物是 rough + all-collisions backlash + BAM。本轮用的是平地 `scene_walk.xml` 位置 PD | 摘录 | 短评估已记录 | 短评估已记录 | 未执行 | 沿用离线对照 | 未执行 |
| alpha_stand | 站立模型 | 摘录 | 未执行 | 未执行 | 未执行 | 沿用离线对照 | 未执行 |
| roller | 必须是滑轮模型 | 摘录 | 未执行 | 未执行 | 未执行 | 沿用离线对照 | 未执行 |
| alpha_sitstand | 坐站相位 | 摘录 | 未执行 | 未执行 | 未执行 | 沿用离线对照 | 未执行 |
| alpha_ground_pick | 地面接触模型 | 摘录 | 未执行 | 未执行 | 未执行 | 沿用离线对照 | 未执行 |
| roller_crouch | 必须是滑轮模型 | 摘录 | 未执行 | 未执行 | 未执行 | 沿用离线对照 | 未执行 |
| roulade | 地面接触，可链式 | 摘录 | 未执行 | 未执行 | 未执行 | 沿用离线对照 | 未执行 |
| ball_kick_left | 含球模型 | 摘录 | 未执行 | 未执行 | 未执行 | 沿用离线对照 | 未执行 |
| ball_kick_right | 含球模型 | 摘录 | 未执行 | 未执行 | 未执行 | 沿用离线对照 | 未执行 |

XL330 `velstand` 的短评估证据：`evidence/xl330-velstand-cpu-r1/`。4 s 零命令最大倾角约 1.08°，1 s 时 0.3 m/s 脉冲最大倾角约 3.67°，两段躯干高度最低约 0.115 m，都没有跨过记录用的 60° / 0.05 m。这是 XML PD 平地上的单次确定性结果，不是 BAM 零样本通过，也不是多种子通过。

## HD-1910

10 格全部未执行。官方 ONNX 是 XL330 权值；HD-1910 上的零样本、重训和 Rust 环都还没有。参数缺口见 `servo-hd1910.md`。不要把上表 XL330 的短评估抄到 HD-1910。

| 策略 | ONNX / 合同 | MuJoCo 行为 | 零样本 | 重训检查点 | 导出数值对照 | Rust×MuJoCo 50 Hz |
| --- | --- | --- | --- | --- | --- | --- |
| alpha_walking | 摘录（仍是 XL330 权值） | 未执行 | 未执行 | 未执行 | 未执行 | 未执行 |
| velstand | 摘录（仍是 XL330 权值） | 未执行 | 未执行 | 未执行 | 未执行 | 未执行 |
| alpha_stand | 摘录 | 未执行 | 未执行 | 未执行 | 未执行 | 未执行 |
| roller | 摘录；若跑，必须用滑轮模型 | 未执行 | 未执行 | 未执行 | 未执行 | 未执行 |
| alpha_sitstand | 摘录 | 未执行 | 未执行 | 未执行 | 未执行 | 未执行 |
| alpha_ground_pick | 摘录 | 未执行 | 未执行 | 未执行 | 未执行 | 未执行 |
| roller_crouch | 摘录；若跑，必须用滑轮模型 | 未执行 | 未执行 | 未执行 | 未执行 | 未执行 |
| roulade | 摘录 | 未执行 | 未执行 | 未执行 | 未执行 | 未执行 |
| ball_kick_left | 摘录 | 未执行 | 未执行 | 未执行 | 未执行 | 未执行 |
| ball_kick_right | 摘录 | 未执行 | 未执行 | 未执行 | 未执行 | 未执行 |

HD-1910 行的「导出数值对照」是未执行：已有的离线对照是 XL330 官方 ONNX 的运行时对照，不是 HD 植物上的导出对照。
