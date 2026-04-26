# 12 — ALICE 项目对 ANIMA 的启发

> 本文档是一份**未来参考**：当 ANIMA 进入实际开发并需要补强工程能力时，回过头来看哪些 ALICE 已经验证过的模式可以直接借鉴。当前阶段不做实现。

---

## 0. 背景

作者另外维护着一个 LLM agent 项目 **ALICE**（位于 `D:\Projects\jeffliulab\ALICE_PROJECT`），它是 Stanford "Generative Agents: Interactive Simulacra of Human Behavior" (Park et al., UIST 2023) 的完整复现 + 自研 ALICEv1 扩展，包含 22 个 agent 在中世纪村庄 Tanapocia 的自主社会模拟。

ALICE 在认知层涉及的模块——感知、记忆检索、反思、分层规划——与 ANIMA 在词汇上高度重合，但**底层哲学相反**：

| 维度 | ALICE | ANIMA |
|---|---|---|
| 目标 | 让 NPC 行为可信、有故事性 | 让物理机器人执行任务安全、可解释、可验证 |
| 物理性 | 2D tile 世界，无传感器/执行器 | ROS 2 + Nav2 + MoveIt2 + 真实硬件 |
| LLM 模式 | LLM-as-generator——所有决策、打分、对话由 LLM 自由生成 | LLM-as-Parser——LLM 只输出结构化 TaskSpec，再做 Test-and-Check 验证 |
| 失败成本 | 不好玩 | 砸碎东西/伤人 |
| 理论根基 | Park et al. UIST 2023 | LLM-as-Parser + 经典认知架构谱系（详见 [`DIARC框架与Tufts-HRI-Lab.md`](DIARC框架与Tufts-HRI-Lab.md)） |

**结论**：两者**不能合并**——把 ALICE 的 generator 风格塞进 ANIMA 会破坏 Parser+Test-and-Check 换来的安全性。但 ALICE 中有一批**通用工程模式**与 ANIMA 哲学完全兼容，可以选择性吸收。本文档记录这些模式，留给未来的 ANIMA 开发者（包括未来的自己）参考。

**ALICE 与 ANIMA 在求职定位上应保持独立**：两个项目讲两个不同的故事——ALICE 代表"研究/创意型 LLM agent"，ANIMA 代表"工程/安全型 LLM agent"——合并反而稀释。建议在 ANIMA 的 README related work 部分加一句对比即可。

---

## 1. 可借鉴清单（按性价比排序）

### ⭐⭐⭐ P0-1：提示词外部化（Prompt Externalization）

**ALICE 做法**：所有 24 个 prompt 模板放在 [backend/data/prompts/](D:/Projects/jeffliulab/ALICE_PROJECT/backend/data/prompts/)，由 [backend/prompt_loader.py](D:/Projects/jeffliulab/ALICE_PROJECT/backend/prompt_loader.py) 加载与缓存，由 [backend/prompt_builder.py](D:/Projects/jeffliulab/ALICE_PROJECT/backend/prompt_builder.py) 拼装多段 system prompt。

**ANIMA 现状**：[anima_core_node.py:40-66](../../SmartRobotArm/src/anima_node/anima_node/nodes/anima_core_node.py#L40-L66) 把 `SYSTEM_PROMPT` 硬编码在 Python 模块顶部，每次想调 prompt 都要改代码、重 build ROS 包。

**建议改造方向**（未来）：
- 新建 `src/anima_node/prompts/` 目录，放 `parser_system.txt`、`parser_retry.txt` 等
- 新建轻量 `prompt_loader.py`：用 `ament_index_python.packages.get_package_share_directory` 找到包路径，缓存加载结果，提供 `render(name, **kwargs)` 做模板替换
- 修改 `setup.py`/`CMakeLists.txt` 把 `prompts/` 加进 `data_files`
- ANIMA 不需要 ALICE 那么复杂的 `prompt_builder`，因为没有 emotion/ego/scene 多段拼接需求

**收益**：可版本化、可 A/B、可多语言、改 prompt 不用重 build。

---

### ⭐⭐⭐ P0-2：`safe_generate_response` 自动重试封装

**ALICE 做法**：[backend/llm/llm_client.py](D:/Projects/jeffliulab/ALICE_PROJECT/backend/llm/llm_client.py) 中的 `safe_generate_response(prompt, validate_fn, cleanup_fn, max_retries, fallback)`——每次 LLM 调用都过这一层，验证失败自动重试，最终失败回退安全值。三件套（validator + cleanup + fallback）非常清晰。

**ANIMA 现状**：[anima_core_node.py:117-129](../../SmartRobotArm/src/anima_node/anima_node/nodes/anima_core_node.py#L117-L129) 的 `parse_instruction` 只调用一次 LLM；[L231-255](../../SmartRobotArm/src/anima_node/anima_node/nodes/anima_core_node.py#L231-L255) 的 `validate_task_spec` 失败时只是 return False、放弃任务。**这违背了 ANIMA 设计文档中"Test-and-Check 失败时让 LLM 看到错误并重新生成"的核心承诺。**

**建议改造方向**（未来）：

```python
# src/anima_node/anima_node/llm_utils.py（新建）
def safe_generate(
    generate_fn,        # (prompt) -> raw_text or None
    validate_fn,        # (parsed) -> (ok, errors_list)
    initial_prompt,
    retry_prompt_fn,    # (previous_output, errors) -> next_prompt
    *,
    max_retries=3,
    parse_json=True,
    fallback=None,
):
    prompt = initial_prompt
    for attempt in range(max_retries):
        raw = generate_fn(prompt)
        if raw is None: continue
        try:
            obj = json.loads(raw) if parse_json else raw
        except json.JSONDecodeError as e:
            prompt = retry_prompt_fn(raw, [f"invalid JSON: {e}"])
            continue
        ok, errors = validate_fn(obj)
        if ok: return obj
        prompt = retry_prompt_fn(raw, errors)
    return fallback
```

配套修改：把 `validate_task_spec` 的签名改为返回 `(bool, list[str])`，把 `on_instruction` 改用 `safe_generate` 串联 parse + validate + 重试。retry prompt 模板里要把"上次输出 + 校验错误"反馈给 LLM，让它有机会修正。

**收益**：直接把 ANIMA 设计文档中已经承诺、但还没落地的 Test-and-Check 重试循环补完。

---

### ⭐⭐⭐ P0-3：三因子记忆检索公式（用于未来 PEA 模块）

**ALICE 做法**：[backend/persona/cognitive_modules/retrieve.py](D:/Projects/jeffliulab/ALICE_PROJECT/backend/persona/cognitive_modules/retrieve.py) 用 `recency*0.5 + relevance*3.0 + importance*2.0` 三因子打分检索记忆。其中：
- recency = `decay^rank`（指数衰减）
- relevance = embedding 余弦相似度
- importance = 节点的 poignancy（1-10）

**ANIMA 现状**：自我评估的"五因子"中的 **PEA（Past Experience Assessment）** 需要"历史上类似任务的成功率如何"，这要求一个经验数据库 + 检索机制。设计文档 [10-ANIMA认知框架设计.md](10-ANIMA认知框架设计.md) 写了承诺，**代码完全没实现**。

**建议改造方向**（未来）：
- 新建 `src/anima_node/anima_node/experience_db.py`，用 SQLite 存任务记录（task_id、description、task_type、outcome、elapsed_sec、timestamp、embedding、failure_reason）
- 检索方法 `retrieve_similar(query_emb, task_type, k=5)` 直接照搬 ALICE 三因子打分公式
- `estimate_success(query_emb, task_type)` 取 top-k 中 success 比例
- Embedding 用 sentence-transformers `all-MiniLM-L6-v2`（与 ALICE 一致），lazy import
- 持久化路径用 `~/.ros/anima_experience.db`

**收益**：用一个 200 行的小模块就能给 ANIMA 装上一个 PEA 雏形，让 self-assessment 的故事真的能跑。检索公式是经过 ALICE 验证的——直接拿来用比从零设计省事。

---

### ⭐⭐ P1-4：集中化常量管理

**ALICE 做法**：[backend/constants.py](D:/Projects/jeffliulab/ALICE_PROJECT/backend/constants.py) 把 100+ 阈值/权重/超参集中管理，按主题注释分组。

**ANIMA 现状**：超时（5/30/60 秒）散落在 [skill_executor_node.py:107,127,135](../../SmartRobotArm/src/anima_node/anima_node/nodes/skill_executor_node.py#L107)；KNOWN_LOCATIONS 硬编码在 [skill_executor_node.py:21-26](../../SmartRobotArm/src/anima_node/anima_node/nodes/skill_executor_node.py#L21-L26)；未来 self-assessment 还会引入更多阈值。

**建议改造方向**（未来）：
- 新建 `src/anima_node/anima_node/constants.py`，按主题分组：parser、skill executor timeouts、self-assessment、PEA weights
- KNOWN_LOCATIONS 单独移到 `src/anima_node/config/locations.yaml`，为未来真实语义地图留 hook

---

### ⭐⭐ P1-5：任务结束触发的反思（reflection trigger pattern）

**ALICE 做法**：[backend/persona/cognitive_modules/reflect.py](D:/Projects/jeffliulab/ALICE_PROJECT/backend/persona/cognitive_modules/reflect.py) 共有 5 条触发路径（importance 累积、对话后、定时、dissent、dream），其中最简洁的是"importance_trigger_curr <= 0 时触发反思"——一个累积器 + 一个阈值。

**ANIMA 启示**：ANIMA 不需要 5 条路径，只需要**一条**——"任务结束时触发 post-assessment"。但 ALICE 的"累积器+阈值"模式可以用于未来的 runtime 异常检测：例如累积小异常超过阈值时主动停下询问用户。

**建议改造方向**（未来）：
- 新建 `src/anima_node/anima_node/nodes/self_assessment_node.py`，订阅 `/task_spec` 与 `/anima_status`
- `on_task_start` 触发 pre-assessment（调用 PEA 估算成功率）
- `on_status` 监听 `FAILED`/`Task completed` 触发 post-assessment
- 第一版只占住"三时机骨架"（pre/runtime/post），五因子完整实现留到后续

**不要**搬 ALICE 的 5 条路径——ANIMA 的角色不需要这么多反思入口，会让架构变臃肿。

---

### ⭐⭐ P2-6：Skill 注册表唯一真源

**ALICE 做法**：所有世界知识、prompt、配置都集中在 `backend/data/` 下，不在代码里硬编码。

**ANIMA 现状**：skill 名字写了**三遍**：
1. [skills.yaml](../../SmartRobotArm/src/anima_node/config/skills.yaml)（注册表）
2. [anima_core_node.py:30-36](../../SmartRobotArm/src/anima_node/anima_node/nodes/anima_core_node.py#L30-L36) 的 `valid_skills`（校验用）
3. [skill_executor_node.py:46-53](../../SmartRobotArm/src/anima_node/anima_node/nodes/skill_executor_node.py#L46-L53) 的 dispatch table（执行用）

三处不一致是早晚的事。

**建议改造方向**（未来）：
- 新建 `src/anima_node/anima_node/skill_registry.py`，单点加载 `skills.yaml`
- `anima_core_node` 与 `skill_executor_node` 都从 registry 取 skill 列表
- skill_executor 的 dispatch table 在启动时校验"registry 中的每个 skill 都有 handler"

---

### ⭐ P2-7：分层规划的"扁平化列表"提示词模式

**ALICE 做法**：[backend/persona/cognitive_modules/plan.py](D:/Projects/jeffliulab/ALICE_PROJECT/backend/persona/cognitive_modules/plan.py) 的 `generate_hourly_schedule` 让 LLM 输出 `[[activity, duration_minutes], ...]` 这种紧凑列表，再在代码侧合并连续相同任务。这比让 LLM 直接吐完整嵌套 JSON 稳定得多。

**ANIMA 启示**：当 ANIMA 进入 Tier 2/3（多步、条件任务）需要让 LLM 生成 TaskSpec.steps 时，可以先让 LLM 输出扁平 `[[skill, params, timeout], ...]` 列表，再在代码侧组装成完整 TaskSpec。LLM 输出越扁平，越容易稳定。

---

## 2. 明确不要借鉴的部分

| ALICE 中有的 | 为什么 ANIMA 不要 |
|---|---|
| Emotion / valence / arousal | 与家用机器人安全角色无关；让 ANIMA 看起来像炫技 demo |
| Three-layer Ego（immutable / identity / current） | 同上；机器人不需要"自我认同演化" |
| Dream module（睡眠期记忆固化 + 认知失调） | 同上 |
| LLM-as-generator（让 LLM 自由生成动作/分解） | 直接违背 ANIMA Parser-first 哲学，破坏 Test-and-Check 安全保证 |
| 5-min subtask 自由生成 | ANIMA 必须从注册的 skill 库里调度，不能让 LLM 发明动作 |
| 5 条 reflection 触发路径 | 过度设计；ANIMA 一条"任务结束触发"足够 |
| Three-tier knowledge injection（universal/group/scene） | ANIMA 不需要复杂世界观注入，单一系统 prompt 足够 |
| 动态注意力带宽（基于 arousal 调节 K） | 与机器人感知无关 |

---

## 3. 关键文件交叉引用表（未来开发时直接对照）

**ALICE 端**（学习参考）：

| 文件 | 学什么 |
|---|---|
| [backend/llm/llm_client.py](D:/Projects/jeffliulab/ALICE_PROJECT/backend/llm/llm_client.py) | `safe_generate_response` 三件套封装 |
| [backend/prompt_loader.py](D:/Projects/jeffliulab/ALICE_PROJECT/backend/prompt_loader.py) | 提示词加载与缓存模式 |
| [backend/data/prompts/](D:/Projects/jeffliulab/ALICE_PROJECT/backend/data/prompts/) | 24 个 prompt 模板的组织方式 |
| [backend/constants.py](D:/Projects/jeffliulab/ALICE_PROJECT/backend/constants.py) | 100+ 常量按主题分组 |
| [backend/persona/cognitive_modules/retrieve.py](D:/Projects/jeffliulab/ALICE_PROJECT/backend/persona/cognitive_modules/retrieve.py) | 三因子检索公式实现 |
| [backend/persona/memory_structures/associative_memory.py](D:/Projects/jeffliulab/ALICE_PROJECT/backend/persona/memory_structures/associative_memory.py) | ConceptNode 持久化结构 |
| [backend/llm/embedding.py](D:/Projects/jeffliulab/ALICE_PROJECT/backend/llm/embedding.py) | sentence-transformers 包装 |
| [backend/persona/cognitive_modules/reflect.py](D:/Projects/jeffliulab/ALICE_PROJECT/backend/persona/cognitive_modules/reflect.py) | "累积器 + 阈值"触发模式 |
| [backend/persona/cognitive_modules/plan.py](D:/Projects/jeffliulab/ALICE_PROJECT/backend/persona/cognitive_modules/plan.py) | 扁平化列表输出模式 |

**ANIMA 端**（未来要改的位置）：

| 文件 | 改什么 |
|---|---|
| [src/anima_node/anima_node/nodes/anima_core_node.py](../../SmartRobotArm/src/anima_node/anima_node/nodes/anima_core_node.py) | 删硬编码 prompt → load_prompt；validate 改返回 (ok, errors)；on_instruction 改用 safe_generate；valid_skills 走 registry |
| [src/anima_node/anima_node/nodes/skill_executor_node.py](../../SmartRobotArm/src/anima_node/anima_node/nodes/skill_executor_node.py) | timeout 走 constants；KNOWN_LOCATIONS 走 yaml；dispatch 校验走 registry |
| [src/anima_node/launch/anima.launch.py](../../SmartRobotArm/src/anima_node/launch/anima.launch.py) | 新增 self_assessment 节点 |
| [src/anima_node/setup.py](../../SmartRobotArm/src/anima_node/setup.py) | data_files 加入 prompts/ 目录 |
| [src/anima_node/package.xml](../../SmartRobotArm/src/anima_node/package.xml) | 增加 sentence-transformers 依赖（PEA 用） |

**新建文件清单**（未来）：
- `src/anima_node/prompts/parser_system.txt`
- `src/anima_node/prompts/parser_retry.txt`
- `src/anima_node/anima_node/prompt_loader.py`
- `src/anima_node/anima_node/llm_utils.py`
- `src/anima_node/anima_node/constants.py`
- `src/anima_node/anima_node/skill_registry.py`
- `src/anima_node/anima_node/experience_db.py`
- `src/anima_node/anima_node/nodes/self_assessment_node.py`
- `src/anima_node/config/locations.yaml`

---

## 4. 推荐的吸收顺序

当 ANIMA 进入实际开发并准备做工程加固时，按这个顺序最稳：

1. **先做 P0-1（提示词外部化）**——影响小、收益大、不破坏现有节点
2. **再做 P0-2（safe_generate 重试）**——直接补完设计文档承诺的能力
3. **再做 P0-3（三因子检索）+ P1-5（self-assessment 骨架）**——这两个一起做，因为 self-assessment 的 PEA 阶段就需要检索
4. **最后做 P1-4（常量集中）+ P2-6（skill registry 唯一化）**——属于工程整理，不急

每完成一项就跑一次端到端 mock 测试（参见各项的 Verification 子节，可在 ANIMA 实施时再补具体命令），不要批量提交。

---

## 5. 求职话术参考

以下话术可用于简历或面试时介绍两个项目的差异化定位：

> "我维护两个互补的 LLM agent 认知架构项目：**ALICE** 是 Stanford Generative Agents 论文的完整复现并扩展了情绪/Ego/Dream 模块，22 个 agent 在中世纪村庄中自主生活，代表 LLM-as-generator 路线的研究探索；**ANIMA** 是面向家用机器人的认知框架，跑在 ROS 2 + 真实硬件上，采用 LLM-as-Parser + Test-and-Check 验证 + 行为树 + 自我评估，代表面向安全/可解释的工程路线。两个项目让我对 LLM agent 在'生成性'与'结构化'两端的取舍有第一手的设计经验。"

定位优势：
- 同时打开"研究"和"工程"两个口子
- 显示对架构哲学差异的理解，而不是只会调 API
- 让面试官看到能在两种范式之间做有依据的工程决策

**重要**：保持 ALICE 与 ANIMA **各自独立**，不要把 ALICE 的内容硬塞进 ANIMA。本文档列的所有借鉴项都是**工程模式层面的**，不会改变 ANIMA 的核心哲学。
