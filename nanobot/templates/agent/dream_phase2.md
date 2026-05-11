Update memory files based on the analysis below.
- [FILE] entries: add the described content to the appropriate file
- [FILE-REMOVE] entries: delete the corresponding content from memory files
- [SKILL] entries: create a new skill under skills/<name>/SKILL.md using write_file

## File paths (relative to workspace root)
- SOUL.md
- USER.md
- memory/MEMORY.md
- skills/<name>/SKILL.md (for [SKILL] entries only)

Do NOT guess paths.

## Editing rules
- Edit directly — file contents provided below, no read_file needed
- Use exact text as old_text, include surrounding blank lines for unique match
- Batch changes to the same file into one edit_file call
- For deletions: section header + all bullets as old_text, new_text empty
- Surgical edits only — never rewrite entire files
- If nothing to update, stop without calling tools

## Skill creation rules (for [SKILL] entries)
- Use write_file to create skills/<name>/SKILL.md
- Before writing, read_file `{{ skill_creator_path }}` for format reference (frontmatter structure, naming conventions, quality standards)
- **Dedup check**: read existing skills listed below to verify the new skill is not functionally redundant. Skip creation if an existing skill already covers the same workflow.
- Include YAML frontmatter with name and description fields
- Keep SKILL.md under 2000 words — concise and actionable
- Include: when to use, steps, output format, at least one example
- Do NOT overwrite existing skills — skip if the skill directory already exists
- Reference specific tools the agent has access to (read_file, write_file, exec, web_search, etc.)
- Skills are instruction sets, not code — do not include implementation code

## Quality
- Every line must carry standalone value
- Concise bullets under clear headers
- When reducing (not deleting): keep essential facts, drop verbose details
- If uncertain whether to delete, keep but add "(verify currency)"


<!-- 这份系统指令（Prompt）的中文翻译如下：

基于以下分析更新记忆文件。
[FILE] 条目：将描述的内容添加到合适的文件中
[FILE-REMOVE] 条目：从记忆文件中删除相应的内容
[SKILL] 条目：使用 write_file 在 skills/<name>/SKILL.md 路径下创建一个新技能


文件路径（相对于工作区根目录）
SOUL.md
USER.md
memory/MEMORY.md
skills//SKILL.md （仅用于 [SKILL] 条目）
绝对不要凭空猜测路径。

编辑规则
直接进行编辑 —— 下方已提供文件内容，不需要使用 read_file（读取文件）
使用完全一致的文本作为 old_text，包含其周围的空行以确保唯一匹配
将对同一个文件的多次更改批量合并为一次 edit_file 调用
对于删除操作：将段落标题 + 所有项目符号作为 old_text，将 new_text 留空
仅进行外科手术式的精准编辑 —— 绝不要重写整个文件
如果没有需要更新的内容，请直接停止，不要调用任何工具

技能创建规则（针对 [SKILL] 条目）
使用 write_file 创建 skills/<name>/SKILL.md
在写入之前，请先 read_file（读取）{{ skill_creator_path }} 以获取格式参考（Frontmatter 结构、命名规范、质量标准）
去重检查：读取下方列出的现有技能，以验证新技能在功能上是否冗余。如果现有技能已经涵盖了相同的工作流，则跳过创建。
需包含 YAML Frontmatter（前置元数据），并提供 name（名称）和 description（描述）字段
保持 SKILL.md 在 2000 字以内 —— 做到简明扼要且具有可执行性
必须包含的内容：何时使用、执行步骤、输出格式以及至少一个示例
绝对不要覆盖现有的技能 —— 如果该技能目录已存在，请跳过
引用智能体（Agent）有权访问的具体工具（例如 read_file、write_file、exec、web_search 等）
技能是一套指令集，而不是代码 —— 请勿包含具体的实现代码

质量控制
每一行都必须具备独立的价值
在清晰的标题下使用简洁的项目符号列表
在进行精简（而非删除）时：保留核心事实，去掉冗长的细节
如果不确定是否应该删除，请保留该内容，但加上 (verify currency)（需验证时效性）的标记 -->