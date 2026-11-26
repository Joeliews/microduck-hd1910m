# 20 格清单

2 个舵机 × 10 个官方策略。官方策略全部列入。轮滑两格（`roller`、`roller_crouch`）将来必须用带滑轮的物理；本轮没有跑。

状态只用这几个词：

- `摘录`：只抄了已验证的 ONNX SHA 和 manifest 合同，没有新跑仿真。
- `沿用离线对照`：store 里 Rust / Python 合成观测序列比特一致。不是 MuJoCo，不是 50 Hz。
- `短评估已记录`：Python 侧 CPU MuJoCo 跑过，见证据目录。不是通过。
- `短闭环已记录`：Rust 控制核心调用了 `mj_step`。不是通过。
- `官方植物多种子已记录（未通过）`：官方 bench 植物上的多种子零样本已记录。不是通过。
- `短训冒烟已记录（未通过）`：官方 PPO 只跑了 2+2 轮冒烟。不是通过，也不表示零样本失败已修好。
- `约100轮短训已记录（预留种子评估未通过）`：从冒烟检查点续上约 100 轮，并用预留种子评过短训导出。不是通过。该导出不是官方 velstand，不覆盖官方权重的行为/零样本格。
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
| velstand | 第 3 轮是 BAM M6 + rough + all-collisions backlash。先前云端短跑仍是平地 XML-PD，只作对照 | 摘录 | 官方植物多种子已记录（未通过） | 官方植物多种子已记录（未通过） | 约100轮短训已记录（预留种子评估未通过） | 沿用离线对照 | 短闭环已记录（XML-PD，非通过；官方植物本机短闭环在 ready 前失败（JointPositionAction 关节名）；接线待修） |
| alpha_stand | 站立模型 | 摘录 | 未执行 | 未执行 | 未执行 | 沿用离线对照 | 未执行 |
| roller | 必须是滑轮模型 | 摘录 | 未执行 | 未执行 | 未执行 | 沿用离线对照 | 未执行 |
| alpha_sitstand | 坐站相位 | 摘录 | 未执行 | 未执行 | 未执行 | 沿用离线对照 | 未执行 |
| alpha_ground_pick | 地面接触模型 | 摘录 | 未执行 | 未执行 | 未执行 | 沿用离线对照 | 未执行 |
| roller_crouch | 必须是滑轮模型 | 摘录 | 未执行 | 未执行 | 未执行 | 沿用离线对照 | 未执行 |
| roulade | 地面接触，可链式 | 摘录 | 未执行 | 未执行 | 未执行 | 沿用离线对照 | 未执行 |
| ball_kick_left | 含球模型 | 摘录 | 未执行 | 未执行 | 未执行 | 沿用离线对照 | 未执行 |
| ball_kick_right | 含球模型 | 摘录 | 未执行 | 未执行 | 未执行 | 沿用离线对照 | 未执行 |

XL330 `velstand` 的 Python 短评估仍是 `evidence/xl330-velstand-cpu-r1/`，没有重跑，也不是通过。Rust 闭环是 `evidence/xl330-velstand-rust-r1/`，见 `rounds/round-02.md`，仍是「短闭环已记录（XML-PD，非通过）」。官方植物多种子零样本见 `rounds/round-03.md`，结论 `executed_not_acceptance`，不是通过。第 4 轮短训冒烟见 `rounds/round-04.md`，第 5 轮约 100 轮续训见 `rounds/round-05.md`，第 6 轮预留种子评估见 `rounds/round-06.md`。三轮结论都是 `executed_not_acceptance`。第 7 轮见 `rounds/round-07.md`，结论是 `blocked`。第 8 轮见 `rounds/round-08.md`，结论是 `failed`：官方植物在 `ready` 前因 `JointPositionAction` 没有 `_joint_names` 而停住，没有 20 ms 分位。XML-PD 短闭环不是那份植物的证据。行为和零样本仍是官方已发布权重、种子 0/1/2 的结果，不是短训导出 `cf280a27…`。表中没有一格是通过。

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
