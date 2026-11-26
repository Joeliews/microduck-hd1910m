# 第 17 轮

结论：自建验收标准已写下。不是一次评估，不是通过，也不是 `official_path`。九个策略的格子仍是未执行。

`0daab160` 没有它们的专门 ONNX bench。这不禁止本仓库自己按 `acceptance-criteria.md` 评。门槛没有降低：倾角 60°、高度 0.06 m、失败比例 10%、每颗预留种子至少 16 条 episode。held-out 种子是 20、21、22。细则在 `self-built-eval-protocol.md`。

不使用 `velstand_bench.py`。不把 `infer_policy.py`、`uv run play`、`play_latest.py`、`body_server` 或 `robotd --sim` 当成专门 bench。velstand 已有的官方植物记录不改。短训导出不覆盖官方权重格。

没有 manifest 或烘焙 `task_id` 的策略，Flat/Rough/Backlash 不能悄悄假定。roller 的烘焙任务号是 `Mjlab-Velocity-Swizzle-MicroDuck`，不是 stride rollers，但仍然必须用滑轮物理。BallKick 只有一个任务号。

随后的提交把入口放在 `scripts/closed_loop/self_built_eval.py`。没有 `SELF_BUILT_EVAL_RUN=1` 时不建环境、不写分数。授权之后若看不到 61 维部署观测，或不能确认命令接口，就停，不写通过。本机还没有跑。
