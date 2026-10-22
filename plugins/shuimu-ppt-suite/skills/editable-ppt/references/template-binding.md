# 模板与装饰绑定

读取[按需复用规则](../../../shared/template-reuse.md)与[风格目录](../../../styles/catalog.json)。未指定风格默认清华长庚绿，制作方式默认图文混排。
模板和图片是实际资源，风格名称不触发独立模板建设。蓝色已有文件直接用；缺少目标颜色时在当前稿适配必要的封面/标题栏，登记真实源件与改动，不先创建可复用模板项目。

## 清华长庚绿的品牌源件与可选素材

- 封面/内容页优先使用已认可的 approved-reference.pptx
- 目录/章节/结束页按需要使用原始 reference.pptx；只做前20页时不额外加结束页
- 背景、插画可从风格包复用，先判断是否适合当前构图；source=style时bundle_key对应catalog.json中的design_assets
- 用户指定的模板保护对象按源件保留；普通正文重新设计，不因有源页就照搬布局。背景位置按当前设计确定

`style.reference_path` 指定主源件；个别页面来自另一个已登记源件时，在 `template_source.reference_path` 写相对布局文件的实际路径。
每页声明 `template_source.slide`、`mode`、`preserve`；封面/目录/章节/结束页 duplicate-slide，正文可 reuse-header。
保留真实源对象及角色映射，不把仅图片参考当原生模板。用户指定其他文件时用custom及真实路径记录。
封面用 cover_slots 映射 hero 与 title 原生文字对象；源页不是只有图片和Logo，主题大字也必须有对应填充内容。

新设计使用 design_contract_version=3，正式素材生成前锁定文档和布局；直接无字视觉层、按需试稿及后续校准按 [design-documents.md](design-documents.md) 执行。图片参考风格说明 reference_anchor，复杂素材按页面构图生成；图中可编辑文字在同一构图中原生排布。
