You have TWO equally important tasks:
1. Extract new facts from conversation history
2. Deduplicate existing memory files — find and flag redundant, overlapping, or stale content even if NOT mentioned in history

Output one line per finding:
[FILE] atomic fact (not already in memory)
[FILE-REMOVE] reason for removal
[SKILL] kebab-case-name: one-line description of the reusable pattern

Files: USER (identity, preferences), SOUL (bot behavior, tone), MEMORY (knowledge, project context)

Rules:
- Atomic facts: "has a cat named Luna" not "discussed pet care"
- Corrections: [USER] location is Tokyo, not Osaka
- Capture confirmed approaches the user validated

Deduplication — scan ALL memory files for these redundancy patterns:
- Same fact stated in multiple places (e.g., "communicates in Chinese" in both USER.md and multiple MEMORY.md entries)
- Overlapping or nested sections covering the same topic
- Information in MEMORY.md that is already captured in USER.md or SOUL.md (MEMORY.md should not duplicate permanent-file content)
- Verbose entries that can be condensed without losing information
For each duplicate found, output [FILE-REMOVE] for the less authoritative copy (prefer keeping facts in their canonical location)

Staleness — MEMORY.md lines may have a ``← Nd`` suffix showing days since last modification:
- SOUL.md and USER.md have no age annotations — they are permanent, only update with corrections
- Age only indicates when content was last touched, not whether it should be removed
- Use content judgment: user habits/preferences/personality traits are permanent regardless of age
- Only prune content that is objectively outdated: passed events, resolved tracking, superseded approaches
- Lines with ``← Nd`` (N>{{ stale_threshold_days }}) deserve closer review but are NOT automatically removable
- When removing: prefer deleting individual items over entire sections

Skill discovery — flag [SKILL] when ALL of these are true:
- A specific, repeatable workflow appeared 2+ times in the conversation history
- It involves clear steps (not vague preferences like "likes concise answers")
- It is substantial enough to warrant its own instruction set (not trivial like "read a file")
- Do not worry about duplicates — the next phase will check against existing skills

Do not add: current weather, transient status, temporary errors, conversational filler.

[SKIP] if nothing needs updating.



<!-- 这份系统指令（Prompt）的中文翻译如下：

你拥有两个同等重要的任务：
1、从对话历史中提取新的事实
2、对现有的记忆文件进行去重 —— 发现并标记冗余的、重叠的或过时的内容，即使历史记录中并没有提及这些内容

每一条发现输出一行：
[FILE] 原子事实（尚未存在于记忆中的）
[FILE-REMOVE] 移除的原因
[SKILL] 烤肉串命名法名称 (kebab-case-name)：可复用模式的单行描述

文件类别：USER（身份、偏好），SOUL（机器人的行为、语气），MEMORY（知识、项目上下文）

规则：

原子事实：例如“有一只叫Luna的猫”，而不是“讨论了宠物护理”
纠错：例如 [USER] 位置是东京，而不是大阪
记录用户验证过且确认有效的解决方案/方法

去重 —— 扫描所有记忆文件，寻找以下冗余模式：
同一事实在多处被陈述（例如：“用中文沟通”同时出现在 USER.md 和 MEMORY.md 的多个条目中）
涵盖同一主题的重叠或嵌套段落
MEMORY.md 中包含了已经在 USER.md 或 SOUL.md 中记录的信息（MEMORY.md 不应重复永久性文件中的内容）
可以被精简且不丢失核心信息的冗长条目
对于发现的每一个重复项，针对权威性较低的副本输出 [FILE-REMOVE]（倾向于将事实保留在其最规范/最权威的原始位置）


过时性判断 —— MEMORY.md 中的文本行可能带有类似 ← Nd 的后缀，表示自上次修改以来的天数：
SOUL.md 和 USER.md 没有天数标注 —— 它们是永久性的，仅在需要纠错时更新
天数（Age）仅表示内容最后一次被修改的时间，并不代表它是否应该被删除
需基于内容本身进行判断：用户的习惯、偏好和性格特征是永久性的，无论标记的天数是多少
仅修剪（删除）客观上已经过时的内容：例如已过去的事件、已解决的追踪事项、被取代的旧方法
带有 ← Nd（当 N>{{ stale_threshold_days }} 时）后缀的行值得仔细审查，但并非自动删除
在移除时：优先删除单个条目，而不是删除整个段落


技能发现 —— 当且仅当以下所有条件都满足时，标记 [SKILL]：
一个具体的、可重复的工作流在对话历史中出现了 2 次或以上
它包含清晰的步骤（不能是诸如“喜欢简短回答”这类模糊的偏好）
它有足够的实质内容，值得为其建立一套独立的指令集（不能是诸如“读取文件”这类微不足道的操作）
不用担心重复问题 —— 下一阶段将会与现有的技能库进行比对检查


不要添加：当前天气、瞬时的状态、临时性错误、对话填充废话。

如果没有需要更新的内容，输出 [SKIP]。 -->
