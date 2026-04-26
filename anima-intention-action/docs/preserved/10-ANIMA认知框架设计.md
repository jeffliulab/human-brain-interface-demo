# ANIMA 认知框架设计

> 设计一套开源的、面向移动操作机器人的 LLM 认知框架，基于 ROS 2 + Python + 现代 LLM 生态，作为未来 SOMA 家务机器人的大脑。
>
> **学术背景说明**：ANIMA 的若干关键设计（LLM-as-Parser、test-and-check、三阶段自我评估、Action Scripts → 行为树的映射）借鉴了已有认知架构的研究成果。这部分学术谱系与 Tufts HRI Lab / DIARC / 相关论文的详细关系集中在 [`DIARC框架与Tufts-HRI-Lab.md`](DIARC框架与Tufts-HRI-Lab.md)（私有文档）。**本设计文档是私有设计草稿；ANIMA 对外的公开 README（`anima`、`soma-arm`）不使用 DIARC 叙事。**

---

## 1. 设计动机

### 1.1 为什么不直接用 DIARC

| 问题 | 说明 |
|------|------|
| 语言生态 | DIARC 基于 Java/ADE；现代 ML 生态是 Python/PyTorch |
| ROS 版本 | DIARC 的 ROS 接口主要面向 ROS 1；Soma Home 用 ROS 2 |
| 耦合度 | DIARC 深度耦合了 Tufts 特有的 NLU/推理/信念系统 |
| 学习曲线 | 对外部开发者不友好，文档有限 |
| 不可携带 | 作为实习参与者，不能直接带走实验室的系统配置 |

### 1.2 从 DIARC 继承什么思想

| DIARC 的核心思想 | 在 Soma Home 框架中的体现 |
|-----------------|----------------------|
| 组件化、分布式 | ROS 2 节点 = 天然组件化 |
| 信息结构作为中介 | 结构化 JSON 作为 LLM 输出到执行层的桥梁 |
| Action Scripts | 技能库 + 行为树 |
| 深度内省 | 执行监控 + 自我评估模块 |
| 对话式自我评估 | 任务前/中/后的状态报告 |
| Parser > Translator | LLM 直接输出结构化可执行表示 |
| 目标管理 + 冲突调解 | 多任务调度 + 优先级管理 |

### 1.3 从论文结论继承什么教训

| 论文结论 | 框架设计决策 |
|----------|------------|
| Parser 方案 > Translator | LLM 直接输出结构化 JSON，不经过中间翻译 |
| 上下文信息对 novel data 无显著帮助 | 不依赖静态 context，而用 LLM Function Calling 技能调度 |
| 间接表达是难点 | 在 prompt 中加入间接表达示例；用更强的模型 |
| 安全隐忧：LLM 可能幻觉 | 加 test-and-check 验证层，不信任裸 LLM 输出 |
| 可解释性很重要 | 保留结构化中间表示，可审计、可调试 |

---

## 2. 框架总览：ANIMA (Autonomous Natural-language Instruction Mapping Architecture)

```
┌─────────────────────────────────────────────────────────────────┐
│                     用户自然语言输入                               │
│            "把沙发上的脏衣服都收拾到洗衣框里"                        │
└─────────────────────────┬───────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              Layer 1: LLM 语言理解层 (NLU)                       │
│                                                                 │
│  LLM-as-a-Parser (论文验证的最优方案)                              │
│  输入: 自然语言 + 技能库描述 (Function Calling)                     │
│  输出: 结构化 TaskSpec JSON                                      │
│                                                                 │
│  ┌──────────────────────────────────────────────────────┐       │
│  │ 验证层 (Test-and-Check, 论文建议的安全机制)              │       │
│  │ • JSON 格式验证                                        │       │
│  │ • 技能名是否存在于技能库                                 │       │
│  │ • 参数类型检查                                          │       │
│  │ • 安全约束检查 (禁止危险动作)                             │       │
│  │ • 如果验证失败 → 要求 LLM 重新生成                       │       │
│  └──────────────────────────────────────────────────────┘       │
└─────────────────────────┬───────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              Layer 2: 任务规划层 (Task Planner)                   │
│                                                                 │
│  行为树引擎 (BehaviorTree.CPP / py_trees)                        │
│  + PlanSys2 符号规划 (可选)                                      │
│                                                                 │
│  TaskSpec → 子任务序列 → 行为树实例                               │
│  目标管理 + 冲突调解 + 优先级排序                                  │
│  执行监控 + 异常检测 + 重规划                                     │
└─────────────────────────┬───────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              Layer 3: 技能执行层 (Skill Executor)                 │
│                                                                 │
│  技能库 = DIARC Action Scripts 的开源替代                         │
│  每个技能 = ROS 2 Action + 前置/后置条件 + 参数 + 超时             │
│                                                                 │
│  ┌─────────┬──────────┬───────────┬──────────┬────────┐        │
│  │navigate │ pick     │ place     │ open_door│ detect │  ...   │
│  │_to      │ _garment │ _in_bin   │          │ _cable │        │
│  └─────────┴──────────┴───────────┴──────────┴────────┘        │
└─────────────────────────┬───────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              Layer 4: 底层策略层 (Policy Layer)                   │
│                                                                 │
│  ACT / Diffusion Policy / VLA                                   │
│  Nav2 导航栈                                                     │
│  安全控制 (力限制、碰撞检测、紧急停止)                              │
└─────────────────────────────────────────────────────────────────┘

  ┌───────────────────────────────────────────────────────────────┐
  │              自我评估与内省模块 (Self-Assessment)                │
  │                                                               │
  │  (继承 DIARC Self-Assessment 思想)                             │
  │  • 任务前: 评估成功概率、最可能失败位置                           │
  │  • 任务中: 监控执行状态、检测异常                                │
  │  • 任务后: 记录结果、分析失败原因、更新经验                       │
  │  • 可对话: 用自然语言解释当前状态和决策依据                       │
  └───────────────────────────────────────────────────────────────┘
```

---

## 3. Layer 1: LLM 语言理解层

### 3.1 采用 LLM-as-a-Parser 方案

基于论文实验结论，我们直接让 LLM 输出结构化的 **TaskSpec JSON**，不做中间翻译。

**TaskSpec 格式定义（继承论文的信息结构思想）：**

```json
{
  "intent": "INSTRUCT",
  "task_description": "收集沙发上的脏衣服放到洗衣框",
  "subtasks": [
    {
      "skill": "navigate_to",
      "params": {"target": "sofa_area"},
      "description": "导航到沙发区域"
    },
    {
      "skill": "scan_and_detect",
      "params": {
        "target_type": "garment",
        "filter": {"state": "dirty"},
        "area": "sofa_area"
      },
      "description": "扫描检测脏衣物"
    },
    {
      "skill": "pick_garment",
      "params": {"target": "$detected_garments[i]"},
      "description": "抓取衣物",
      "loop": "for_each $detected_garments"
    },
    {
      "skill": "navigate_to",
      "params": {"target": "laundry_bin"},
      "description": "导航到洗衣框"
    },
    {
      "skill": "place_in_bin",
      "params": {"target_bin": "laundry_bin"},
      "description": "放入洗衣框"
    }
  ],
  "constraints": {
    "safety": ["no_force_above_10N", "avoid_fragile_objects"],
    "priority": "normal"
  },
  "fallback": "request_human_help"
}
```

### 3.2 LLM 选型

| 场景 | 推荐模型 | 部署方式 | 延迟 |
|------|----------|----------|------|
| **开发/原型** | GPT-4o / Claude Sonnet | API | 1-3s |
| **部署/在线** | Llama-3.1 8B fine-tuned | 本地 (Jetson/4090) | 100-500ms |
| **轻量端侧** | Phi-3 / Qwen2.5-3B | Jetson Orin | 50-200ms |

**微调方案（参考论文方法）：**
- 4-bit QLoRA / PEFT（论文验证有效）
- 训练数据：自定义 TaskSpec 数据集
- 数据增强：复用论文的 8 类风格变体方法

### 3.3 验证层 (Test-and-Check)

论文明确建议未来需要 "test-and-check" 策略来确保 LLM 输出的安全性。
我们在这里实现它：

```python
class TaskSpecValidator:
    """论文建议的 test-and-check 验证层"""
    
    def validate(self, task_spec: dict) -> ValidationResult:
        checks = [
            self.check_json_valid(task_spec),           # valid-json (论文指标)
            self.check_intent_valid(task_spec),          # intent-correct
            self.check_skills_exist(task_spec),          # cpc-name-correct
            self.check_params_valid(task_spec),          # 参数类型和范围
            self.check_safety_constraints(task_spec),    # 安全约束
            self.check_preconditions_met(task_spec),     # 前置条件
        ]
        
        if all(c.passed for c in checks):
            return ValidationResult(valid=True, task_spec=task_spec)
        else:
            # 把失败原因反馈给 LLM，要求重新生成
            return ValidationResult(
                valid=False,
                errors=[c.error for c in checks if not c.passed],
                retry=True
            )
    
    def check_skills_exist(self, task_spec):
        """检查所有技能名是否在技能库中（对应论文 cpc-name-correct）"""
        for subtask in task_spec["subtasks"]:
            if subtask["skill"] not in self.skill_registry:
                return CheckResult(
                    passed=False,
                    error=f"Unknown skill: {subtask['skill']}. "
                          f"Available: {list(self.skill_registry.keys())}"
                )
        return CheckResult(passed=True)
    
    def check_safety_constraints(self, task_spec):
        """检查安全约束（论文强调的 LLM 幻觉风险）"""
        FORBIDDEN = ["unplug_wall_socket", "cut", "throw", "force_open"]
        for subtask in task_spec["subtasks"]:
            if subtask["skill"] in FORBIDDEN:
                return CheckResult(
                    passed=False,
                    error=f"Forbidden action: {subtask['skill']}"
                )
        return CheckResult(passed=True)
```

### 3.4 LLM Function Calling 技能调度 + Affordance Scoring

论文发现静态上下文信息对 novel data 无显著帮助（§1.3）。
我们利用 LLM 原生的 Function Calling / Tool Use 能力，将技能注册表直接作为 tools 传入 LLM API，同时结合轻量 Affordance Scoring 确保物理可行性：

```python
class SkillDispatcher:
    """LLM Function Calling + Affordance Scoring 技能调度器
    
    替代原有的 RAG 向量检索方案（SkillRAG）。
    对于 <100 个技能的家庭机器人，Function Calling 比 RAG 更简单、准确。
    参考：SayCan (Google, 2022) 的 affordance grounding 思想。
    """
    
    def __init__(self, skill_registry, llm_client):
        self.skill_registry = skill_registry
        self.llm_client = llm_client
    
    def build_tools(self) -> list:
        """将技能注册表转换为 LLM Function Calling tools 格式"""
        tools = []
        for skill in self.skill_registry.values():
            tools.append({
                "name": skill.name,
                "description": (
                    f"{skill.description}\n"
                    f"前置条件: {', '.join(skill.preconditions)}\n"
                    f"效果: {', '.join(skill.effects)}"
                ),
                "input_schema": {
                    "type": "object",
                    "properties": skill.param_schema,
                },
            })
        return tools
    
    def dispatch(self, user_instruction: str, world_state: dict) -> dict:
        """技能调度：Function Calling 选技能 + Affordance 验证"""
        # Step 1: LLM Function Calling 选择技能和参数
        response = self.llm_client.messages.create(
            model="claude-sonnet-4-20250514",
            system=SYSTEM_PROMPT,
            tools=self.build_tools(),
            messages=[{"role": "user", "content": user_instruction}],
        )
        
        selected_skill = None
        for block in response.content:
            if block.type == "tool_use":
                selected_skill = {
                    "skill": block.name,
                    "params": block.input,
                }
                break
        
        if selected_skill is None:
            return {"error": "LLM 未选择任何技能"}
        
        # Step 2: Affordance Check（物理可行性验证）
        skill_spec = self.skill_registry[selected_skill["skill"]]
        affordance_ok, reason = self.affordance_check(
            skill_spec, selected_skill["params"], world_state
        )
        
        if not affordance_ok:
            selected_skill["affordance_warning"] = reason
            selected_skill["affordance_score"] = 0.0
        else:
            selected_skill["affordance_score"] = 1.0
        
        return selected_skill
    
    def affordance_check(self, skill_spec, params, world_state) -> tuple:
        """轻量物理可行性检查（借鉴 SayCan affordance scoring）
        
        不需要训练 value function，而是基于规则检查前置条件：
        - 物体是否在臂的可达范围内？
        - 物体重量是否超过载荷限制？
        - 当前关节状态是否允许执行？
        """
        for precond in skill_spec.preconditions:
            if not self.check_precondition(precond, params, world_state):
                return False, f"前置条件不满足: {precond}"
        return True, "OK"
```

**为什么用 Function Calling 替代 RAG？**

| 维度 | RAG 向量检索 | Function Calling | Function Calling + Affordance |
|------|------------|-----------------|------|
| 依赖 | FAISS/ChromaDB + Embedding 模型 | 无额外依赖 | 无额外依赖 |
| 适用规模 | 1000+ 技能 | <100 技能 | <100 技能 |
| 语义准确性 | 依赖 embedding 质量 | LLM 原生理解 | LLM 原生理解 |
| 物理接地 | 无 | 无 | 有（affordance check） |
| 维护成本 | 改技能需重建索引 | 改 YAML 即可 | 改 YAML 即可 |

> **备注**: 当技能库超过 100 个时，可用 RAG 预筛选 top-20 相关技能，再作为 Function Calling 的候选集。此时 RAG 作为预过滤器而非最终选择器。

---

## 4. Layer 2: 任务规划层

### 4.1 行为树引擎

用 **py_trees** (Python) 或 **BehaviorTree.CPP** (C++) 替代 DIARC 的 Action Scripts。

**DIARC Action Scripts 对照表：**

| DIARC 概念 | Soma Home 行为树对应 |
|------------|-------------------|
| Action Script (有序动作组合) | Sequence 节点 |
| FOR / FOR EACH | Iterator / ForEach 节点 |
| IF-THEN-ELSE | Selector + Condition 节点 |
| TRY | Fallback 节点 |
| Exit / Early Return | Abort / Cancel |
| Action Interpreter | 行为树 Executor |
| Goal Manager | Blackboard + Priority Queue |

**TaskSpec → 行为树的动态生成：**

```python
class BehaviorTreeFactory:
    """把 LLM 输出的 TaskSpec 转换成可执行的行为树"""
    
    def build_from_taskspec(self, task_spec: dict) -> py_trees.composites.Sequence:
        root = py_trees.composites.Sequence(
            name=task_spec["task_description"],
            memory=True
        )
        
        for subtask in task_spec["subtasks"]:
            if "loop" in subtask:
                # FOR EACH 循环
                node = self.build_loop_node(subtask)
            else:
                # 单个技能调用，带 fallback
                skill_node = self.build_skill_node(subtask)
                fallback = self.build_fallback(subtask, task_spec.get("fallback"))
                node = py_trees.composites.Selector(
                    name=f"try_{subtask['skill']}",
                    memory=True,
                    children=[skill_node, fallback]
                )
            root.add_child(node)
        
        return root
```

### 4.2 目标管理与冲突调解

继承 DIARC 的 Action Manager 设计：

```python
class GoalManager:
    """管理并发目标，调解冲突（类似 DIARC Action Manager）"""
    
    def __init__(self):
        self.active_goals = PriorityQueue()
        self.goal_history = []
    
    def submit_goal(self, task_spec: dict):
        priority = task_spec.get("constraints", {}).get("priority", "normal")
        goal = Goal(task_spec=task_spec, priority=priority)
        
        # 检查冲突
        conflicts = self.detect_conflicts(goal)
        if conflicts:
            resolution = self.resolve_conflicts(goal, conflicts)
            if resolution == "preempt":
                self.preempt_current()
            elif resolution == "queue":
                pass  # 排队等待
            elif resolution == "reject":
                return GoalResult(rejected=True, reason="conflict")
        
        self.active_goals.put(goal)
        return GoalResult(accepted=True)
```

---

## 5. Layer 3: 技能执行层

### 5.1 技能注册表

每个技能是一个 ROS 2 Action Server，带完整的元数据：

```python
@dataclass
class SkillSpec:
    name: str                        # 技能名（对应论文的 action name）
    description: str                 # 自然语言描述
    param_schema: dict               # 参数 JSON Schema
    preconditions: List[str]         # 前置条件
    effects: List[str]               # 后置效果
    timeout: float                   # 超时时间
    recovery_options: List[str]      # 失败恢复选项
    usage_examples: List[str]        # 使用示例（用于 Function Calling 描述）
    ros2_action: str                 # ROS 2 Action Server 名称

# 技能注册
SKILL_REGISTRY = {
    "navigate_to": SkillSpec(
        name="navigate_to",
        description="导航到指定位置",
        param_schema={"target": "string (location name or coordinates)"},
        preconditions=["robot_localized", "map_available"],
        effects=["robot_at(target)"],
        timeout=120.0,
        recovery_options=["replan_path", "wait_and_retry", "request_help"],
        usage_examples=[
            "navigate to the sofa area",
            "go to the closet",
            "move to laundry bin location"
        ],
        ros2_action="/navigate_to_pose"
    ),
    "pick_garment": SkillSpec(
        name="pick_garment",
        description="抓取指定衣物",
        param_schema={
            "target": "string (garment ID from detection)",
            "garment_type": "string (optional)"
        },
        preconditions=["garment_detected", "robot_near(garment)"],
        effects=["holding(garment)"],
        timeout=60.0,
        recovery_options=["retry_grasp", "reposition", "skip"],
        usage_examples=[
            "pick up the blue t-shirt",
            "grab the socks from the floor"
        ],
        ros2_action="/pick_garment"
    ),
    "place_in_bin": SkillSpec(
        name="place_in_bin",
        description="将手中物品放入指定收纳框",
        param_schema={"target_bin": "string (bin name)"},
        preconditions=["holding(object)", "robot_near(bin)"],
        effects=["not_holding(object)", "object_in(bin)"],
        timeout=30.0,
        recovery_options=["retry_place", "adjust_position"],
        usage_examples=[
            "put the garment into the laundry bin",
            "place it in the clean clothes box"
        ],
        ros2_action="/place_in_bin"
    ),
    # ... 更多技能
}
```

### 5.2 技能执行器

```python
class SkillExecutor:
    """执行单个技能，处理反馈和超时"""
    
    async def execute(self, skill_name: str, params: dict) -> SkillResult:
        spec = SKILL_REGISTRY[skill_name]
        
        # 1. 检查前置条件
        for precond in spec.preconditions:
            if not self.check_precondition(precond, params):
                return SkillResult(
                    success=False,
                    error=f"Precondition not met: {precond}"
                )
        
        # 2. 调用 ROS 2 Action
        action_client = self.get_action_client(spec.ros2_action)
        goal = self.build_goal(spec, params)
        
        result = await action_client.send_goal_async(
            goal, 
            timeout=spec.timeout
        )
        
        # 3. 记录执行日志（用于数据引擎和自我评估）
        self.log_execution(skill_name, params, result)
        
        return result
```

---

## 6. 自我评估与内省模块

### 6.1 设计思路

直接继承 DIARC 自我评估框架的三阶段设计：

**任务前 (Pre-Execution Assessment)：**
```python
class PreAssessment:
    """任务前评估：这个任务我能做吗？（对应 "Can You Do This?" 论文）"""
    
    def assess(self, task_spec: dict) -> Assessment:
        # 1. 检查所有技能是否可用
        skill_availability = self.check_skill_availability(task_spec)
        
        # 2. 根据历史执行数据估计成功概率
        success_prob = self.estimate_success_probability(task_spec)
        
        # 3. 识别最可能失败的步骤
        failure_hotspot = self.identify_failure_hotspot(task_spec)
        
        # 4. 估计完成时间
        estimated_time = self.estimate_completion_time(task_spec)
        
        return Assessment(
            can_do=success_prob > 0.3,  # 低于30%建议不做
            success_probability=success_prob,
            most_likely_failure=failure_hotspot,
            estimated_time=estimated_time,
            explanation=self.generate_explanation(...)  # 自然语言解释
        )
    
    def estimate_success_probability(self, task_spec):
        """基于历史执行统计估计成功率（论文的采样方法简化版）"""
        subtask_probs = []
        for subtask in task_spec["subtasks"]:
            history = self.execution_history.get(subtask["skill"], [])
            if history:
                prob = sum(1 for h in history if h.success) / len(history)
            else:
                prob = 0.5  # 没有历史数据时保守估计
            subtask_probs.append(prob)
        
        # 串联任务：总成功率 ≈ 各步成功率的乘积
        from functools import reduce
        return reduce(lambda a, b: a * b, subtask_probs, 1.0)
```

**任务中 (Runtime Monitoring)：**
```python
class RuntimeMonitor:
    """任务中监控：检测异常和性能偏差"""
    
    def monitor_step(self, skill_name, execution_state) -> MonitorResult:
        # 1. 超时检测
        if execution_state.elapsed > SKILL_REGISTRY[skill_name].timeout * 0.8:
            return MonitorResult(warning="approaching_timeout")
        
        # 2. 状态异常检测（对应 DIARC 的 resilience 研究）
        if self.detect_anomaly(execution_state):
            return MonitorResult(
                alert="anomaly_detected",
                recommended_action=self.suggest_recovery(skill_name)
            )
        
        # 3. 性能偏差检测
        expected = self.get_expected_performance(skill_name)
        if self.performance_diverged(execution_state, expected):
            return MonitorResult(
                warning="performance_degraded",
                details=self.explain_divergence(execution_state, expected)
            )
        
        return MonitorResult(status="normal")
```

**任务后 (Post-Execution Analysis)：**
```python
class PostAnalysis:
    """任务后分析：更新经验、记录失败、生成报告"""
    
    def analyze(self, task_spec, execution_log) -> AnalysisReport:
        # 1. 对比预测 vs 实际
        predicted = self.pre_assessment_cache[task_spec["id"]]
        actual_success = execution_log.success
        
        # 2. 更新历史统计
        for step in execution_log.steps:
            self.execution_history[step.skill_name].append(step)
        
        # 3. 如果失败，分析原因
        if not actual_success:
            failure_analysis = self.analyze_failure(execution_log)
            # 加入数据引擎的失败聚类
            self.data_engine.record_failure(failure_analysis)
        
        # 4. 生成自然语言报告
        report = self.generate_report(task_spec, execution_log, predicted)
        
        return AnalysisReport(
            success=actual_success,
            predicted_success_prob=predicted.success_probability,
            actual_steps=len(execution_log.steps),
            failure_step=execution_log.failure_step if not actual_success else None,
            failure_reason=failure_analysis if not actual_success else None,
            natural_language_report=report
        )
```

### 6.2 对话式自我评估

继承 "Can You Do This?" 论文的思路，让机器人能用自然语言解释自己：

```python
class SelfAssessmentDialogue:
    """机器人自然语言自我评估对话"""
    
    DIALOGUE_TEMPLATES = {
        "pre_task": {
            "high_confidence": "我可以完成这个任务。预计需要{time}分钟，成功概率约{prob}%。",
            "medium_confidence": "我可以尝试，但{failure_point}可能会有困难。成功概率约{prob}%。",
            "low_confidence": "这个任务对我来说有挑战。最大的风险是{failure_point}。建议{suggestion}。",
        },
        "during_task": {
            "normal": "正在执行{current_step}，进度{progress}%。",
            "warning": "注意：{warning_msg}。我正在{action}。",
            "failure": "{step}失败了，原因是{reason}。正在尝试{recovery}。",
        },
        "post_task": {
            "success": "任务完成。处理了{count}件衣物，用时{time}分钟。",
            "partial": "部分完成。成功处理了{success_count}/{total_count}件。{failure_count}件因{reasons}未能处理。",
            "failure": "任务未能完成。在{failure_step}步失败，原因是{reason}。建议{suggestion}。",
        }
    }
```

### 7.5 五因素事件触发评估模型

综合 Frasca & Scheutz 2022 (IEEE RA-L) 的三阶段评估 + Conlon et al. 2023 (Frontiers in Robotics and AI) 的事件触发机制，
ANIMA 在三阶段评估（Pre/Runtime/Post）基础上，设计了五个持续监控的评估因素：

| 因素 | 全称 | 评估内容 | 触发条件 |
|------|------|---------|---------|
| **ITA** | Interpretation of Task Assessment | LLM 解析是否正确？TaskSpec 是否符合用户意图？ | 每次指令解析后 |
| **MQA** | Model Quality Assessment | 世界模型（语义地图、物体位置）与传感器观测是否一致？ | 检测到感知异常时 |
| **SQA** | Solver Quality Assessment | 运动规划/导航策略是否最优？是否频繁失败？ | 策略失败率超过阈值时 |
| **GOA** | Generalized Outcome Assessment | 当前计划的整体预期成功率是否可接受？ | 每次子任务完成/失败后 |
| **PEA** | Past Experience Assessment | 类似任务的历史表现如何？ | 收到新任务时 |

```python
class EventTriggeredAssessment:
    """五因素事件触发评估（ANIMA 设计，综合 Frasca 2022 + Conlon 2023）
    
    与三阶段评估的关系：
    - 三阶段（Pre/Runtime/Post）是时间维度的评估
    - 五因素是内容维度的评估
    - 两者正交互补：任何时刻都可以检查任何因素
    """
    
    def __init__(self, experience_db, world_model):
        self.experience_db = experience_db
        self.world_model = world_model
        self.thresholds = {
            "ita_confidence": 0.7,    # LLM 解析置信度阈值
            "mqa_divergence": 0.3,    # 世界模型偏差阈值
            "sqa_failure_rate": 0.5,  # 策略失败率阈值
            "goa_min_success": 0.3,   # 最低预期成功率
        }
    
    def assess_ita(self, task_spec, original_instruction) -> float:
        """意图评估：LLM 解析结果是否合理？"""
        # 检查 TaskSpec 中的技能是否全部存在
        # 检查参数是否在合理范围内
        # 可选：用第二个 LLM 调用验证（交叉检查）
        pass
    
    def assess_mqa(self, expected_state, observed_state) -> float:
        """模型质量评估：世界模型 vs 传感器观测"""
        # 检查：物体位置是否与预期一致？
        # 检查：导航地图是否仍然有效？（是否有新障碍物？）
        pass
    
    def assess_goa(self, remaining_plan, execution_history) -> float:
        """预期结果评估：当前计划还能成功吗？"""
        # 基于历史成功率计算剩余子任务的联合成功概率
        # P(success) = P(step_i) × P(step_i+1) × ... × P(step_n)
        pass
    
    def assess_pea(self, task_type) -> float:
        """历史经验评估：类似任务的表现"""
        history = self.experience_db.query(task_type=task_type)
        if not history:
            return 0.5  # 无历史数据，默认中等信心
        return sum(h.success for h in history) / len(history)
```

### 7.6 VLM 运行时视觉监控（远期）

参考 AHA (2025)、ARMOR (2026)、I-FailSense (2025) 等最新研究，
ANIMA 可在运行时通过 VLM 监控相机图像来检测执行异常：

```python
class VLMExecutionMonitor:
    """VLM 视觉监控（Phase 11 实现）
    
    工作方式：
    1. 技能执行前，VLM 被告知"机器人将要做 X"
    2. 执行过程中，定期（1-5Hz）将相机图像送给 VLM
    3. VLM 判断："当前画面是否与预期一致？" 
    4. 如果检测到异常（物体掉落、抓取失败、碰撞等），触发恢复
    
    参考：
    - AHA (2025): 开源 VLM 用于检测和推理操控失败
    - I-FailSense (2025): 检测语义不对齐错误和控制错误
    """
    
    def monitor(self, camera_image, expected_action, task_context) -> dict:
        prompt = f"""你正在监控一个家庭机器人的执行过程。
机器人当前应该在执行: {expected_action}
任务背景: {task_context}

请判断这张图片中机器人的执行状态：
1. 正常 (execution looks correct)
2. 异常 (something went wrong)

如果异常，描述具体问题。"""
        
        response = self.vlm.analyze(camera_image, prompt)
        return {
            "status": response.status,  # "normal" | "anomaly"
            "description": response.description,
            "confidence": response.confidence,
            "suggested_recovery": response.recovery_action,
        }
```

> 注：VLM 监控是计算密集型操作，建议仅在关键操作（抓取、放置）时启用，而非全程监控。

---

## 7. 与其他开源方案的对比与集成

### 7.1 我们的框架 vs 现有方案

| 方案 | 定位 | 与 ANIMA 的关系 |
|------|------|--------------|
| **SayCan** | LLM + 可行性评分选动作 | ANIMA 的 Function Calling + Affordance Scoring 借鉴了类似思路 |
| **Code as Policies** | LLM 生成 Python 代码作为策略 | ANIMA 不用代码生成，用结构化 JSON（更安全） |
| **Inner Monologue** | LLM + 多种反馈循环 | ANIMA 的自我评估对话类似 inner monologue |
| **VoxPoser** | LLM + VLM → 3D voxel 值图 | ANIMA 的操作层可集成 VoxPoser 思路 |
| **ROSA** | ROS Agent (LangChain) | ANIMA 可以用 ROSA 作为 ROS 接口层 |
| **BehaviorTree.CPP** | 行为树引擎 | ANIMA 直接使用作为任务编排引擎 |
| **PlanSys2** | PDDL 符号规划 for ROS 2 | ANIMA 可选用于复杂多步规划 |

### 7.2 推荐的技术栈选择

```
LLM 推理:       vLLM / Ollama (本地) 或 API (开发期)
Prompt 管理:     LangChain / 自定义 (轻量)
行为树:          py_trees (Python) 或 BehaviorTree.CPP (C++)
符号规划 (可选):  PlanSys2
ROS 2 集成:      rclpy / ROS 2 Action Client/Server
技能调度:          LLM Function Calling + Affordance Scoring (备选: FAISS / ChromaDB，技能库 >100 时启用)
数据存储:        SQLite (执行历史) + Parquet (轨迹数据)
```

---

## 8. ROS 2 节点架构

```
homeops_cognitive/
├── nlu_node                    # LLM 语言理解 + 验证
│   ├── llm_parser              # LLM-as-a-Parser
│   ├── skill_dispatcher         # Function Calling 技能调度
│   └── task_spec_validator     # Test-and-Check 验证层
│
├── planner_node                # 任务规划 + 行为树
│   ├── behavior_tree_factory   # TaskSpec → 行为树
│   ├── goal_manager            # 目标管理与冲突调解
│   └── execution_monitor       # 执行监控
│
├── skill_executor_node         # 技能执行
│   ├── skill_registry          # 技能注册表
│   ├── skill_clients           # ROS 2 Action Clients
│   └── recovery_manager        # 恢复策略管理
│
├── self_assessment_node        # 自我评估
│   ├── pre_assessment          # 任务前评估
│   ├── runtime_monitor         # 运行时监控
│   ├── post_analysis           # 任务后分析
│   └── dialogue_interface      # 自然语言报告
│
└── data_engine_node            # 数据引擎接口
    ├── execution_logger        # 执行日志
    ├── failure_classifier      # 失败分类
    └── experience_database     # 经验数据库
```

**节点间通信：**
| 话题/服务 | 类型 | 功能 |
|----------|------|------|
| `/user_instruction` | Topic (String) | 用户自然语言指令输入 |
| `/task_spec` | Topic (JSON) | LLM 解析后的结构化任务 |
| `/task_status` | Topic | 任务执行状态 |
| `/self_assessment` | Service | 请求自我评估 |
| `/skill_feedback` | Topic | 技能执行反馈 |
| `/natural_language_report` | Topic (String) | 自然语言状态报告 |

---

## 9. 评测指标体系

直接继承论文设计的指标思路，扩展到整个系统：

### 9.1 语言理解评测（继承论文指标）

| 指标 | 来源 | 用途 |
|------|------|------|
| valid-json | 论文 | LLM 输出格式正确率 |
| intent-correct | 论文 | 意图识别准确率 |
| skill-name-correct | 论文 cpc-name-correct | 技能名映射正确率 |
| param-correct | 扩展 | 参数解析正确率 |
| subtask-sequence-correct | 扩展 | 子任务序列正确率 |
| safety-violation-rate | 扩展 | 安全约束违反率 |

### 9.2 系统级评测

| 指标 | 定义 |
|------|------|
| 端到端任务成功率 | 完整任务成功数 / 总尝试数 |
| 自我评估准确性 | 预测成功率 vs 实际成功率的相关性 |
| 失败预测准确性 | 预测的最可能失败点 vs 实际失败点的匹配率 |
| 恢复成功率 | 失败后恢复成功数 / 失败总数 |
| 指令到执行延迟 | 用户说话到机器人开始动的时间 |
| 任务完成时间 | 端到端执行时间 |
| 幻觉检出率 | 验证层拦截的无效/危险 LLM 输出比例 |

---

## 10. 这个框架在 Soma Home 中的角色

```
Soma Home 系统
├── ANIMA (本文档设计的 LLM 认知框架)     ← 大脑
│   ├── 语言理解
│   ├── 任务规划
│   ├── 技能调度
│   └── 自我评估
│
├── 感知系统                             ← 眼睛
│   ├── DINO + SAM2 + DINOv2
│   └── 语义地图
│
├── 策略学习系统                          ← 小脑
│   ├── ACT / Diffusion Policy
│   ├── OpenVLA / π0
│   └── 世界模型
│
├── 导航系统                             ← 腿
│   └── Nav2
│
├── 数据引擎                             ← 记忆
│   └── 采集 → 标注 → 筛选 → 训练
│
└── 硬件平台                             ← 身体
    └── COBOT Magic / Stretch 3
```

**ANIMA 是把所有这些系统连接起来的"认知胶水"。**

没有它，你只有一堆能力模块但不知道何时调用哪个。
有了它，机器人能理解"把脏衣服收拾了"这句话，自动规划子任务序列，
调用正确的感知+导航+操作技能，监控执行进度，处理异常，并用自然语言报告结果。

---

## 11. 与简历/面试的关联

> 简历话术与面试问答集中在 [`../SOMA_HOME_EXP/08-简历与面试指南.md`](../SOMA_HOME_EXP/08-简历与面试指南.md)；涉及 Tufts HRI Lab / DIARC 的独立背景叙事集中在 [`DIARC框架与Tufts-HRI-Lab.md`](DIARC框架与Tufts-HRI-Lab.md)。
