# 项目开发进度记录

> BCI × Anima — Intention to Action 演示项目的纵向进度日志。每个版本段包含：目标、做了什么、关键决策（尤其是 pivot）、验收结果、commit 锚点。
>
> **全景路线图**见 `planning/11-execution-roadmap.md`；本文件只记录"已发生"与"进行中"。

---

## 版本概览

| 版本 | 核心产出 | 状态 | 锚点 commit |
|---|---|---|---|
| v0.1 | 场景 1「我想喝水」Anima 五层全栈本地跑通（mock skills） | 完成 | `bfe6efa` |
| v0.2 | 实时 MuJoCo + 自主 Stretch 技能 + Hetzner 常驻 + MJPEG 网页直播 | 完成 | `ca6756a` |
| v0.3 | 产品重设计：MuJoCo 主视图 + Anima 折叠抽屉 + 真实病房场景 | 进行中 | — |
| v0.4 | 场景 2-6 分支 + 真实失败叙事 | 未开始 | — |
| v1.0 | Hillsboro 产品着陆页 + 域名 + 两页 PDF（PRD + FMEA） | 未开始 | — |
| v1.1 | Anima 分仓为独立 OSS + 论文 | 未开始 | — |

---

## v0.1 — Anima 五层全栈本地跑通（mock skills）

**目标**：端到端证明 Anima 认知框架（5 层 L0-L5 + 5 因素 ITA/MQA/SQA/GOA/PEA + LLM-as-Parser）可以驱动一个 BCI 风格的 Intent-to-Action 闭环，场景选最典型的「我想喝水」。机器人动作不上物理引擎，用 mock skill 代替。

**做了什么**：

- FastAPI 骨架（`demo/core`，uv + Python 3.12，`:8765`），DeepSeek provider 走 `deepseek-chat`
- Pydantic 模型：`TaskSpec` / `IntentToken` / `FiveFactors`
- **L0 Input**：文本特征抽取 + 装饰性 256 通道波形（text-hash 种子，UI 明确标注 "decorative only — intent derived from text via LLM parser"）
- **L1 Intent Parser**：DeepSeek 强制 tool-call → `IntentToken`（35 词词表）
- **L2-L5**：`py_trees` 行为树 Sequence + mock skill 节点（`MockSkillBehaviour`）+ 五因素事件触发评估（PEA 写入 `demo/core/src/storage/pea_log.jsonl`）
- HTTP + WebSocket 路由（`/api/intent`、`/ws`），所有 L0-L5 事件走单条 WebSocket 驱动前端动画
- Next.js 16 前端（`demo/web`，Tailwind + zustand + ReactFlow，`:3000`），7 个关键组件：
  - `LayerStack`（左栏层级指示）
  - `IntentInput` / `SignalWaveform` / `TaskSpecPanel` / `IntentTokenStream`（中栏意图链）
  - `BehaviorTreeFlow`（行为树可视化）
  - `FiveFactorPanel`（右栏评估）

**关键决策（v0.1 阶段固化）**：

- **D7 修订**：L0 不做假神经解码，改成「自然语言输入 + LLM Parser → Intent Token」。彻底规避假数据，LLM-as-Parser 正是 Anima 核心 IP
- **D18**：装饰波形保留作为视觉元素，UI 明确标注 decorative，诚信 + 美感双保
- **D1**：DeepSeek 作为默认 LLM（100% OpenAI API 兼容，后续可切换）
- **D5**：Python FastAPI + Next.js monorepo（为 ROS 2 未来留通路，实际在 v0.2 被 pivot 掉了——见下节）
- **D12**：2D 临床仪表盘为主屏（3D 仿真次屏推到 v0.2）

**验收**：本地 `uv run uvicorn` + `npm run dev` 双进程；输入"我想喝水"→ L0-L5 依次高亮 → TaskSpec `DRINK_WATER` confidence > 0.8 → BT 五节点 sky→green → 五因素实时更新 → PEA 落盘。

**commit 锚点**：
- `87e1d3b` feat(core): FastAPI scaffold + DeepSeek provider
- `2ee8a64` feat(core): Pydantic TaskSpec/IntentToken/FiveFactors models
- `76faa50` feat(l0): decorative waveform + text feature extractor
- `0209247` feat(l1): LLM Intent Parser with tool use
- `6f1d3a7` feat(l2-l5): py_trees behavior tree + 5-factor assessment
- `048b124` feat(core): HTTP + WebSocket routes
- `0421d82` feat(web): Next.js scaffold + zustand + ws client
- `0a033d7` feat(web): 7 key UI components for scene 1
- `bfe6efa` chore: v0.1 E2E verified + README

---

## v0.2 — 实时 MuJoCo + 自主 Stretch 技能 + Hetzner 常驻

**目标**：让面试官打开一个网页，左边看 Stretch RE3 在病房场景里**真实自主地**抓水、送到病床旁；右边看 Anima L0-L5 实时运行 + 五因素。整套部署在 Hetzner `anima-robot-cloud`（`dev.jeffliulab.com`，Cloudflare 前置 + ufw 锁源）。

### Pivot 2026-04-20（v0.2 中途决策）

**原方案**（`planning/15-3d-simulation-design.md`）= Docker + ROS 2 Humble + Gazebo Harmonic + MoveIt 2 + Nav2。

**执行时发现的问题**：

1. `hello-robot` 不提供 `stretch_moveit2` apt 包或 GitHub 配置，要自己写 SRDF + kinematics config（3-5h 工作量）
2. `stretch_mujoco` Python API 已完全够用：
   - `sim.pull_camera_data()` → RGB 帧
   - `sim.move_to(Actuators.lift, pos)` + `wait_until_at_setpoint` → 关节位置控制
   - `sim.set_base_velocity(v, ω)` → 底盘速度
   - Stretch 臂只有 5 DoF（lift Z + arm 伸缩 + wrist yaw/pitch/roll），**分析 IK 10 行以内搞定**
3. Nav2 对封闭小场景（单房间 + 走廊）过重

**新方案**：纯 Python `stretch_mujoco` API + 分析 IK + unicycle PID。Anima L3 skill 直接调 `stretch_mujoco`，不启动任何 ROS 节点。ROS 2 Humble + stretch_ros2 workspace 保留不删（v1.x 如果接真机会用到）。

**为什么这是对的**：

- 开发体验 bonus：MuJoCo 原生支持 macOS，Mac 本地也能跑，不受制于 VSCode Remote SSH
- Hetzner 部署简化：无 ROS，只 FastAPI + Next.js + MuJoCo 三进程
- 保留"真自主"语义：每次运行都从 MJCF 查 cup 位姿 + 算 IK + 步进物理，**不是脚本重放**
- 未来接真机路径未被堵死：v1.x 想上 ROS 可以把 `SimSkillBehaviour` 换成 `Ros2SkillBehaviour`，上层 `py_trees` 零改

### 实际实现

**新增后端模块**（`demo/core/src`）：

- `sim/manager.py` — 持有 `StretchMujocoSimulator` + 自己渲染 `demo_view` 第三人称相机（`stretch_mujoco` 的 camera pipeline 不暴露自定义 MJCF 相机，所以绕过）
- `routes/sim.py` — `/api/sim/mjpeg`（multipart MJPEG 流）+ `/api/sim/reset` + `/api/sim/status`
- `anima/l3_skill.py` — `SimSkillBehaviour` 基类 + 6 个具体 skill：`locate` / `navigate` / `grasp` / `lift` / `deliver` / `release`。六个 skill 共享一个 blackboard dict；`NavigateSkill` 用 unicycle PID + align/approach 两段 hysteresis
- `anima/l2_planner.py` — sim 不可用时自动回落到 v0.1 的 `MockSkillBehaviour`（保证本地零配置也能跑）
- `l5_assessment.py` — `p_skill` 从固定 0.91 改成 skill 真实成功率滑窗（从 `pea_log.jsonl` 读）

**新增前端组件**：

- `demo/web/src/components/center/SimulationView.tsx` — `<img>` MJPEG + Reset 按钮
- `app/page.tsx` 布局从 3 列改成 4 列（nav / sim live / intent+BT / factors）

**部署**：Hetzner（`dev.jeffliulab.com`），systemd 三单元 + nginx 反代（`/` → Next.js prod，`/api` → FastAPI，`/ws` → FastAPI upgrade；`/api/sim/` 关 buffering）。

### 验收

冷启动 E2E（E2E 脚本见 `planning/11` §Verification）：

- 打开 `https://dev.jeffliulab.com` 看到病房场景（床、床头柜、水杯、Stretch 初始位）
- 文本框输入"我想喝水"→ L0→L5 依次高亮 → TaskSpec `DRINK_WATER` → BT 六节点 sky→green
- MJPEG 实时看到 Stretch 自主导航 → 臂伸到杯 → 合爪 → 抬起 → 返回床边（**非脚本重放**，每次 IK 重新算）
- 五因素数值随过程更新；PEA 新增一行 outcome=success
- Reset Sim 按钮 → 2 秒内场景归位

### v0.2 非目标（已推到后续版本）

- 场景 2-6 的 Anima 分支逻辑 → v0.3
- 失败 fallback 叙事 → v0.3
- 其他 5 段视频 → v0.4
- 正式域名 + HTTPS + 产品着陆页 → v1.0
- Anima OSS 分仓 → v1.1

**commit 锚点**：`ca6756a` feat(v0.2): live MuJoCo sim + autonomous Stretch skills + Hetzner deploy

**详细执行计划**：`~/.claude/plans/lively-juggling-kettle.md`（包含 S1-S9 步骤 + 风险预案 + pivot 完整推理）。

---

## v0.3 — 产品重设计（进行中）

**触发原因**：v0.2 以「技术跑通」为导向，UI 是「Anima 仪表盘 + 仿真窗口」的 4 列布局。但这个岗位是**产品岗**，面试官第一眼要看到的是**产品**，不是技术架构。需要重新设计信息层级。

**目标**：

- MuJoCo 实时画面成为**主视觉**（占屏比 >60%），模拟真实护理机器人产品的第一视角
- Anima L0-L5 分析面板收成**可折叠抽屉 / Inspector 面板**，默认收起，供想看技术的人主动展开
- 病房场景从 v0.2 的占位几何（box + cylinder）升级到**真实病房资产**（床、床头柜、病人 humanoid、墙壁贴图）
- 保留 v0.2 全部后端能力不动

**当前状态**（2026-04-20 晚 — 服务器侧已部署、本地仓库刚同步完）：

### 已完成（生产可用，跑在 `dev.jeffliulab.com`）

**前端重设计 — 浅色"产品"主题**（`demo/web/src/components/`）
- 主题从 v0.2 的 `zinc-950` 暗色技术风改成白底 + `zinc-200` 边框的临床产品风
- 新增 `bci/` 目录：`SessionHeader` / `ChannelHealth` / `NeuralActivity` / `DecoderOutput` / `FiringRateBars` —— 假装的 BCI 信号面板（装饰性，符合 D18：UI 标注 decorative）
- 新增 `shell/` 目录：`MissionRibbon`（顶部任务条）/ `BciDrawer`（左抽屉）/ `TaskDrawer`（右抽屉）—— 实现 v0.3 目标的"折叠抽屉"信息层级
- `center/SimulationView` 升级为多相机 + E-stop + 状态轮询的产品级组件

**后端：多相机渲染管线**（`demo/core/src/sim/manager.py`）
- 5 路相机：`demo_view` / `grasp_view` / `bedside_view` / `top_down` / `tv_view`
- `_CameraFeed` 类：每路一个 `mujoco.Renderer` + 自己的 latest_jpeg + condvar，渲染线程从一份共享 `MjData` 同步刷所有 feed
- `STREAM_CAMERAS` 常量定义、`/api/sim/cameras` 路由广告、`/api/sim/mjpeg?camera=X` 按名取流
- 关掉每个 renderer 的 `mjVIS_RANGEFINDER`（否则地面会被黄色测距光束糊满）

**E-stop 通道**（独立于 LLM/BT 的旁路）
- `SimManager.estop_active: threading.Event`
- `routes/sim.py`: `POST /api/sim/estop` 设 flag 并把底盘速度归零；`POST /api/sim/estop/clear` 清掉
- `l3_skill.py SimSkillBehaviour.update`：每 tick 第一件事检查 flag → 立即 FAILURE，不走 LLM/BT 重建
- `Reset Sim` 同时清 estop flag
- 前端：右上角红色 E-stop 按钮 / 激活时变 amber Clear E-stop 按钮 / 顶部红条提示

**Reset 死锁修复**（`SimManager.stop()` 子段）
- 触发：4 路渲染线程在 `Renderer.update_scene()` 调用中持有对 `_model` 的引用；旧版 `stop()` 把渲染线程 join 超时 2s 后直接释放 `_model` → 在 mid-frame 解引用 → SEGV (signal 11)
- 修复：join 超时 2s → 10s；先逐个 `feed.renderer.close()` 释放 GL context，再清 `_feeds` 和 `_model`；render loop tick 头多一层 None 防御
- 前端配合：`SimulationView` 每 3s 轮询 `/api/sim/status`（用 `available && running` 判断），reset 后 17s 才刷新 `<img>`（匹配真实 sim 启动耗时）

**Canonical Subtask Safety Net**（`l1_parser.py _CANONICAL_PLANS`）
- 每个 intent 都有一份确定性的 BT 兜底计划，LLM parse 失败也能跑

**6 个意图全部跑通**（每条都给出可演示动作）
- `DRINK_WATER` → 5 步抓杯送床边
- `ADJUST_TV` → TV 屏材质 emission 变亮蓝
- `CALL_HELP` → 机器人抬臂做信标 + 护士 mocap 出现在病床旁停留 6s 后归位 + ws `help.called` 事件
- `GOTO_BED` → base 驱到 `(4.5, 1.3, -π/2)` 即床头侧（v0.3 后期从 `(2.71, 1.25)` 床尾位调到床头位；中途用过 `(4.2, 1.0)` 但和 nightstand 碰撞导致 PID 在 x≈3.7 反复震荡超时，最终改成 `y=1.3` 让出 nightstand 北缘 `y=0.79` 的避让带）
- `TURN_OFF_LIGHT` / `TURN_ON_LIGHT` → 5 盏光源 diffuse 清零或恢复 + 吊灯发光材料置黑或亮（**幂等**：subtask 名 `turn_off_light` / `turn_on_light` 决定目标态，不再纯 toggle）
- E-stop 中点 → outcome=cancel（旁路 LLM 直写 estop endpoint）

**病房场景 MJCF**（`/root/pkgs/stretch_mujoco/stretch_mujoco/models/hospital_ward.xml`）
- TV 从 Y=−1.95（右后方，挡在 demo_view 相机背后）挪到 Y=+1.95（左墙面向房间），demo_view 现在能看见
- 新增 `<camera name="tv_view">` 对准 TV，配合 `tv_view` MJPEG 流
- 新增 `nurse` mocap body：胶囊身体 + 球头 + 五官几何 + 护士帽，初始藏在地板下 `(-3, 1, -10)`；CallHelpSkill 通过 `data.mocap_pos/quat` 控制。2026-04-21 调参：torso 半径 `0.18 → 0.22`、rgba `0.55/0.78/0.88 → 0.15/0.45/0.85`（饱和医疗蓝）让 demo_view 远景更能认出护士轮廓
- **本地副本**：已拷贝到 `demo/core/assets/scenes/hospital_ward.xml`（新增）做版本化备份；运行时仍走 `ANIMA_SCENE_XML` 环境变量指向的服务器路径，未改动 `SCENE_XML` 默认值

**渲染性能约束**（v0.3 排查中确认的硬件事实）
- Hetzner CPX31（无 GPU）跑 osmesa 软件渲染 5 路相机，满载 ~0.4 fps
- 直接后果：任何由 BT 驱动的"滑入式"动画（如最初设计的护士走入门）在渲染流上只采样到 1-2 帧，视觉上等同于瞬移
- 解决思路：动画必须设计成「目标态保持 ≥ 渲染周期」的离散关键帧形式，靠多次采样让低帧率渲染抓到。CallHelpSkill 的 `_HOLD_S=6.0` 就是为此设的（见下）
- **2026-04-21 调优**：`RENDER_W/H` 960×540 → 640×360（`sim/manager.py`），per-camera fps 约 +25%。更激进的分辨率会降低产品观感，目前 trade-off 合理

### 验收（已通过）

- `/api/sim/cameras` 返回 5 个相机
- `tv_view` MJPEG 200 OK + ~50KB/帧；离线 `mujoco.Renderer` 直渲两路确认 demo_view 能看见 TV、tv_view 是清晰特写（snapshot：`/tmp/snap_demo_view.png`、`/tmp/snap_tv_view.png`）
- 两次连续 `/api/sim/reset` 不再 SEGV，systemctl 状态保持 active
- 6 个 intent 在前端逐一跑通 outcome=success，E-stop outcome=cancel

### 本次会话本地同步动作（2026-04-20）

之前的 agent 全程在服务器编辑（`/tmp/` + scp + sed -i），本地仓库严重滞后。本次把以下文件从服务器拉回本地：

| 本地路径 | 来源 |
|---|---|
| `demo/core/src/sim/manager.py` | server `/root/anima/demo/core/src/sim/manager.py` |
| `demo/core/src/routes/sim.py` | 同上 |
| `demo/core/src/anima/l3_skill.py` | 同上 |
| `demo/web/src/components/center/SimulationView.tsx` | server `/root/anima/demo/web/...` |
| `demo/core/assets/scenes/hospital_ward.xml`（新增目录） | server `/root/pkgs/stretch_mujoco/stretch_mujoco/models/hospital_ward.xml` |

`bci/` 和 `shell/` 下的新组件目录此前已在本地存在但未 git add（git status 中显示为 `??`），与服务器内容字节等价。

### v0.3 末段三项调整（2026-04-20 续，本地+服务器已同步，**未推送 git**）

用户要求三件事，已在 server 完成、本地同步：

1. **「关灯」按钮幂等化** — `IntentInput.tsx` 每 3s 轮询 `/api/sim/status` 取 `light_off`，按钮文案在「关灯」/「开灯」之间切；后端 `ToggleLightSkill` 改为读 subtask name (`turn_off_light` / `turn_on_light`) 决定目标态而非纯 toggle，避免「再说一次关灯反而开了灯」的语义错误
2. **「叫护士过来」可视化** — 重写 `CallHelpSkill`：原计划用 `_lerp` 做门口→床边的滑入动画，实测在 0.4 fps 渲染下只渲到 1-2 帧、视觉上和瞬移无差。最终方案是直接 teleport 到 `(1.0, 1.5, 0)` （visitor_chair 旁），face yaw `-π/4` 对准 demo_view，停留 `_HOLD_S=6.0s` 让低帧率渲染抓到多帧，然后 teleport 回 `(-3, 1, -10)` 藏进地板下
3. **「去床边」改到床头位** — `BEDSIDE_POSE` 最终值 `(4.5, 1.3, -π/2)`；patient body 头部约在 `(4.5, 0)`，新位置正好在床头侧朝向病人脸。  
   **避障迭代**：先试 `(4.2, 1.0, -π/2)`，跑起来 unicycle PID 在 `(3.7, 1.0)` 卡住反复震荡 50+ 秒到 timeout。日志显示 robot heading 在 -0.35 ~ -1.10 之间来回摆。**根因**：nightstand 碰撞箱 `pos=(3.8, 0.65), size=(0.28, 0.14, 0.01)` → y 边到 `0.79`；Stretch 底盘半径约 `0.35` → robot 中心 y < `1.14` 就会卡在 nightstand 北缘。改 `y=1.3` 留 `0.16m` 安全余量，2026-04-21 验证一次到位 `(4.31, 1.28)` outcome=success

**排查代价记录**（教训）：
- 一开始用 `logger.info` 打调试，root logger 默认 level=WARNING 全部静默，浪费一轮迭代。后续诊断改用 `logger.warning`
- 用 sed 改 Python 字符串字面量时把闭引号吃掉了；改用 Python 脚本 + 字面 `replace` 安全
- bash heredoc 把 `mgr._data` 解析成变量；改写本地 `/tmp/skill_rewrite.py` + scp 上传执行

### 本地分主题 commit + push（2026-04-21）

服务器改动全部同步回本地后，分 4 个主题落盘并 push 到 `origin/main`：

| commit | 主题 | 范围 |
|---|---|---|
| `767792b` | `feat(v0.3)` 多相机 sim + E-stop + 6 意图 + canonical plans | backend（`demo/core/src/**`、`hospital_ward.xml`） |
| `f10d755` | `feat(v0.3)` 浅色产品主题 + 折叠抽屉 shell | frontend（`demo/web/src/components/**`、`bci/`、`shell/`、`globals.css`） |
| `75b0a2e` | `docs` PROGRESS.md + anima-intention-action README 刷新 + 删 2 份过时中文笔记 | 根目录文档 |
| `0279d60` | `feat(anima-intention-action)` 5 层框架的独立 Python 参考实现 | `anima-intention-action/{src,examples,tests,pyproject.toml}` |

`planning/13-demo-ui-design.md` 已在本 session 内更新 v0.3 浅色主题 + 抽屉设计（该文件被 `.gitignore` 的 `planning/` 规则挡住，不进仓但留在工作区作本地参考）。

### 并行工作说明（2026-04-21）

仓库根下的 **`WASM-TEST/`** 目录属于**另一个 agent** 在做 wasm 方案的测试工作区，本 agent 不读写该目录、不加入 gitignore、不在 commit 中触碰。如 `git status` 中出现该目录下改动，视为外部 agent 的状态，跳过。

### 下一步（pending — 用户手动）

1. **录 v0.3 验收视频**（路线图 v0.3 → v0.4 之间的桥）：live URL `https://dev.jeffliulab.com`，推荐脚本 `我想要水` → `请叫护士过来` → `请关灯` → `请开电视` → `去床边` → 点紧急停止，每条 10–15s 让 MJPEG 追上
2. 浏览器过一遍 6 意图 + 相机切换 + 抽屉展开/收起 + BT 节点高亮 + 五因素仪表刷新（curl/MJPEG 只能证明后端对，视觉细节需要人眼）

### 工作恢复锚点（resume notes）

- **服务器是 canonical live state**：`anima-robot-cloud`（SSH 别名）`/root/anima/`，systemd `anima-api.service` + `anima-web.service`
- **服务器侧不是 git 仓库**（裸目录），所以"以服务器为准、本地周期性同步"是常态
- 本地仓库下次启动时：`git status` 应显示上述 5 个文件为 `M` / `??`，先决定 commit 还是丢弃
- 验证服务器健康：`ssh anima-robot-cloud 'curl -s http://127.0.0.1:8765/api/sim/status'` 应返回 `available:true, running:true`
- v0.3 截图：`运行时的截图/`（未追踪目录）

**v0.3 验收标准（预定）**：

- 首屏打开 3 秒内，非技术观众能识别出"这是一个 BCI 控制的护理机器人产品" — 已基本达成（浅色产品主题 + MJCF 主视图占主屏）
- 点一下「技术分析」按钮能看到完整 Anima L0-L5 + 五因素 — 已达成（右抽屉 TaskDrawer）
- 场景视觉质感达到「像真实产品 demo 视频」的水平 — 待最终录制确认

---

## Anima IP 完整性检查

每次发版都要确认以下 Anima 核心元素在 demo 中完整可见（署名规则见 `/Users/macbookpro/.claude/projects/-Users-macbookpro-Local-Root-human-brain-interface-demo/memory/anima_ip_preservation.md`）：

- **5 层**：L0 Signal → L1 Parser → L2 Planner → L3 Skill → L4 Actuator → L5 Assessment（`LayerStack` 组件全程可见）
- **5 因素**：ITA / MQA / SQA / GOA / PEA（`FiveFactorPanel` 实时刷新）
- **LLM-as-Parser**：L1 通过 DeepSeek forced tool-call 输出结构化 `IntentToken`，不生成自然语言
- **Test-and-Check**：v0.1 已在 `l2_planner.py` 做 JSON / 意图 / 参数校验；v0.3 扩展到技能 / 安全 / 前置条件六道关
- **GOA 乘积公式**：`P(success) = P₁ × P₂ × ... × Pₙ`（`l5_assessment.py`）
- **PEA 三因子检索**：recency × 0.5 + relevance × 3.0 + importance × 2.0（实现见 `storage/pea_log.jsonl` + 检索函数）
- **Function Calling + Affordance Scoring**（<100 技能时替代 RAG）
- **行为树执行**：`py_trees`

Anima 框架 © Jeff Liu Lab。原始 preserved 设计见 `anima-intention-action/docs/preserved/`。

---

## 参考文档

- 全景路线图：`planning/11-execution-roadmap.md`
- 决策记录 D1-D18：`planning/12-open-questions.md`
- 场景目录（6 幕）：`planning/06-demo-scenarios.md`
- UI 设计（v0.2 前）：`planning/13-demo-ui-design.md`（v0.3 会新增一份）
- Anima IP 保护规则：`~/.claude/projects/-Users-macbookpro-Local-Root-human-brain-interface-demo/memory/anima_ip_preservation.md`
- JD 原文：`产品岗jd.md`
- 研究事实基础（公司画像 / 行业数据 / 监管）：`planning/archive/调研综合与demo方案v1.md`（Part 1 仍然有效）
