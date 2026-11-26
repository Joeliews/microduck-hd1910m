# HD-1910 条件仿真假设

这是条件仿真的假设页，不是本机实测 ident，也不是实机验收。本轮只冻结先验并留下可重放接线，不在云端跑 HD 仿真，不把任何格子标成已执行或通过。

有两层先验，不要并成一个数。

- `spec`：飞特规格书 A/0（HD-1910-C001，2026-09-07）。4.8 / 6 / 7.4 V 都有堵转和空载点。与社区 wiki 不一致处不取平均。
- `manufacturer_identified`：飞特官方 BAM 仓里仅有的 7.4 V m6。不是本机台架重测。

自标 `actuator: sts3215` 的 `hd1910_1910_m6.json`、`radxa_1910_m6.json`，以及 XL330 的 m6，仍然排除。不要写二手解读里的 armature `0.00224`，那个数和文件不符。

## 制造商辨识（仅 7.4 V）

仓：https://github.com/ftservo/ftservo-bam 与 https://gitee.com/ftservo/ftservo-bam 。两边 HEAD 都是 `bab3967811f0bec8b79898cb03e7f5812fe581f9`，作者 ftservo，2026-10-27 17:09:23 北京时间，Apache-2.0。文件 `bam/params/feetech_hd1910_7_4V/m6.json`，675 字节，SHA256 `81a441fb921130bcc9bcfbd9ee0c77e3c38d9ab758bc7e0559fb029c436355ba`。内容自 `79eff6d5884227e12905f40ec3e8042cd4727b6f`（2026-09-26 22:27:12 北京时间）起未改。仓库里的字节副本在 `evidence/ftservo-hd1910-7_4V-m6/m6.json`。

params README 没有台架、固件或轨迹记录。不能把这一档外推成 4.8 V 或 6.0 V 的 BAM。

| 字段 | 原文 | 标记 |
| --- | --- | --- |
| kt | 0.5644993059031307 | manufacturer_identified。该库口径是 N·m/A，不是规格书的 7.5 kg·cm/A |
| R | 2.9664762312357853 | manufacturer_identified |
| armature | 0.0018273861091867637 | manufacturer_identified。BAM 文档中的表观惯量 I，kg·m²，转子惯量乘减速比平方 |
| q_offset | 0.008824155147854507 | manufacturer_identified。BAM 辨识零偏，不是相对 XL330 的 HOME |
| command_delay | 0.0009781055842204172 | manufacturer_identified。秒 |
| friction_base | 0.011950659296477161 | manufacturer_identified |
| friction_stribeck | 0.0 | manufacturer_identified |
| load_friction_motor | 0.3534653049182988 | manufacturer_identified |
| load_friction_external | 0.04335300722280222 | manufacturer_identified |
| load_friction_motor_stribeck | 1.6996676628765351e-06 | manufacturer_identified |
| load_friction_external_stribeck | 0.14250972390583813 | manufacturer_identified |
| load_friction_motor_quad | 0.006861907376104702 | manufacturer_identified |
| load_friction_external_quad | 0.009999951209775423 | manufacturer_identified |
| dtheta_stribeck | 0.716192604078371 | manufacturer_identified |
| alpha | 4.248291402139783 | manufacturer_identified |
| friction_viscous | 0.004767196924056633 | manufacturer_identified |
| model | m6 | manufacturer_identified。条件仿真默认只用 m6 |
| actuator | hd1910 | manufacturer_identified。注册表键是小写 `hd1910` |

`m6.json` 没有 `error_gain_ratio`。类常量在同一 SHA 的 `HD1910Actuator.__init__` 里，不在 JSON 中：`vin=7.4`，`kp=32`，`error_gain=0.163`，`max_pwm=0.97`。

其余档的 SHA256，只归档哈希，默认不用：m1 `1d3c1ca00f0ded75c4a3c38cbc1e678b9c3cf343bae1fd8acfa01f39992a19e2`；m2 `fa125815597e7eff15ca74cf5055f118027f0ae52caa0fa1b48420040d02b52e`；m3 `c583672e951b6f3bcab4cd791433644a7b9d98b44ea4f70be8239557172fbb47`；m4 `eab81d0dde2a61b92c1652daad029d4075d40c722356a315830a455ddd7ba5a4`；m5 `2e957de04d4429e7385436dfc4df432585eca1339e514feaab35e500ba084c83`。

## 规格书先验（4.8 / 6 / 7.4 V）

| 项 | 值 | 标记 | 随机化 |
| --- | --- | --- | --- |
| 工作电压 | 4–8.4 V | spec | 工作区间，不是已测分布 |
| 空载速度 | 0.137 / 0.109 / 0.088 s/60° @ 4.8 / 6 / 7.4 V | spec | 规格写明 ±10% |
| 堵转扭矩 | 9 / 12 / 15 kg·cm @ 4.8 / 6 / 7.4 V | spec | 规格写明 ±10% |
| 堵转电流 | 1.2 / 1.6 / 2 A @ 4.8 / 6 / 7.4 V | spec | 规格写明 ±10% |
| 空载电流 | ≤160 / ≤180 / ≤210 mA @ 4.8 / 6 / 7.4 V | spec | 上限，没有分布 |
| 额定负载 | 2.2 / 3 / 3.7 kg·cm @ 4.8 / 6 / 7.4 V | spec | 没有额外公差 |
| 额定电流 | 500 / 690 / 900 mA @ 4.8 / 6 / 7.4 V | spec | 没有额外公差 |
| Kt | 7.5 kg·cm/A | spec | 不换算，也不与 BAM 的 kt 合并 |
| 整机质量 | 21 ± 2 g | spec | ±2 g 是整机质量公差，不是输出轴惯量 |
| 外形 | 34 × 20 × 23 mm | spec | 外壳尺寸，不是连杆 CAD 尺寸 |
| 减速比 | 1/320 | spec | 无 |
| 齿隙上限 | ≤ 0.5° | spec | 上限，不是 15 只的分布 |
| 编码器 | 12 bit，0.088°，中位 2048 | spec | 无 |

网格和 URDF 仍只是 CAD/装配几何。本页不冻结任何谱系里没有写出的连杆长度、质量或惯量。

## 仍缺

| 项 | 标记 |
| --- | --- |
| 4.8 V 与 6.0 V 的 BAM 参数 | missing。不能用 7.4 V m6 外推 |
| 总线压降、电源内阻、固件限流 | missing |
| 齿隙分布 | missing。规格只有 ≤ 0.5° |
| 连杆未称重的质量与惯量 | missing。不编造 |
| 相对 XL330 的 HOME | missing。`q_offset` 不是这个量 |
| 本机 15 颗舵机的实测 ident | missing |
| 台架、固件、轨迹记录 | missing。params README 没有这些记录 |
| 扭矩-速度曲线 | missing。规格只有堵转点和额定点 |

条件仿真轨迹只表示「7.4 V 制造商辨识加规格书先验」。它不回写成本机 ident，也不填 20 格里的 HD-1910 行。接线见 `rounds/round-16.md`。实机前还要测的量见 `hd1910-pre-hardware-measurements.md`。
