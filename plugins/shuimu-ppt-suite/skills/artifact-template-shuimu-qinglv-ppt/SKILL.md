---
name: artifact-template-shuimu-qinglv-ppt
description: "Create a presentation using the 水木青绿 · Shuimu Qinglv PPT template and its retained reference file. Use when the user selects this template, names 水木青绿 · Shuimu Qinglv PPT, or explicitly invokes $artifact-template-shuimu-qinglv-ppt. 用于北京清华长庚医院及医疗、科研、学术、工作汇报场景；从保留的12页原始PPTX中复用版式，保持水木青绿色体系、医院标识、字体层级、页眉页脚和原生可编辑对象。"
---

# 水木青绿 · Shuimu Qinglv PPT

## 样式优先级

用户在本次对话输入框明确写出的要求 > 所选 Skill 规范 > 附件设计文档的样式建议。
附件仅用于逐页内容、页序和图文摆放参考；全局字体字号、配色、层级及装饰按 Skill 执行。
“按附件制作”不自动授权附件样式覆盖 Skill。使用附件前遵循[样式来源规则](../ppt-design-brief/references/style-priority.md)。

使用保留的原始 PPTX 创建医疗、科研、学术或工作汇报。始终保持参考文件不变，输出为新的 PPTX。

## 制作前：需求转设计

先按 [../ppt-design-brief/SKILL.md](../ppt-design-brief/SKILL.md) 判断范围与输入完整性。
只有自然语言、对话或大纲时先形成逐页设计；已有完整设计直接复用，并保留本 Skill 的模板与编辑性要求。
只交设计或用户要求等确认时，到文档交付为止；已授权制作则按页面 ID 和上屏文案继续以下流程。

## Workflow

1. 读取 `artifact-template.json`，相对于本 Skill 目录解析模板与预览路径。
2. 规划页面前完整读取 `references/template-guide.md`，按其中的版式角色选择源页面。
3. 加载 [@presentations](plugin://presentations@openai-primary-runtime)，使用其模板跟随工作流导入保留的 `reference.pptx`。
4. 把用户需求和提供的材料作为唯一内容来源；不得为填满模板而编造事实、数据或案例。
5. 为每个输出页指定一个源页面，复制源页并只修改继承的文本、图片、表格或图表对象。允许重复使用同一个源页面承担相同版式角色。
6. 保留水木青绿视觉系统、医院标识、母版、页眉页脚、字体层级、对象几何与原生可编辑结构。不要用通用主题重建，也不要在模板上叠加另一套设计。
7. 清理所有未使用的占位符和演示文案；正文过长时先压缩内容或换版式，不得静默缩小字体。
8. 渲染并逐页检查最终演示文稿，修复溢出、裁切、换行、错位和残留占位文字后再交付。

## Fidelity

保留源页面、版式、母版、字体、几何、图像、图表、表格和重复出现的页面装饰。

用户指令决定内容及明确要求的偏离；未明确要求改动的视觉与格式均以保留的参考模板为准。
