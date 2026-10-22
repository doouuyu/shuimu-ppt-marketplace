# 新任务设计约定（v3）

新建图文混排任务使用design_contract_version=3。先形成内容与视觉决策，再展开元素和素材，正式素材生成前冻结设计。旧v2可验证并沿已有快照续作，检查输出明确标记兼容，不自动迁移或补造设计。

## 整页与模块设计接口

每页visual_design包含：
- focus：作为视觉重点的模块ID
- reading_order：内容模块ID列表，顺序不重复，包含focus；纯装饰模块不必进入阅读顺序
- background：render_method（native/image/hybrid）、appearance、decision_reason、element_ids；背景只认领图片和图形；原生页面底色可使用空element_ids并设置slide.background
- modules：每项id、purpose、appearance、render_method、decision_reason、element_ids、text_region_ids

appearance应说明本页有意义的分组、主次与图文融合，轮廓、材质等只记录影响画面的决定；decision_reason说明为何该方案适合内容、文字量与编辑需求。不得用统一泛化描述或坐标表替代实际设计判断。
所有非模板保护元素须归入背景或一个模块，同一元素不重复归属。原生模块不含图片，image模块只含图片，hybrid模块同时含图片与原生对象。模块中的文字、表格和图表用region_id关联composition.regions，其区域ID列入模块text_region_ids。

素材usage_role为evidence/illustration/decoration/container。真实记录evidence不得source=generated，须记录source_url或source_path；其他用途可生成。每项素材记录crop_policy，说明裁切/伸缩范围。
container额外记录aspect_ratio（计划宽高比）和text_safe_regions（一个或多个归一化[x,y,w,h]，范围0到1）。素材框与承载的原生文字归属同一hybrid模块。整页联合视觉层同样适用：可包含多个实际承载区，由text_region_ids列出，不能仅将整幅画布视为文字安全区；模块的用途说明各分区对应关系，不要求把共享图层重复归属多个模块。图像到位后可记录actual_text_safe_regions，表示人工查看得到的实际安全区，不改写原提示词。框体完整contain放置，不裁切；文字须落在其实际安全区。校验按实际图片尺寸计算contain后的留白偏移，生成比例变化后须校准布局，不拉伸硬套。

构图记录与准确文案、图片提示词写入同一设计文档；与layout.json一起冻结。生成结果更新状态、尺寸和来源；改变设计或几何须先同步文档，再freeze --revise。
背景可用原生、图片或混合，不以“一张全页生成背景”作为混排通行条件；用户明确指定的模板背景与品牌对象继续保留。

# layout.json 约定

此清单是逐对象组装的输入，不是某个 PPT API 的直接参数。构建器按当前官方本地 API 映射这些值。
校验工具使用 Python 标准库，不安装依赖；它只读取输入文件。

`layout-example.json` 保留为旧v2兼容示例，不是新任务设计起点。新任务按上方v3规则独立设计，不套用该示例的内容或版式。

## 顶层与素材

```json
{
  "workflow": "editable-ppt",
  "readability_profile": "screen",
  "canvas": {"width": 1280, "height": 720, "unit": "px"},
  "style": {"id": "shuimu-qinglv", "reference_kind": "native-template", "reference_path": "../references/reference.pptx", "explicitly_requested": false},
  "assets": [{"id": "A001", "path": "../assets/A001.png", "kind": "decoration",
    "source": "generated", "purpose": "decorative", "text_free": true,
    "prompt": "无字、无数字的柔和蓝色波纹，右侧构图，白底", "status": "planned"}],
  "slides": []
}
```

这是字段示意，实际 slides 不能空，必须落实设计中生成或复用的图片。模板绑定字段见 template-binding.md。
style 必填，不得隐式选择像素答辩。样式按输入框明确要求 → 所选 Skill → 附件建议执行。
需要记录例外时，user_overrides 使用包含 source: user_message、用户原话 quote、element_ids 与 properties 的对象；
禁止用附件字号或自由文本声称用户例外。例外记录不自动免除数值与渲染检查。命名原生模板必须核对 reference_path 与套件原文件，按源页角色复用。

素材项：`id, path, kind, source, text_free`。path 相对于 layout.json 所在目录，如 `../assets/A001.png`。
source 为 generated/user/external/template/style；生成项必须 `text_free: true`、完整 prompt 和 status。
使用生成素材或已验收风格素材。正文 visual 可为 primary-image、native-figure、native-content 或 text-only；按内容决定，不默认每页主图。v2装饰用decoration_asset_id登记；v3背景按visual_design.background记录。
v3中旧visual.strategy仅为兼容字段，不代替visual_design。正式构建要求生成素材status=accepted及实际width_px/height_px，仍须看图核实。
外部资产写 `source_url`，生成素材记录 `prompt`，已有实物记录 `width_px/height_px`。

## 每页与所有元素

页：`id: P01`、`role: cover/content/...`、`elements: [...]`。可另带背景色、来源注释及预期重叠记录。
原生模板每页须有 template_source，图片参考须有 reference_anchor；不要把封面改称 content 绕过检查。
所有元素必须有全套唯一的 `id`、`type`、`box: [x,y,w,h]`、`z`。
type 支持 text/image/shape/connector/table/chart。无论元素是否在组内，都保留自己的名称和编辑能力。
仅继承原模板的设计性出血对象可声明 `template_bleed: true` 和 `source_object`（原对象名称/ID），
并保留 template_source；必须与源页并排检查，不能将新增越界对象标记成模板出血绕过检查。

元素的 PPT 名称必须等于 id。实际图表/表格对象也要命名；若 API 不支持命名某类型，可以在最终导出前
有针对性地设置相应 OOXML cNvPr name，并重新渲染核对，不能靠调整检查清单掩盖对象缺失。

## 文字示例

```json
{
  "id": "P01-title", "type": "text", "box": [48, 28, 1184, 76], "z": 2,
  "text": "专病科研平台建设", "font_family": "Microsoft YaHei", "text_role": "title",
  "font_size_pt": 32, "bold": true, "color": "#10367D", "background_color": "#FFFFFF",
  "align": "left", "valign": "middle", "margin_px": [0, 0, 0, 0],
  "line_spacing": 1.15, "paragraph_after_pt": 0,
  "max_lines": 1, "overflow": "reflow_then_revise"
}
```

此字体名只是示例，构建前确认安装。实际 fontFamily / fontSizePt / verticalAlignment 等属性以本机
presentations 文档为准。支持 `runs` 记录局部强调；text 仍需是全部 runs 的合并文字，以便核对。

所有文字（含表格/图表）按 projection-readability.md 中选定的阅读场景检查，默认 screen；仅明确远距离投影时选择 projection。screen 不要求全部加粗，也不禁止对比度合格的深灰文字。
text_role 取 cover_title/title/subtitle/section_title/body/label/node_title/support/footnote/metric；metric 仅用于简短关键数字，不参与副标题与普通正文的比较；漏写时普通文字按 body、表格/图表按 label，
ID 以 -title 结尾按标题检查，以 -subtitle 结尾按副标题检查。页面副标题必须用 subtitle，不能标成 body/footnote。
同页主标题、副标题、正文/标签/节点之间至少各差 2 pt（随画布缩放），局部 runs/text_styles 也参与比较；分区标题可独立通过字重建立层级。
support 必须用 parent_id 关联同页主标签，字号至少小1pt，局部覆盖同样检查。副标题不可通过局部覆盖降低角色。具体字号依阅读规范，无副标题时无需创建对象。
background_color 为文字实际背景，未写则继承 slide.background（未写页面背景时默认白色）。深底白字
或色块上的字必须显式声明该局部背景；照片/渐变按最不利位置检查。文字 opacity 只能是 1。
表格声明 header_color/header_fill/body_color/body_fill/alternate_fill；每格继承的 font_size_pt、
bold 也要写在表格元素上。图表默认文字写 color/font_size_pt/bold，不依赖运行时的小灰字默认值。
局部 runs 和表格单元格/图表轴图例覆盖的 text_styles 用扁平字段记录，如
`{"text_role":"label","font_size_pt":20,"bold":false,"color":"#111111"}`，继承对象其余字段；
局部背景不同也写 background_color。text_styles 仅是设计映射，不直接作为库 API 参数。

## 其他类型

- image：`asset_id`、`fit: contain/cover`；可加 `crop`/`focus`，在排版文档解释归一化单位。
- shape：`purpose`（template/background/separator/diagram/content-panel）、`geometry`、`fill`、
  `stroke`、`stroke_width_px`、`corner_radius_px`；文本另建 text 元素。内容容器按本页分组需要、模板与风格选择，不统一要求开放、封闭或圆角。
- connector：`from/to` 为同页对象 ID，补充连接边、`line_color/line_width_px/end_arrow`。
  box 是连接线外包框（水平或垂直线也保留至少 1 px 的审计包络）。
- table：`rows` 二维数组；`column_widths/row_heights` 均为 px；`font_family/font_size_pt`；
  以及表头颜色、边框、内边距、列对齐等样式。各列宽与行高之和应等于 box 的宽/高。
- chart：`chart_type`、`categories`、`series: [{name, values}]`、`font_family/font_size_pt`；
  以及轴、数据标签、格式、颜色、单位、`source_ref`。系列长度须等于类别数；百分比值/显示格式不得混淆。

对外内容不得标记 data_status 为 temporary/mock/synthetic/unverified；不把假数值当正式事实。
`review_gaps` 可保存页面/对象/缺项与省略方式，构建器不得写入 PPT 正文、备注或隐藏页。
文字、表格、图表标签不得带制作占位语；真实预测/目标的必要限定要保留。

检查工具验证基本字段、尺寸、引用、数据形状和部分原生对象属性，不计算字体的真实占用宽度，也不证明
重叠合理、资产没有文字、图表数据正确或 PowerPoint 中可正常调整。必须另外执行渲染/数据/编辑验证。

## 正文主视觉声明

```json
{"visual":{"strategy":"primary-image","primary_asset_id":"A001","relationship":"呈现本页研究型病房与数据采集关系"}}
```

兼容字段：主图purpose=primary，kind使用scene/illustration/architecture等语义类型；装饰purpose=decorative。v3另以usage_role区分真实性、示意、装饰与素材框。
原生主图声明 element_ids（实际 table/chart/connector 或 purpose=diagram 的 shape）及 reason。
图像可见主体尺寸、语义与风格仍须看最终渲染，声明本身不代表验收。

## 阅读安全区与模块边距

v3每页声明composition，从本页文字容量与模块设计确定阅读安全区和内边距，例如：

```json
{"composition":{"safe_area":[32,16,1216,688],"regions":[{"id":"system-13","box":[190,296,170,180],"padding_px":14}]}}
```

文字、表格和图表须在阅读安全区内；背景与有意出血装饰不受此内容边距约束。region_id 关联区域，检查该对象不侵入其 padding_px；容器本身不关联自己的内边距。模块层级与阅读路径仍由视觉核对，不能只保证文字框没有重叠。
