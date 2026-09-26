---
name: ppt-image-blue-orange-blocks
description: 端到端生成白底蓝橙块状风格的整页图片 PPT。Use when the user explicitly invokes $ppt-image-blue-orange-blocks, asks for 蓝橙块状图片版、白底蓝色为主橙色点缀、少图标多色块的商务/医疗/科技汇报，或选择该风格并希望从需求文档、内容稿或大纲产出逐页图片和最终 .pptx。复用 $ppt-image-deck 的完整工作流，只替换固定视觉系统；不得仅因普通图片版 PPT 请求而触发。
---

# 蓝橙块状图片版 PPT

## 样式优先级

用户在本次对话输入框明确写出的要求 > 所选 Skill 规范 > 附件设计文档的样式建议。
附件仅用于逐页内容、页序和图文摆放参考；全局字体字号、配色、层级及装饰按 Skill 执行。
“按附件制作”不自动授权附件样式覆盖 Skill。使用附件前遵循[样式来源规则](../ppt-design-brief/references/style-priority.md)。

沿用 `ppt-image-deck` 的端到端流程，用固定的白底、蓝色主视觉、橙色强调和块状信息结构生成整套
16:9 图片版 PPT。只改变视觉风格，不改变提示词文档、逐页生成、逐页核对和 PPTX 汇总步骤。

## 制作前：需求转设计

输入可为自然语言、对话、大纲或已有设计。先读取本 Skill 的 `references/blue-orange-block-style.md`，
再按 [../ppt-design-brief/SKILL.md](../ppt-design-brief/SKILL.md) 补齐逐页设计，已有完整设计则复用。
共用默认不覆盖本风格。只交设计或要求等确认时到文档交付为止；已授权制作继续下方流程，
基础 Skill 中相同的前置步骤不重复执行。

## 执行顺序

1. 把当前 Skill 目录记为 `SKILL_DIR`，解析同一插件中的基础 Skill：
   `../ppt-image-deck/SKILL.md`。
2. 完整读取基础 Skill 的 `SKILL.md` 和
   `../ppt-image-deck/references/prompt-doc-format.md`，把其中四阶段工作流、输入输出、图片生成限制、
   核对标准和汇总方式全部作为强制规则。
3. 完整读取 `references/blue-orange-block-style.md`，把其中固定风格前缀逐字写入每一页图片提示词。
4. 不读取、不使用基础 Skill 的 `references/default-style.md`；本 Skill 的蓝橙块状规范替代它。
5. 若用户另外提供风格参考图或风格文档，只提取与白底、蓝橙、块状信息结构兼容的细节。只有用户明确
   要求改变本风格时才偏离；否则保持本 Skill 的固定视觉系统。
6. 使用用户的需求文档、内容稿和数据作为唯一文字与事实来源。参考图中的示例文字存在问题，只参考
   配色、信息密度和块状构图，不得复制、改写或补全其中任何文字、数字、机构或产品名称。

## 不变的基础工作流

严格执行基础 Skill 的四个阶段：

1. 生成逐页图片提示词文档；
2. 每页只调用一次内置 `image_gen` 生成完整图片；
3. 用 `view_image` 逐页核对并只重生成不合格页面；
4. 用基础 Skill 的 `scripts/build_pptx.py` 把合格图片汇总为全画幅 PPTX。

不得用 HTML、SVG、Canvas、Pillow、matplotlib、PowerPoint 文本框或其他程序式方式绘制页面内容。
代码只允许在最终汇总阶段把整张页面图片放入 PPTX。

## 风格覆盖规则

- 固定使用白底和清晰的蓝色主视觉，橙色仅作重点、对照或行动项强调。
- 默认用 2–6 个大块状信息容器构成页面，优先矩形、横条、双栏、矩阵和步骤块。
- 默认每页使用 0–2 个图标，确有语义需要时最多 3 个；图标不得成为主体。
- 避免徽章、印章、复杂环形箭头、装饰性人物、照片拼贴和密集小图标。
- 保证中文锐利、逐字准确；信息装不下时拆页或压缩文案，不缩成小字。
- 图片中不放页码、Logo、院徽、水印和与内容无关的装饰性英文。

## 文字验收门槛

逐页把生成图片与该页“画面文字”和核对锚点比对。任何错字、漏字、多字、乱码、伪文字、数字错误、
术语错误或参考图残留文字都判定为不合格，必须重生成对应页面。不得通过程序覆盖文字来修补图片。

## 汇总脚本

从当前 Skill 目录解析基础脚本，不假设用户目录结构：

```bash
python "$SKILL_DIR/../ppt-image-deck/scripts/build_pptx.py" \
  --images <项目>/images \
  --out <项目>/out/<方案名>.pptx
```

最终交付提示词文档、逐页图片、核对结果和 `.pptx`，并明确说明页面主体是整张图片，内部文字和图形
不可逐项编辑。
