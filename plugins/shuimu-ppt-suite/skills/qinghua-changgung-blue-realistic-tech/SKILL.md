---
name: qinghua-changgung-blue-realistic-tech
description: 端到端生成“清华长庚蓝写实科技风”的整页图片 PPT：冰白底、深海军蓝标题、亮蓝/青蓝模块、少量橙色数字强调，结合写实医疗人物/场景与真实感软件界面，并使用蓝色流线渐变章节页。Use when the user explicitly invokes $qinghua-changgung-blue-realistic-tech, selects “清华长庚蓝写实科技风”, asks for “清华长庚蓝写实风/清华长庚蓝科技图片版”, or requests the exact style represented by this skill's retained reference montage. Reuse $ppt-image-deck's workflow while replacing its default visual system. Do not invoke for generic blue, medical, realistic, hospital, or technology presentations, and do not confuse it with 水木医蓝 or the 清华长庚原生标题栏 workflow.
---

# 清华长庚蓝写实科技风

## 样式优先级

用户在本次对话输入框明确写出的要求 > 所选 Skill 规范 > 附件设计文档的样式建议。
附件仅用于逐页内容、页序和图文摆放参考；全局字体字号、配色、层级及装饰按 Skill 执行。
“按附件制作”不自动授权附件样式覆盖 Skill。使用附件前遵循[样式来源规则](../ppt-design-brief/references/style-priority.md)。

沿用 `ppt-image-deck` 的端到端图片版工作流，使用固定的冰白蓝色、结构化信息、写实医疗场景与
软件界面视觉生成整套 16:9 PPT。只替换视觉系统，不改变逐页提示词、图片生成、验收和汇总流程。

## 制作前：需求转设计

输入可为自然语言、对话、大纲或已有设计。先读取本 Skill 的 `references/style-contract.md`，
再按 [../ppt-design-brief/SKILL.md](../ppt-design-brief/SKILL.md) 补齐逐页设计，已有完整设计则复用。
共用默认不覆盖本风格。只交设计或要求等确认时到文档交付为止；已授权制作继续下方流程，
基础 Skill 中相同的前置步骤不重复执行。

## 执行顺序

1. 把当前 Skill 目录记为 `SKILL_DIR`，完整读取同一插件中的基础 Skill：
   `../ppt-image-deck/SKILL.md`。
2. 完整读取 `../ppt-image-deck/references/prompt-doc-format.md`，继承其中的四阶段工作流、输入输出、
   图片生成限制、逐页核对和 PPTX 汇总规则。
3. 完整读取 `references/style-contract.md`，把其中“固定风格前缀”逐字写入每一页图片提示词，并按
   页面角色选用对应版式。
4. 需要重新确认整体观感时，用 `view_image` 查看 `assets/style-reference.jpg`。该图只证明风格，
   不得作为内容来源，也不得直接传给图片模型诱导复制其中的缩略文字、数字或页面内容。
5. 不读取、不使用基础 Skill 的 `references/default-style.md`；本 Skill 的视觉契约完全替代它。
6. 使用用户材料作为唯一文字与事实来源。先压缩长文案或拆页，再生成页面；不得为了匹配参考图而
   编造项目、平台、医院、人物、软件功能、数据或结论。

## 不变的基础工作流

严格执行基础 Skill 的四个阶段：

1. 生成逐页图片提示词文档；
2. 每页只调用一次内置 `image_gen` 生成完整 3840×2160 图片；
3. 用 `view_image` 逐页核对，只重生成不合格页面；
4. 用 `../ppt-image-deck/scripts/build_pptx.py` 把合格图片汇总为全画幅 PPTX。

禁止用 HTML、SVG、Canvas、Pillow、matplotlib、PowerPoint 文本框或其他程序式方式绘制页面。
代码只允许在最终汇总时把完整页面图片放入 PPTX。

## 风格覆盖规则

- 内容页以冰白或极浅蓝为底；深海军蓝建立标题层级，亮蓝与青蓝承担信息结构，橙色只强调关键数字。
- 所有内容页保留左上统一标题锚点：顶部短竖线、横向细线、深蓝标题和一行小副标题。
- 常规页面采用“结构化文字 + 单一写实视觉”的非对称构图；视觉可为医疗人物/场景、设备或软件界面。
- 软件界面必须简洁可信，只有用户提供的关键标签可读；不得生成成片随机微文字、虚构品牌或伪造截图。
- 章节页使用居中深蓝标题与底部蓝色流线渐变，不使用照片、卡片阵列或满屏装饰。
- 数据页优先蓝色表格、条形图和大数字，橙色只突出 1–3 个核心值。
- 图片中不生成 Logo、院徽、水印或页码；用户明确提供并授权的品牌资产另行按其要求处理。

## 验收门槛

逐页同时检查：文字逐字准确、数字和术语正确、冰白蓝色体系稳定、标题锚点一致、写实视觉与内容相关、
软件界面没有乱码、橙色不过量、章节页流线结构正确。任何错字、伪文字、参考图残留内容、过度 3D、
满屏深蓝、密集小卡片或无关人物都判定为不合格，必须重生成该页，不得程序覆盖修补。

## 汇总命令

```bash
python "$SKILL_DIR/../ppt-image-deck/scripts/build_pptx.py" \
  --images <项目>/images \
  --out <项目>/out/<方案名>.pptx
```

最终交付逐页提示词文档、页面图片、验收结果和 `.pptx`，并明确说明整页主体是图片，内部文字、
图表、界面和照片不可逐项编辑。
