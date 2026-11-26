# XL330 参数冻结

官方策略的舵机是 XL330。训练配置写的是 `motor_name="xl330"`、`model="m6"`，没有在 `microduck_constants.py` 里写 M288 或 M077。下面规格按 ROBOTIS XL330-M288-T 摘录，因为商品页和 e-Manual 的控制表电流上限 1750 mA 与运行时注释一致；仓库里另有分支 `xl330m077t`，本轮没有打开实物，所以「装机就是 M288」仍是规格候选，不是实测确认。

## 训练执行器（官方，冻结）

出处：`pollen-robotics/microduck_rl` @ `53fb7d115b1be79c6d07e8fd4eab311285e16f2a` 的 `microduck_constants.py`，以及 Rhoban/bam @ `57d13ead53206a6bf0db3d66f86506ae8c2ce01a` 分支 `mjlab_frictionloss` 的 `bam/params/xl330/m6.json`。

训练侧固定参数：

| 项 | 值 | 标记 |
| --- | --- | --- |
| `kp_fw` | 200 | 官方代码 |
| `vin_range` | (6.5, 8.2) V | 官方代码。高于下面的规格电压上限 |
| `vin_drop_gain_range` | (0.0, 0.2) | 官方代码 |
| `vin_min` | 6.0 V | 官方代码 |
| `delay_min_lag` / `delay_max_lag` | 3 / 6 | 官方代码。单位按 mjlab 延迟执行器的步，本文件不换算成毫秒 |
| `max_current` | 源码里注释掉的 1.75 | 官方代码里未启用该行 |

BAM `m6.json`（`mjlab_frictionloss` @ `57d13ead`，`actuator` 字段为 `xl330`）：

| 字段 | 值 |
| --- | --- |
| kt | 0.36601349688984386 |
| R | 2.8113923539223227 |
| armature | 0.0018077432831600838 |
| q_offset | 0.0271132870444849 |
| friction_base | 0.004771183165566 |
| friction_stribeck | 0.004676345799486616 |
| load_friction_motor | 0.2667860954283698 |
| load_friction_external | 8.515871897059342e-06 |
| load_friction_motor_stribeck | 1.0722918395099123e-05 |
| load_friction_external_stribeck | 0.08077928978935671 |
| load_friction_motor_quad | 0.009972471242139415 |
| load_friction_external_quad | 0.004902565732332559 |
| dtheta_stribeck | 2.890372094130307 |
| alpha | 8.683259907618984 |
| friction_viscous | 0.005359668274599504 |

这些是 BAM 辨识参数，标记为官方训练依赖里的辨识文件，不是本仓库对某一台舵机的新测量。Rhoban/bam 默认分支上的同名 JSON 数值不同（含 `command_delay`，kt 约 0.346），不纳入这次冻结。

## 部署侧（官方 runtime @ `4024f6ee`）

| 项 | 值 | 标记 |
| --- | --- | --- |
| 行走 `action_scale` | 0.9 | 官方代码，Walk 模式默认 |
| 站立 `standing_action_scale` | 1.0 | 官方代码 |
| 轮滑 `action_scale` | 0.8 | 官方代码，且 manifest 对 `roller` / `roller_crouch` 再写 0.8 |
| 头低通 | 0.5 | 官方 `Tuning` 默认。短评估没有加 |
| 腿低通 | 0.7 | 官方 `Tuning` 默认。短评估没有加 |
| `gain` | 200 | 官方代码，与 `kp_fw` 同数 |
| `CURRENT_LIMIT_MA` | 1000 | 官方代码。注释写明出厂是 1750，鸭子行走这套 ONNX 时用 1000 |
| `MOTOR_MAX_V` | 6.0 | 官方代码。用 Goal PWM 把电机电压帽在约 6 V |
| 电池可用窗口 | 6.6–8.2 V | 官方代码，总线电压，不是规格书电压 |

## 规格（XL330-M288-T）

出处：ROBOTIS 商品页 `en.robotis.com` item `902-0163-000`，以及 e-Manual `ROBOTIS-GIT/emanual` `docs/en/dxl/x/xl330-m288.md`。商品页与手册在堵转电流的舍入上不完全相同，表内分列。

| 项 | 值 | 标记 |
| --- | --- | --- |
| 电压 | 3.7–6.0 V，推荐 5.0 V | 规格 |
| 堵转扭矩 | 0.42 / 0.52 / 0.60 N·m @ 3.7 / 5.0 / 6.0 V | 规格 |
| 堵转电流 | 商品页在 5.0 V 写 1.5 A；手册对照表写 1.11 / 1.47 / 1.74 A @ 3.7 / 5.0 / 6.0 V | 规格，两处不一致，不取平均 |
| 空载转速 | 76 / 103 / 123 rpm @ 3.7 / 5.0 / 6.0 V（手册对照表）；商品页在 5.0 V 写 104 rpm | 规格，两处不一致 |
| 减速比 | 288.4 : 1 | 规格 |
| 编码器 | 12 bit，4096 pulse/rev，ams AS5601 | 规格 |
| 重量 | 18 g | 规格 |
| 尺寸 | 20 × 34 × 26 mm | 规格 |
| 齿轮 | 工程塑料直齿 | 规格 |
| 电流上限寄存器 | 出厂 1750 mA | 规格（控制表） |
| 齿隙 | 商品页为「-」，无角度数 | 缺失 |

训练用的 `vin_range` (6.5, 8.2) 超出规格上限 6.0 V。运行时 `MOTOR_MAX_V = 6.0` 是另一层限制。仿真若沿用训练范围，必须写成训练配置，不能写成规格允许。

## XML 位置执行器（短评估实际用到的，不是训练执行器）

`robot_walk.xml` 的 `chosen_actuator`：阻尼 0.053，frictionloss 0.0048，armature 0.0018，position `kp=0.55`，`forcerange` ±0.96。注释写「200 kp」。这是导出 MJCF 里的 PD，BAM 在 mjlab 里会换掉它。短评估用的就是这一层。

## HOME 与关节顺序

策略 14 维，不含嘴。顺序与官方 `obs.rs` 一致：

`left_hip_yaw, left_hip_roll, left_hip_pitch, left_knee, left_ankle, neck_pitch, head_pitch, head_yaw, head_roll, right_hip_yaw, right_hip_roll, right_hip_pitch, right_knee, right_ankle`

`model.rs` 的 `DEFAULT_POSITION`（嘴为 0，已跳过）与 MJCF `STAND` 关键帧最大绝对差 4e-5 rad。短评估的 HOME 取关键帧，观测相对这个 HOME。零命令时初始 `obs[3:6] = [0, 0, -1]`，相对关节位置为 0。

动作：`ctrl = STAND + action_scale * action`。短评估的站立零命令用 `action_scale = 1.0`。ONNX 字节里含 `Sub`、`Div`、`Gemm`、`Elu` 字符串，与官方 `velstand_bench.py` 描述的图内归一化一致；脚本没有在图外再归一化一次。
