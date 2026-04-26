export const SITE = {
  title: "Intent-to-Action · BCI × Embodied AI",
  titleZh: "脑控具身智能产品原型",
  description: "用 Anima 认知框架连接侵入式 BCI 信号与居家护理具身机器人。5 层认知栈 + 5 因素实时评估 + 6 道安全闸门。",
  author: "Jeff Liu",
  email: "jeff.pang.liu@gmail.com",
  repo: "https://github.com/jeffliulab/human-brain-interface-demo",
} as const;

export const LIVE_DEMO = {
  url: "https://dev.jeffliulab.com",
  label: "在线 Demo",
  warning: "桌面浏览器",
} as const;

export const NAV_ITEMS = [
  { href: "#prototype", label: "可交互原型" },
  { href: "#demo", label: "DEMO 细节" },
  { href: "#details", label: "技术细节" },
] as const;

export const DEMO_STILLS = [
  { image: "demo/top-view.png", caption: "俯视视角 · 病房场景全局 + Stretch 导航路径" },
  { image: "demo/bedside.png", caption: "床边视角 · 接近病人送达时刻" },
  { image: "demo/grasp.png", caption: "抓取特写 · grasp → lift 执行瞬间" },
] as const;

export const HERO = {
  h1: "脑控具身智能产品原型",
  h1En: "Intent-to-Action, Audited End-to-End",
  subhead:
    "病人通过想「取水喝」，机器人便能执行取水动作，并智能识别任务是否成功。",
  ctaPrimary: { href: "#demo", label: "演示" },
  ctaSecondary: { href: "#prototype", label: "原型" },
  ctaTertiary: { href: "#details", label: "细节" },
} as const;

export const STORYBOARD = [
  {
    step: "01",
    title: "脑意图输入",
    caption: "BCI 解码出的用户意图以自然语言代理接入（装饰波形仅作可视化）。",
    image: "storyboard/01-intent.png",
  },
  {
    step: "02",
    title: "结构化意图解析",
    caption: "L1 LLM Parser 强制 tool-call，输出 IntentToken JSON + 置信度。",
    image: "storyboard/02-parse.png",
  },
  {
    step: "03",
    title: "行为树调度执行",
    caption: "L2 py_trees Sequence → L3 六原子技能（locate / navigate / grasp / lift / deliver）。",
    image: "storyboard/03-act.png",
  },
] as const;

export const CONTRIBUTION = {
  intro: "系统基于 Anima 认知框架独立实现，覆盖 L1–L5 全链路：",
  did: [
    "L1 · LLM-as-Parser（强制 tool-call · IntentToken 35 词词表）",
    "L2 · py_trees 行为树 + 6 道 Test-and-Check 安全闸门",
    "L3 · 六个原子技能（locate / navigate / grasp / lift / deliver / release）",
    "L4 · MuJoCo 病房场景 + Stretch RE3 集成 · MJPEG 实时流",
    "L5 · 五因素实时评估（ITA / MQA / SQA / GOA / PEA）+ 事件回放",
  ],
} as const;

export const PROTOTYPE_HOTSPOTS = [
  { id: 1, title: "L0 · 意图输入", desc: "自然语言输入 + 快速指令按钮，模拟 BCI 解码后的意图。", x: 11, y: 18 },
  { id: 2, title: "信号健康 & 神经活动", desc: "CHANNEL HEALTH / NEURAL ACTIVITY / FIRING RATE 装饰可视化。", x: 11, y: 68 },
  { id: 3, title: "MuJoCo Live View", desc: "L4 物理仿真 MJPEG 流 · Stretch RE3 实时自主动作。", x: 47, y: 50 },
  { id: 4, title: "L1 · Intent Decode", desc: "IntentToken 标签 + 置信度 + drift_score 实时显示。", x: 85, y: 14 },
  { id: 5, title: "Anima Stack", desc: "L0–L5 五层认知栈逐层激活状态。", x: 85, y: 42 },
  { id: 6, title: "BT Pipeline", desc: "L2 行为树当前执行节点 + L3 六技能成功率。", x: 85, y: 72 },
] as const;

export const TECH_DETAILS = [
  {
    summary: "Anima 5 层认知栈",
    image: "details/anima-stack.png",
    body: [
      "L0 · Input — 信号特征抽取 + 装饰波形（UI 明确标注 decorative only）",
      "L1 · Parser — LLM 强制 tool-call，输出 IntentToken（35 词词表）",
      "L2 · Planner — IntentToken → TaskSpec → py_trees 行为树",
      "L3 · Skill — 六个原子技能，每个带前置 / 后置条件检查",
      "L4 · Actuator — MuJoCo 物理仿真或真机（Stretch / Kinova / 未来人形）",
      "L5 · Assessment — 5 因素实时评估，PEA 写入可查询日志",
    ],
  },
  {
    summary: "5 因素实时评估",
    image: "details/five-factors.png",
    body: [
      "ITA — Intent 置信度，L1 解析质量 < 阈值触发用户确认",
      "MQA — 信号质量 + 跨天神经漂移，drift_score > 0.3 触发重校准",
      "SQA — 技能执行质量，滑窗成功率决定是否切换 fallback",
      "GOA — 整体目标达成概率，P(success) = P₁ × P₂ × … × Pₙ",
      "PEA — 过往经验检索，recency × 0.5 + relevance × 3.0 + importance × 2.0",
    ],
  },
  {
    summary: "LLM-as-Parser · 为什么强制 tool-call",
    body: [
      "LLM 在系统里只做一件事：把自由文本解析成结构化 IntentToken JSON。",
      "强制 tool-call、不生成自然语言。目的是规避「假神经解码」——不伪装 BCI 已经能解码出完整自然语言。",
      "同时规避 LLM 幻觉式生成动作。这是核心差异化设计。",
    ],
  },
  {
    summary: "6 道 Test-and-Check 安全闸门",
    body: [
      "① JSON 合法性 — 解析失败 → 重问 LLM",
      "② 意图合法性 — 不在 35 词词表 → 发起澄清",
      "③ 技能可用性 — 无对应技能 → 回落通用",
      "④ 参数合法性 — 越界 → 请用户确认",
      "⑤ 安全边界 — 力 / 距离 / E-stop → 直接拒绝并解释",
      "⑥ 前置条件 — 电量 / 抓握状态 / 场景检查 → 请求补全或回滚",
    ],
  },
  {
    summary: "技术栈",
    body: [
      "后端 · FastAPI · WebSocket · MuJoCo · py_trees · DeepSeek tool-call",
      "前端 · Next.js · Zustand · MJPEG 实时流",
      "部署 · Hetzner · Docker · Nginx",
      "仓库 · github.com/jeffliulab/human-brain-interface-demo",
    ],
  },
] as const;
