# BCI × Anima — Intention to Action

> 最小可信原型：用 Anima 认知框架（5 层 + 5 因素 + LLM-as-Parser）驱动仿真中的 Stretch RE3 护理机器人，完成脑机接口风格的「意图 → 行动」闭环。文本输入代理 BCI 解码出的意图；下游 TaskSpec、行为树、五因素评估、审计日志都是功能实现。

- **展示页**：<https://jeffliulab.github.io/human-brain-interface-demo/>
- **在线 Demo**：<https://dev.jeffliulab.com>（桌面浏览器）
- **状态**：v0.2 — 实时 MuJoCo + 自主 Stretch 技能 + Hetzner 部署

---

## 这是什么

独立作品集项目，演示一种把侵入式 BCI 的低带宽意图信号翻译成可审计机器人行动的中间层设计。差异化点是**把自研的 Anima 认知框架作为意图-行动之间的中间件**，而不是把 BCI 信号直接接到 VLA 里。

**当前场景**：「我想喝水」— 用户文本输入 → L1 LLM Parser 输出 `IntentToken` → L2 Planner 生成行为树 → L3 Skill 调 `stretch_mujoco` API 真实执行（导航、抓取、送达）→ L5 五因素实时评估。

**Anima 框架**（© Jeff Liu Lab）：

- **5 层**：L0 Signal / L1 Parser / L2 Planner / L3 Skill / L4 Actuator / L5 Assessment
- **5 因素**：ITA（意图可信度）/ MQA（运动质量）/ SQA（安全质量）/ GOA（目标达成概率）/ PEA（后评估）
- **LLM-as-Parser**（不是 Generator）：LLM 只输出结构化 TaskSpec JSON
- **Test-and-Check 六道关**：JSON / 意图 / 技能 / 参数 / 安全 / 前置条件

---

## 仓库结构

```
demo/
├── core/         FastAPI 后端（uv + Python 3.12）:8765
│   └── src/
│       ├── anima/    Anima L0-L5 实现
│       ├── sim/      MuJoCo StretchMujocoSimulator 管理
│       ├── routes/   HTTP + WebSocket + MJPEG 流
│       └── llm/      DeepSeek provider
├── web/          Next.js 前端（Tailwind + zustand + ReactFlow）:3000
└── sim/          MuJoCo 场景资产

github-page/     展示页（Astro 静态站 → GitHub Pages）
.github/workflows/pages.yml   GitHub Actions 自动部署
```

---

## 本地运行

### 后端（:8765）

```bash
cd demo/core
cp .env.example .env        # 填入 DEEPSEEK_API_KEY
uv sync
uv run uvicorn src.main:app --reload --port 8765
```

后端启动时会尝试初始化 `StretchMujocoSimulator`。MuJoCo 原生支持 macOS，无需 Docker。如果初始化失败（缺依赖 / 缺 MJCF），Anima L3 自动回落到 mock skill，前端功能不受影响。

### 前端（:3000）

```bash
cd demo/web
npm install
npm run dev
```

打开 `http://localhost:3000`，输入「我想喝水」。

### 展示页（Astro）

```bash
cd github-page
npm install
npm run dev
```

推送到 main 后 GitHub Actions 自动部署到 Pages。

---

## demo 现场展示了什么

1. **L0 Input** — 文本特征抽取 + 装饰性 256 通道波形（UI 明确标注 "decorative only"）
2. **L1 Intent Parser** — DeepSeek `deepseek-chat` 强制 tool-call → `IntentToken`（35 词词表）
3. **L2 Planner / L3 Skill** — `py_trees` Sequence 六节点（locate / navigate / grasp / lift / deliver / release）
4. **L4 Actuator** — `stretch_mujoco` Python API（分析 IK + unicycle PID）直接驱动仿真中的 Stretch RE3
5. **L5 Assessment** — ITA / MQA / SQA / GOA / PEA 实时更新，PEA 落盘到 `demo/core/src/storage/pea_log.jsonl`
6. **MJPEG 直播** — `sim.pull_camera_data()` → FastAPI multipart 流 → 前端 `<img>`，展示 Stretch 真实自主执行（每次运行从 MJCF 重新查 cup 位姿 + 重算 IK，不是脚本重放）

---

## 致谢与声明

Anima 认知框架 © Jeff Liu Lab。
Stretch RE3 MJCF / Python API 由 Hello Robot 提供。
MuJoCo（Google DeepMind）、py_trees、FastAPI、Next.js、Astro 等开源组件致谢。

独立作品集项目。与 Neuralink / Hello Robot 等任何具名公司均无合作关系。
