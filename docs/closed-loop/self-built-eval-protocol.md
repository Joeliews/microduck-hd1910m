# 自建行为验收

这是本仓库的验收入口，不是官方脚本，也不是 `official_path`。`pollen-robotics/microduck_rl` `0daab160` 里，除 `velstand.onnx` 的 `scripts/velstand_bench.py` 以外，没有专门的 ONNX 行为 bench。没有官方路径，只说明还不能把官方脚本的结果填进格子，不说明这些格子不能评。

官方 runtime 钉在 `pollen-robotics/microduck`。训练栈钉在 `pollen-robotics/microduck_rl` `0daab160d3fb1c2cbaba16a4a19052f36709dd9e`。不要用本 Fork 的 `microduck_rl/`。不要把 `scripts/infer_policy.py`、`uv run play`、`play_latest.py`、`body_server` 或 `robotd --sim` 当成专门 bench。`infer_policy.py` 只是官方交互式 ONNX 排练。`0daab160` 里没有 `claude_experiments/sitstand_fallback_eval.py`，也没有 `velstand_rise_battery.py`。

不要把非 velstand 策略送进 `scripts/velstand_bench.py`，也不要送进 VelStand 植物。velstand 已经记下的官方植物多种子和种子 10/11/12 官方权重 held-out 保持原样。短训导出不得覆盖那些格子。

## 通过线（不降低）

沿用 `acceptance-criteria.md` 第 2、3 节。10% 失败比例是本仓库门槛，不是 Pollen 发布的官方通过线。

失败：统计窗内躯干倾角 > 60°，或躯干高度 < 0.06 m，或状态非有限值。

连续动作（`alpha_walking`、`alpha_stand`、`roller`）：每个预留种子至少 16 条 episode。每条命令族的失败比例 ≤ 10%，并且中位高度、倾角、失败比例都写入报告，才可以写行为通过。命令族固定为：零速度；前进 `vx=0.2`；侧向 `vy=0.15`；偏航 `vyaw=0.5`。水平速度脉冲用 `acceptance-criteria.md` 已经写下的 0.8 / 1.0 / 1.2 m/s。统计窗 8 s，3 s 之后再统计。这些幅值是本仓库冻结的口径，不是 `velstand_bench.py` 的官方命令表。

单次动作：相位用 manifest。坐站 ramp 2 s、unwind 1 s。拾取周期 4 s、结束相位 0.7、时长 2.8 s。轮滑蹲周期 5 s、结束相位 0.7、时长 3.5 s、部署 `action_scale` 0.8。翻滚时长 1.0 s。左右踢各 0.5 s。结束后再记至少 2 s 零命令恢复。相位段和恢复段都用上面的失败定义。任务量另记，不代替失败比例：坐站记高度曲线；拾取记最低手或嘴高度；翻滚记姿态角变化；踢球在有球模型时记球位移。

墙钟 20 ms 不是这一页的通过线。逻辑 50 Hz 也不写成墙钟通过。

## 预留种子

held-out 只用 20、21、22。三颗都要跑，不能只用一颗。不得把 velstand 的 0/1/2 或 10/11/12 目录改写成这次结果。选模若以后发生，不得使用 20/21/22。

本页写下标准时，这九个策略都还没有按此跑过。

## 任务号

有 manifest 或烘焙 `task_id` 的，必须用那一个，不能改成别的植物。

| 策略 | 任务 | 残余 |
| --- | --- | --- |
| alpha_walking | 无 manifest `training.task_id` | Flat/Rough/Backlash 未钉住。运行时必须显式给出任务号并写明这是未钉住的选择。文档里的速度配方 `441tzs6d` 是教师，不是这个 ONNX 的任务号。 |
| alpha_stand | 无 manifest `training.task_id` | 同上。站起环境 `69u48n8l` 是教师，不是这个 ONNX 的任务号。 |
| roller | 烘焙 `Mjlab-Velocity-Swizzle-MicroDuck` | 这是 swizzle，不是 stride rollers。部署 `action_scale` 0.8。仍必须是带滑轮的物理；若该任务号的 XML 没有滑轮，入口失败退出，不改用无轮模型，也不改用 VelStand。 |
| alpha_sitstand | manifest `Mjlab-SitStand-Flat-MicroDuck` | 无专门 ONNX bench。 |
| alpha_ground_pick | 注册表里有 GroundPick，周期 4.0；ONNX 无 `task_id` | 变体未钉住。必须显式给出任务号。 |
| roller_crouch | 注册表里有 RollerCrouch，周期 5.0；ONNX 无 `task_id` | 变体未钉住。必须显式给出任务号，且物理必须带滑轮。部署 `action_scale` 0.8。 |
| roulade | 注册表里见到的是 `Mjlab-Roulade-Flat-MicroDuck`；ONNX 无 `task_id`，也没有 backlash 孪生 | 产物本身没钉住。若选用上述任务号，报告里仍要写未钉住。时长用 1.0 s，不用 `infer_policy` 的默认 2.0 s。 |
| ball_kick_left / ball_kick_right | 只有 `Mjlab-BallKick-Flat-MicroDuck` | 没有左右分开的任务号。`KICK_FOOT` 默认 `"right"`。左踢必须显式把脚设为 left。时长用 0.5 s，不用 `infer_policy` 的默认 3.0 s。 |

入口找不到 61 维部署观测时必须停，不得用零观测或特权观测冒充。停下来的记录是 `blocked`，不是通过。
