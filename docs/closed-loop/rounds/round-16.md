# 第 16 轮

结论：这是官方 BAM 先验盘点和可重放接线，不是评估跑程，也不是本机仿真。没有把任何格子标成通过或已执行。云端没有跑 HD 仿真。

## 先验

飞特官方仓 https://github.com/ftservo/ftservo-bam 与 https://gitee.com/ftservo/ftservo-bam 。两边 HEAD 都是 `bab3967811f0bec8b79898cb03e7f5812fe581f9`，作者 ftservo，2026-10-27 17:09:23 北京时间，Apache-2.0。

文件 `bam/params/feetech_hd1910_7_4V/m6.json`。675 字节。SHA256 `81a441fb921130bcc9bcfbd9ee0c77e3c38d9ab758bc7e0559fb029c436355ba`。内容自 `79eff6d5884227e12905f40ec3e8042cd4727b6f`（2026-09-26 22:27:12 北京时间）起未改。仓库归档是 `evidence/ftservo-hd1910-7_4V-m6/m6.json`，字节与这个哈希一致。

标记是 `manufacturer_identified`。只此 7.4 V 一档。`actuator` 字段是 `hd1910`。`kt` 用该库的 N·m/A，不与规格书 7.5 kg·cm/A 合成一个数。`armature` 是表观惯量 I，kg·m²。`command_delay` 是秒。`q_offset` 不是相对 XL330 的 HOME。JSON 里没有 `error_gain_ratio`。类常量 `vin=7.4`，`kp=32`，`error_gain=0.163`，`max_pwm=0.97`。

规格书 A/0 的 4.8 / 6 / 7.4 V 先验还在。自标 `sts3215` 的 JSON 和 XL330 m6 排除。不要使用 armature `0.00224`。

m1 到 m5 只记下哈希，条件仿真默认不用：m1 `1d3c1ca00f0ded75c4a3c38cbc1e678b9c3cf343bae1fd8acfa01f39992a19e2`；m2 `fa125815597e7eff15ca74cf5055f118027f0ae52caa0fa1b48420040d02b52e`；m3 `c583672e951b6f3bcab4cd791433644a7b9d98b44ea4f70be8239557172fbb47`；m4 `eab81d0dde2a61b92c1652daad029d4075d40c722356a315830a455ddd7ba5a4`；m5 `2e957de04d4429e7385436dfc4df432585eca1339e514feaab35e500ba084c83`。

## 接线

植物结构仍是官方 velstand 的 all-collisions + backlash + rough，物理 0.005 s、decimation 4。执行器换成隔离检出里的飞特 BAM：`motor_name=feetech_hd1910_7_4V`，`model=m6`，`kp_fw=32`。不用 XL330 的 `kp_fw=200`。

脚本 `scripts/closed_loop/run_hd1910_conditional_plant.sh` 和 sidecar `scripts/closed_loop/hd1910_conditional_plant.py` 自标 `hd1910_ftservo_official_m6_allcollisions_backlash_rough`。`import bam` 必须落在 `FTSERVO_BAM` 检出里，HEAD 必须是 `bab39678…`。不修改官方-rl 里钉死的 Rhoban BAM `62bd8ce12154340be97e06f7f41a0ca8f116d967`，也不把 PyPI `better-actuator-models==1.0.2` 当作这套参数的来源。

没有 `HD_CONDITIONAL_SIM_RUN=1` 时，脚本退出且不写跑程结果。本轮没有设置这个变量，所以没有仿真结果可以报告。

## 残余

- params README 没有台架、固件或轨迹记录。
- 不能外推到 4.8 V 或 6.0 V。
- 总线压降、电源内阻、固件限流、齿隙分布、连杆未称重质量与惯量、相对 XL330 的 HOME、本机 15 颗实测 ident，都还缺。
- 官方 velstand 配置里其余的执行器域随机（例如摩擦缩放、动作延迟步数）没有被当成 HD 实测。电压被钉在 7.4 V，避免沿用 XL330 的电压区间。
