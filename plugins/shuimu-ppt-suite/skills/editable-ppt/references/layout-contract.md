# layout.json 约定

此清单是逐对象组装的输入，不是某个 PPT API 的直接参数。构建器按当前官方本地 API 映射这些值。
校验工具使用 Python 标准库，不安装依赖；它只读取输入文件。

完整单页示例见 `layout-example.json`，包含原生标题、正文、表格和注释，可作为字段起点，不能把示例
内容当成用户材料。该例没有需要生成的图片，所以 assets 为空。

## 顶层与素材

```json
{
  "workflow": "editable-ppt",
  "canvas": {"width": 1280, "height": 720, "unit": "px"},
  "assets": [],
  "slides": []
}
```

素材项：`id, path, kind, source, text_free`。path 相对于 layout.json 所在目录，如 `../assets/A001.png`。
source 为 generated/user/external；生成项必须 `text_free: true`。这只是声明，仍须看图核实。
外部资产写 `source_url`，生成素材记录 `prompt`，已有实物记录 `width_px/height_px`。

## 每页与所有元素

页：`id: P01`、`role: cover/content/...`、`elements: [...]`。可另带背景色、来源注释及预期重叠记录。
所有元素必须有全套唯一的 `id`、`type`、`box: [x,y,w,h]`、`z`。
type 支持 text/image/shape/connector/table/chart。无论元素是否在组内，都保留自己的名称和编辑能力。

元素的 PPT 名称必须等于 id。实际图表/表格对象也要命名；若 API 不支持命名某类型，可以在最终导出前
有针对性地设置相应 OOXML cNvPr name，并重新渲染核对，不能靠调整检查清单掩盖对象缺失。

## 文字示例

```json
{
  "id": "P01-title", "type": "text", "box": [48, 28, 1184, 76], "z": 2,
  "text": "专病科研平台建设", "font_family": "Microsoft YaHei",
  "font_size_pt": 32, "bold": true, "color": "#10367D",
  "align": "left", "valign": "middle", "margin_px": [0, 0, 0, 0],
  "line_spacing": 1.15, "paragraph_after_pt": 0,
  "max_lines": 1, "overflow": "reflow_then_revise"
}
```

此字体名只是示例，构建前确认安装。实际 fontFamily / fontSizePt / verticalAlignment 等属性以本机
presentations 文档为准。支持 `runs` 记录局部强调；text 仍需是全部 runs 的合并文字，以便核对。

## 其他类型

- image：`asset_id`、`fit: contain/cover`；可加 `crop`/`focus`，在排版文档解释归一化单位。
- shape：`geometry`（如 rect）、`fill`、`stroke`、`stroke_width_px`；文本另建 text 元素。
- connector：`from/to` 为同页对象 ID，补充连接边、`line_color/line_width_px/end_arrow`。
  box 是连接线外包框（水平或垂直线也保留至少 1 px 的审计包络）。
- table：`rows` 二维数组；`column_widths/row_heights` 均为 px；`font_family/font_size_pt`；
  以及表头颜色、边框、内边距、列对齐等样式。各列宽与行高之和应等于 box 的宽/高。
- chart：`chart_type`、`categories`、`series: [{name, values}]`、`font_family/font_size_pt`；
  以及轴、数据标签、格式、颜色、单位。系列长度须等于类别数；百分比值/显示格式不得混淆。

检查工具验证基本字段、尺寸、引用、数据形状和部分原生对象属性，不计算字体的真实占用宽度，也不证明
重叠合理、资产没有文字、图表数据正确或 PowerPoint 中可正常调整。必须另外执行渲染/数据/编辑验证。
