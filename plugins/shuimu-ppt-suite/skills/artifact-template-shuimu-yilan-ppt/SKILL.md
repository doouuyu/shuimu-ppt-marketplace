---
name: artifact-template-shuimu-yilan-ppt
description: "Create a presentation using the 水木医蓝 · Shuimu Yilan PPT template and its retained reference file. Use when the user selects this template, names 水木医蓝 · Shuimu Yilan PPT, or explicitly invokes $artifact-template-shuimu-yilan-ppt. 用于医院、临床科研、数智医疗、国家项目合作及学术工作汇报场景；基于保留的 30 页参考 PPTX，复用深海军蓝与医疗蓝配色、清爽留白、流动科技光线、建筑线稿、清晰中文层级和 16:9 全画幅版式。"
---

# 水木医蓝 · Shuimu Yilan PPT

使用保留的 30 页参考 PPTX 创建医院、临床科研、数智医疗、国家项目合作或学术工作汇报。始终保持参考文件不变，输出为新的 PPTX。

本模板是**整页图片型模板**：参考稿每页是一张全画幅图片，不含可直接替换的原生文本框、图表或表格对象。新内容必须生成新的整页视觉，禁止把新文本框覆盖在旧页图片上。

## Workflow

1. 读取 `artifact-template.json`，相对于本 Skill 目录解析参考 PPTX 与预览路径。
2. 规划页面前完整读取 `references/template-guide.md`，按其中的版式角色选择参考页。
3. 加载 [@presentations](plugin://presentations@openai-primary-runtime)，把保留的 `reference.pptx` 作为唯一视觉依据；不得混用其他模板或通用主题。
4. 把用户需求和提供的材料作为唯一内容来源；不得为填满版式而编造事实、数据、机构、人物、照片或案例。
5. 为每个输出页指定一个参考页角色，提炼其构图、信息密度、配色、字体层级、图标语言和装饰方式。
6. 使用内置 `image_gen` 为每个输出页生成一张完整的 16:9 全画幅页面图片，页面文字直接烧录在图中；一页一次调用。除非用户要求保留原页内容，否则不得直接复用参考页中的具体文字或数据。
7. 禁止用 HTML、SVG、Canvas、Pillow、matplotlib、程序化图形或 PowerPoint 文本框重建页面；代码仅可用于把最终整页图片无边距汇总为 PPTX。
8. 全套页面保持水木医蓝视觉系统。信息过多时压缩文案、换版式或拆页，不得用小字硬塞。
9. 逐页核对中文、数字、术语、裁切、留白、边界、色彩和残留占位文字；不合格页只重生成对应页面。
10. 汇总为新 PPTX 后渲染全部页面复检，再交付最终演示文稿；不得修改保留的 `reference.pptx`。

## Fidelity

保留参考稿的 16:9 画幅、深海军蓝与医疗蓝体系、白到浅冰蓝内容页、深蓝首尾页、清晰中文层级、建筑线稿、流动科技光线、轻薄线性图标和克制装饰。

用户指令决定内容与明确要求的偏离；未明确要求改动的视觉与格式均以保留参考为准。不得复制参考稿中的南昌大学第一附属医院名称、国家项目名称、示例数字或合作单位，除非用户提供并明确要求使用。

若用户要求原生可编辑文本、表格或图表，应先说明本模板为整页图片型模板，并改用适合原生对象的模板或工作流，不得声称图片内文字可编辑。
