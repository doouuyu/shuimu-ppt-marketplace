# 模板与装饰绑定

读取[按需复用规则](../../../shared/template-reuse.md)与[风格目录](../../../styles/catalog.json)。未指定风格默认清华长庚绿，制作方式默认图文混排。
模板和图片是实际资源，风格名称不触发独立模板建设。蓝色已有文件直接用；缺少目标颜色时在当前稿适配必要的封面/标题栏，登记真实源件与改动，不先创建可复用模板项目。

## 清华长庚绿

- 封面/内容页优先使用已认可的 approved-reference.pptx
- 目录/章节/结束页按需要使用原始 reference.pptx；只做前20页时不额外加结束页
- 统一科技背景和相关插画从风格包直接复用，source=style，bundle_key 对应 catalog.json 的 design_assets
- 背景放满整页画布，文字和图表位于安全区，白字标题栏及结论条按参考保持

`style.reference_path` 指定主源件；个别页面来自另一个已登记源件时，在 `template_source.reference_path` 写相对布局文件的实际路径。
每页声明 `template_source.slide`、`mode`、`preserve`；封面/目录/章节/结束页 duplicate-slide，正文可 reuse-header。
保留真实源对象及角色映射，不把仅图片参考当原生模板。用户指定其他文件时用custom及真实路径记录。
封面用 cover_slots 映射 hero 与 title 原生文字对象；源页不是只有图片和Logo，主题大字也必须有对应填充内容。

新设计使用 design_contract_version=2，生图前锁定文档和布局。图片参考风格说明 reference_anchor，复杂素材按页面构图生成；图中可编辑文字单独原生排布。
