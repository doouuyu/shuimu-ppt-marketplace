---
name: shuimu-ppt
description: Route a presentation request to the correct workflow in the 水木 PPT 套件. Use when the user explicitly invokes $shuimu-ppt, asks to use the 水木 PPT 套件, asks Codex to choose among $editable-ppt、$aihia、$qinghua-changgung-blue-realistic-tech、$pixel-defense-academic-ppt、水木青绿、水木青绿图片版、水木医蓝、$ppt-image-blue-orange-blocks and $ppt-image-deck, or gives a presentation request without knowing which bundled workflow fits. Do not replace a worker skill that the user explicitly invokes.
---

# 水木 PPT 套件路由

本 Skill 只负责选择并交接给正确的工作 Skill，不自行生成幻灯片，也不混合不同工作流的规则。

## 可编辑流程独立入口

用户明确调用 `$editable-ppt` 或选择“可编辑 PPT 风格/可编辑PPT流程”，或明确要求“逐页设计 → 素材设计 + 详细排版设计 → 原生文字图形组装”时，选择 `../editable-ppt/SKILL.md`。

用户同时指定该流程和某种模板/视觉外观时，以可编辑流程执行，并按其 template-binding 规则绑定实际
参考文件。有原生模板必须复用封面、目录、章节过渡、标题栏、主题和结束页，不能只借用配色。
仅有图片参考则匹配参考构图并保留原生文字，不假称复制原生模板；不同时执行图片版流程。
仅说“可编辑”时，保留已明确选用的水木青绿原生模板等原有路由；没有指定本流程时，不自动迁移旧图片版风格。

## 路由原则

按以下优先级判断；一旦命中就停止继续比较。

1. 用户显式写出某个工作 Skill 名称时，直接选择该 Skill。
2. 用户明确要求“AIHIA”“华医智锦模板”“AIHIA 标题栏/封面”，或显式调用 `$aihia` 时，选择该 Skill。
3. 用户明确要求“清华长庚蓝写实科技风”“清华长庚蓝写实风”“清华长庚蓝科技图片版”，或显式调用 `$qinghua-changgung-blue-realistic-tech` 时，选择该 Skill。
4. 用户明确要求“像素答辩学术汇报风”“像素答辩风”“高密度科研答辩图片版”，或显式调用 `$pixel-defense-academic-ppt` 时，选择该 Skill。
5. 用户明确要求“清华长庚标题栏”“北京清华长庚医院标题栏”“清华长庚标题 + Logo + 底色”“水木青绿图片版”时，选择 `$artifact-template-shuimu-qinglv-image-ppt`。
6. 用户明确要求“水木青绿”“清华长庚模板”，并要求原生对象、完整可编辑、沿用原模板版式时，选择 `$artifact-template-shuimu-qinglv-ppt`。
7. 用户明确要求“水木医蓝”，或选择深海军蓝、医疗蓝、数智医疗、科技光线风格时，选择 `$artifact-template-shuimu-yilan-ppt`。
8. 用户明确要求“蓝橙块状图片版”“白底蓝色为主、橙色点缀”“少图标、多色块”，或显式调用 `$ppt-image-blue-orange-blocks` 时，选择该 Skill。
9. 用户要求整页图片 PPT、提供自定义风格文档或参考图，但没有点名上述模板、AIHIA、清华长庚蓝写实科技风、像素答辩学术汇报风、蓝橙块状风格与清华长庚标题栏时，选择 `$ppt-image-deck`。
10. 只有在“水木青绿”请求无法判断要全页可编辑还是图片主体加原生标题栏时，询问一次：需要“原生对象完整可编辑”，还是“图片主体 + 清华长庚原生标题栏”？

## 严格门槛

不得仅因内容与清华长庚医院、医疗或绿色风格有关，就选择 `$artifact-template-shuimu-qinglv-image-ppt`。

只有提示词明确要求清华长庚原生标题栏，或明确写出“水木青绿图片版”/该 Skill 名称时，才可选择图片混合版。

不得仅因内容涉及 AI、医院、医疗科技或紫色风格，就选择 `$aihia`；必须明确点名 AIHIA、华医智锦
模板、AIHIA 原生标题栏/封面或该 Skill 名称。

不得仅因内容涉及医院、蓝色、写实照片、软件界面或科技风，就选择
`$qinghua-changgung-blue-realistic-tech`；必须明确点名“清华长庚蓝写实科技风”或其约定别名，或显式
调用该 Skill。仅要求“水木医蓝”时仍使用 `$artifact-template-shuimu-yilan-ppt`；仅要求清华长庚原生
标题栏时仍使用 `$artifact-template-shuimu-qinglv-image-ppt`。

不得仅因内容是学术、科研、答辩、课题申报或使用蓝色，就选择 `$pixel-defense-academic-ppt`；必须明确
点名“像素答辩学术汇报风”“像素答辩风”“高密度科研答辩图片版”或显式调用该 Skill。

## 交接流程

1. 用一句话告知用户已选择的工作流及原因。
2. 完整读取所选目录中的 `SKILL.md`：
   - `../editable-ppt/SKILL.md`
   - `../aihia/SKILL.md`
   - `../qinghua-changgung-blue-realistic-tech/SKILL.md`
   - `../pixel-defense-academic-ppt/SKILL.md`
   - `../artifact-template-shuimu-qinglv-ppt/SKILL.md`
   - `../artifact-template-shuimu-qinglv-image-ppt/SKILL.md`
   - `../artifact-template-shuimu-yilan-ppt/SKILL.md`
   - `../ppt-image-blue-orange-blocks/SKILL.md`
   - `../ppt-image-deck/SKILL.md`
3. 仅按所选工作 Skill 的要求继续；它引用的资料、脚本和模板按其说明加载。
4. 不同时执行两个工作 Skill，除非用户明确要求制作两个独立版本。

## 快速判断示例

- “用可编辑 PPT 风格，先写素材设计和排版设计，再生成 PPT” → `$editable-ppt`
- “用可编辑 PPT 风格，外观参考清华长庚蓝，文字不要放进图片” → `$editable-ppt`，先确定具体蓝色参考，再绑定源页/图区域与生成无字装饰素材
- “用可编辑 PPT 风格，套用 AIHIA 模板” → `$editable-ppt`，复用 AIHIA 原生封面 1、章节 4、标题栏 6、结束 14，正文原生组装

- “用水木青绿做一份可编辑的科室汇报” → `$artifact-template-shuimu-qinglv-ppt`
- “用 AIHIA 原生封面和标题栏做一套图片版汇报” → `$aihia`
- “用清华长庚蓝写实科技风做一套医院数字化图片版汇报” → `$qinghua-changgung-blue-realistic-tech`
- “用像素答辩学术汇报风做一套项目申报图片版 PPT” → `$pixel-defense-academic-ppt`
- “正文用 image_gen，但要叠加清华长庚标题、Logo 和青绿色底栏” → `$artifact-template-shuimu-qinglv-image-ppt`
- “用水木医蓝做数智医疗项目汇报” → `$artifact-template-shuimu-yilan-ppt`
- “白底，蓝色为主橙色点缀，少图标多色块，做成图片版 PPT” → `$ppt-image-blue-orange-blocks`
- “按我给的风格参考图做整页图片 PPT” → `$ppt-image-deck`
- “帮我用水木 PPT 套件做汇报” → 根据编辑性、指定风格和标题栏要求选择；只有结果会实质变化时才追问。
