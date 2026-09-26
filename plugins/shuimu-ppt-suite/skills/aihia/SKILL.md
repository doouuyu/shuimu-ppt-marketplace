---
name: aihia
description: "Create a hybrid image-based PPT using the retained AIHIA reference: duplicate its native cover, generate each content body with image_gen, and overlay the original editable purple title bar, title text, and authentic AIHIA logo. Use when the user explicitly invokes $aihia, selects the AIHIA template, asks for AIHIA/华医智锦标题栏或封面, or requests a deck in this exact AIHIA purple medical-technology visual system. Do not invoke for generic purple, medical, AI, or technology styling without an explicit AIHIA/template request."
---

# AIHIA 图片混合 PPT

## 样式优先级

用户在本次对话输入框明确写出的要求 > 所选 Skill 规范 > 附件设计文档的样式建议。
附件仅用于逐页内容、页序和图文摆放参考；全局字体字号、配色、层级及装饰按 Skill 执行。
“按附件制作”不自动授权附件样式覆盖 Skill。使用附件前遵循[样式来源规则](../ppt-design-brief/references/style-priority.md)。

使用保留的 AIHIA 模板创建图片主体与原生品牌对象混合的演示文稿：封面直接复制原模板第 1 页，普通
内容页由 `image_gen` 生成主体图片，再叠加原模板第 6 页的可编辑标题、紫色渐变标题栏和真实 AIHIA Logo。
始终保持 `assets/reference.pptx` 不变，输出为新的 PPTX。

## 制作前：需求转设计

先按 [../ppt-design-brief/SKILL.md](../ppt-design-brief/SKILL.md) 判断范围与输入完整性。
只有自然语言、对话或大纲时先形成逐页设计；已有完整设计直接复用，并保留本 Skill 的模板与编辑性要求。
只交设计或用户要求等确认时，到文档交付为止；已授权制作则按页面 ID 和上屏文案继续以下流程。

## Workflow

1. 完整读取 `references/template-guide.md`、`references/prompt-format.md` 和
   `references/manifest-format.md`。
2. 加载 [@presentations](plugin://presentations@openai-primary-runtime)，把
   `assets/reference.pptx` 作为唯一封面、标题栏、Logo、配色和品牌视觉来源。不得重绘、仿造或替换
   AIHIA Logo。
3. 把用户提供的材料作为唯一内容来源。先规划页面：第 1 页必须为 `cover`；普通正文页使用
   `content`。原生封面负责标题、副标题、汇报人与日期；正文内容由图片模型生成。
4. 为每个 `content` 页编写独立图片提示词。画布固定 16:9、3840×2160，顶部 0—240 px 严格留空，
   主体内容从 y≥270 px 开始。不得让图片模型生成页面标题、AIHIA Logo、页码或标题栏。
5. 每个 `content` 页只调用一次内置 `image_gen` 生成整张主体图片。禁止用 HTML、SVG、Canvas、
   Pillow、matplotlib、PowerPoint 文本框或其他程序式方式绘制主体内容。
6. 逐页使用 `view_image` 检查中文、数字、术语、裁切、顶部安全区、配色和一致性。任何错字、乱码、
   伪文字或进入顶部安全区的内容都必须重生成对应页面，不得程序覆盖修补。
7. 创建 `manifest.json`。封面条目不需要图片；正文条目必须提供图片文件名和单行标题。
8. 运行 `scripts/build_aihia_deck.mjs`。脚本复制原模板第 1 页作为封面并替换原生文本；复制第 6 页
   作为正文页，只保留紫色标题栏、标题文本框和 AIHIA Logo，再把主体图片铺满并调整到标题栏下层。
9. 渲染最终 PPTX 的每一页，检查封面文本、标题栏几何、Logo 清晰度、标题换行、主体遮挡、图片边界
   和残留占位内容。修正后重新汇总，直至全部通过。

## 汇总命令

先按 Presentations Skill 初始化 Artifact Tool 工作区。把当前 Skill 的绝对目录记为 `AIHIA_SKILL_DIR`，
再运行：

```bash
node <presentations-skill>/container_tools/setup_artifact_tool_workspace.mjs \
  --workspace <工作区>

node "$AIHIA_SKILL_DIR/scripts/build_aihia_deck.mjs" \
  --workspace <工作区> \
  --images <主体图片目录> \
  --manifest <manifest.json> \
  --python <工作区依赖中的 Python 路径> \
  --out <输出.pptx>
```

## Fidelity

- 原生封面来源固定为参考稿第 1 页；不得用图片模型近似重做封面。
- 原生标题栏来源固定为参考稿第 6 页；必须保留其 `#694CD5 → #6F34A7` 紫色渐变、白色标题和
  右上角真实 AIHIA Logo。
- 图片主体遵循参考稿的紫色、靛蓝、洋红、少量电光蓝和白底医疗科技视觉，但不得复制模板示例文字、
  示例数据或无关照片。
- 封面文字和页面标题为原生可编辑对象；正文图片中的文字、图表和图形不可逐项编辑。不得声称整页
  内容均可编辑。

用户指令决定内容和明确要求的偏离；未明确要求修改的 AIHIA 品牌对象、几何和配色均以保留模板为准。
