# 模板绑定：先继承，再填内容

“可编辑”决定制作流程，用户指定的模板决定视觉，两者独立。引用下列 Skill 的模板资源和视觉指南，
不执行其整页图片工作流。不得因正文可编辑而重新设计封面、标题栏和过渡页。

## 选型

路径相对本 Skill 根目录。源 PPTX 只读，复制到项目 references/ 后记录相对路径；不得覆盖源文件。

| 用户指定 | style.id / reference_kind | 实际参考 | 复用方式 |
| --- | --- | --- | --- |
| 水木青绿、清华长庚青绿模板、清华长庚标题栏 | shuimu-qinglv / native-template | ../artifact-template-shuimu-qinglv-ppt/assets/reference.pptx | 封面 1，目录 2，章节 3/6/9，正文 4/5/7/8/10/11，结束 12；通用标题栏来自 4 |
| AIHIA、华医智锦模板 | aihia / native-template | ../aihia/assets/reference.pptx | 封面 1，目录 3，章节过渡 4，正文标题栏 6，结束 14 |
| 水木医蓝 | shuimu-yilan / image-reference | ../artifact-template-shuimu-yilan-ppt/assets/reference.pptx | 30 页均为整页图片；按其 template-guide 的角色目录匹配构图，不能声称原生复制 |
| 清华长庚蓝写实科技风 | qinghua-changgung-blue-realistic-tech / image-reference | ../qinghua-changgung-blue-realistic-tech/assets/style-reference.jpg | 读取 style-contract；逐页记录参考蒙太奇区域，匹配浅蓝留白、写实主视觉和蓝色流线章节 |
| 像素答辩 | pixel-defense-academic-ppt / image-reference | ../pixel-defense-academic-ppt/assets/content-layout-reference.png | 仅明确选择时读取其 page-family-map、style-contract 和其他页角色参考 |
| 蓝橙块状 | custom / image-reference | 用户所选参考图 | 读取 ../ppt-image-blue-orange-blocks/references/style-contract.md；保留蓝橙比例和留白，缺少参考图时先明确视觉依据 |
| 用户提供其他 PPTX | custom / native-template 或 image-reference | 用户实际文件 | 先检查是否有原生对象，建立页面角色清单，不能假定存在可编辑母版 |
| 未指定风格 | neutral / none | 无 | 使用本流程的柔和专业默认视觉，不隐式借用像素答辩 |

“青花长庚”按语境规范为“清华长庚”。只说“清华长庚风格”且不能从附件/上下文确定青绿、医蓝、
蓝写实哪一个时，先问一次；不能随意选择。用户实际附带的模板优先于同名内置模板，此时用 custom
记录实际源文件。不要将图片型医蓝静默替换成青绿。

## 绑定记录与源页检查

1. 完整读取所选模板的 template-guide 或 style-contract；查看封面、目录、过渡、标题栏和结束页。
2. 检查实际尺寸、主题字体、配色、母版/版式继承、装饰、图片裁切和字号，记录到 01-逐页设计首部。
3. 每个目标页记录源页号/参考图区域、角色、哪些对象保持、哪些替换、正文安全区。角色值统一为
   cover/toc/section/content/ending；标题过渡页属于 section。
4. AIHIA 默认用第 1 页封面，不把第 2 页备选封面混入；章节用第 4 页，结束用第 14 页。第 15 页
   没有可复用正文，不作为结束页。删除模板自带的原项目标题、日期、规模数据和重复/隐藏占位文本。

原生绑定示例（layout.json 所在目录为 design/）：

```json
{
  "style": {
    "id": "aihia", "reference_kind": "native-template", "explicitly_requested": true,
    "reference_path": "../references/aihia-reference.pptx"
  },
  "slides": [{
    "id": "P01", "role": "cover",
    "template_source": {
      "slide": 1, "mode": "duplicate-slide",
      "preserve": ["theme", "layout", "background", "logo", "title-style"]
    }
  }]
}
```

以上仅示范绑定字段，不是可独立执行的完整布局。正文允许 `reuse-header`，其他角色用
`duplicate-slide`。preserve 表示保护规则：不存在的 Logo 不得发明，存在的 Logo 不得重绘。
内置原生模板用文件哈希与保留原件核对；不允许通过改 style.id 隐藏模板不匹配。

## 原生页的实际组装

导入并复制原页，保留主题、母版、背景、装饰图、对象几何及样式；替换已有文本，不从空白页重新摆。
正文清除不属于新内容的示例对象，在继承安全区加入可编辑内容与新生成素材。标题、页码、图形和真实
Logo 使用原对象或原始媒体。将保留对象映射到目标元素 ID；设计清单也须包含这些对象，不能只登记新正文。
原模板允许的出血在设计文档明确说明，渲染确认后保留，不为了适配坐标校验而改变模板构图。

## 只有图片参考时

不能复用不存在的原生文字/主题。仍要匹配其封面、过渡和标题的构图：先从实际参考提取无字背景/装饰，
或用 imagegen 基于参考生成无字视觉素材；再把原生文字放回参考对应位置、尺寸与样式。记录
`reference_anchor`（源 PPT 页码或蒙太奇中的具体页/区域）、视觉重建差异。不得直接贴含旧标题的整页图，
也不得因需要可编辑而自行换一套封面。真实 Logo 单独复用，不交给图片模型重绘。
模板无法忠实导入、缺少关键原件时先说明障碍，不静默改为 neutral。
