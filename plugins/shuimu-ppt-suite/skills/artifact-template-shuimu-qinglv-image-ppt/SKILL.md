---
name: artifact-template-shuimu-qinglv-image-ppt
description: "Create a hybrid image-based PPT that uses image_gen for each slide body and overlays the original editable Beijing Tsinghua Changgung Hospital title bar (title, hospital logo, and teal background) from the retained 水木青绿 reference. Use only when the user's prompt explicitly requests the 清华长庚标题栏、北京清华长庚医院标题栏、清华长庚标题+Logo+底色、水木青绿图片版, or explicitly invokes $artifact-template-shuimu-qinglv-image-ppt. Do not invoke for generic green/medical styling, ordinary 清华长庚 content, the editable 水木青绿 template, or requests that do not explicitly require this title bar."
---

# 水木青绿图片版 · 原生标题栏混合 PPT

使用 `image_gen` 生成每页主体图片，再把保留的清华长庚原生标题栏覆盖到图片上方。始终保持
`assets/reference.pptx` 不变，输出为新的 PPTX。

## 触发门禁

仅在用户提示词明确要求以下任一事项时使用：

- 使用“清华长庚标题栏”或“北京清华长庚医院标题栏”；
- 使用原始清华长庚“标题 + Logo + 标题栏底色”；
- 使用“水木青绿图片版”；
- 显式调用 `$artifact-template-shuimu-qinglv-image-ppt`。

仅提到青绿色、医疗、医院、清华长庚内容或水木青绿风格时不得触发。若用户要求全原生可编辑，改用
`$artifact-template-shuimu-qinglv-ppt`；若不要求清华长庚标题栏，改用普通图片版 PPT 工作流。

## 制作前：需求转设计

触发门禁满足后，按 [../ppt-design-brief/SKILL.md](../ppt-design-brief/SKILL.md) 判断范围与输入完整性。
只有自然语言、对话或大纲时先形成逐页设计；已有完整设计直接复用，并保留本 Skill 的模板与编辑性要求。
只交设计或用户要求等确认时，到文档交付为止；已授权制作则按页面 ID 和上屏文案继续以下流程。

## Workflow

1. 读取 `artifact-template.json`，相对于本 Skill 目录解析参考 PPTX 与预览路径。
2. 完整读取 `references/template-guide.md`、`references/prompt-format.md` 和
   `references/manifest-format.md`。
3. 加载 [@presentations](plugin://presentations@openai-primary-runtime)，把保留的
   `assets/reference.pptx` 作为唯一品牌与标题栏来源；不得重绘、伪造或近似生成医院 Logo。
4. 把用户提供的材料作为唯一内容来源。先规划页面，再为每页确定 `header: true|false`：普通内容页默认
   `true`；封面、章节页和结束页默认 `false`，除非用户明确要求普通标题栏。
5. 为每页编写独立图片提示词。普通内容页只让 `image_gen` 生成主体层：画布为 16:9、3840×2160，
   顶部 240 px 严格留空，任何正文、图形、标题、Logo 或装饰不得进入；主体内容从 y≥270 px 开始。
6. 标题安全区使用平整的白色或与页面底色连续的浅色背景。不得用阴影、下划线、分隔线、描边、色块
   边缘或渐变断层暗示标题区域；不得让图片模型生成页面标题或医院标识。
7. 每页只调用一次内置 `image_gen` 生成整张主体图片；不得使用 HTML、SVG、Canvas、Pillow、
   matplotlib 或程序化绘图生成页面视觉。逐页检查文字、数字、术语、裁切和安全区。
8. 创建 `manifest.json` 后运行 `scripts/build_hybrid_deck.mjs`。脚本以参考稿第 4 页为标题栏来源，
   保留原生标题文本框、医院 Logo 和青绿底色，删除其余原页内容；把主体图片铺满页面，再通过确定性的
   OOXML 图层调整将主体图片置于三个原生标题栏对象之下。
9. 对 `header: true` 的页面，把清单中的 `title` 写入原生标题文本框。标题必须单行，不得把标题烧录
   进主体图片。`header: false` 的页面删除标题栏对象，只保留主体图片。
10. 渲染最终 PPTX，逐页检查标题栏几何、Logo 清晰度、标题换行、顶部遮挡、图片边界、错字和残留
    模板内容。不合格时修正对应图片或标题后重新汇总。

## 汇总命令

先按 Presentations 技能说明初始化 Artifact Tool 工作区。将本 Skill 的绝对目录记为 `SKILL_DIR`，
再运行：

```bash
node <presentations-skill>/container_tools/setup_artifact_tool_workspace.mjs \
  --workspace <工作区>

node "$SKILL_DIR/scripts/build_hybrid_deck.mjs" \
  --workspace <工作区> \
  --images <主体图片目录> \
  --manifest <manifest.json> \
  --python <工作区依赖中的 Python 路径> \
  --out <输出.pptx>
```

## Fidelity

必须原样继承参考稿第 4 页标题栏的对象、层级和几何：青绿底色位于标题栏底层，标题文本框保留原字体
与格式，医院 Logo 使用原图并位于右上角。不得让图片模型重绘 Logo，不得用近似文字或图标代替。

最终普通内容页是混合结构：主体内容为不可逐项编辑的整页图片；页面标题、Logo 和标题栏底色为原生
PowerPoint 对象，其中页面标题可编辑。不得声称主体图片中的文字、图表或图形可编辑。

用户指令决定内容及明确要求的偏离；未明确要求改变的品牌视觉均以保留参考稿为准。
