# 水木 PPT 插件市场

面向 ChatGPT 和 Codex 的水木 PPT 工作流插件。直接描述想法即可先得到完整逐页设计文档，再按需要
进入原生可编辑、标题栏混合图片版和整页图片版等九种制作流程；也可以只交付设计文档。

当前插件版本：`0.1.0+codex.20260917082415`。更新内容见 [CHANGELOG.md](CHANGELOG.md)。

## 安装

在安装了 Codex CLI 的环境中执行：

```bash
codex plugin marketplace add doouuyu/shuimu-ppt-marketplace
codex plugin add shuimu-ppt-suite@shuimu-ppt-marketplace
```

安装后重新启动 ChatGPT/Codex 桌面应用，并新建一个任务，让 Codex 加载插件中的 Skills。

也可以在桌面应用的 Plugins 页面选择“水木 PPT 插件市场”，然后安装“水木 PPT 套件 · Shuimu PPT Suite”。

## 使用

没有设计文档时，可以直接输入自然语言：

```text
使用 $shuimu-ppt。我想做一份介绍我们产品的 PPT，给初次接触的用户看。
重点讲能解决的问题、具体优势和使用方法，少讲技术原理。
下面是我的想法和资料：……
先只给我 Markdown 设计文档，写出每页完整文案、布局和配图要求。
科技风，保持整套统一；实际 PPT 模板我会在制作时提供。
```

生成的 `design/PPT设计文档.md` 包含受众与目标、叙事结构、完整逐页文案、布局与视觉、素材要求和
必要的缺项说明。未指定页数时按内容拟定；已有完整设计文档则直接复用，不要求重新准备材料。

也可单独调用 `$ppt-design-brief` 生成设计文档。只要大纲或只改一页时按所需范围处理。
实际模板后补不妨碍先完成内容设计，模板提供后再绑定其视觉与安全区。

希望直接得到 PPT 时说明完整交付范围：

```text
使用 $ppt-image-blue-orange-blocks，按下面的需求直接制作 8 页 PPT：……
我没有设计文档，请先整理每页设计，再继续生成图片和最终 PPTX。
```

九种制作流程都接入了需求设计步骤。明确要求直接制作时会继续执行；只有用户要求先审设计、
确认后再制作，或存在影响结果的关键缺项时才等待，不把“确认设计”设成所有任务的必经步骤。

让 Codex 自动选择工作流：

```text
使用 $shuimu-ppt，根据我的内容和编辑性要求选择合适的水木 PPT 工作流并制作 PPT。
```

也可以直接调用插件内的工作流：

- `$aihia`
- `$qinghua-changgung-blue-realistic-tech`（清华长庚蓝写实科技风）
- `$pixel-defense-academic-ppt`（像素答辩学术汇报风）
- `$editable-ppt`（可编辑 PPT 风格，独立流程）
- `$artifact-template-shuimu-qinglv-ppt`
- `$artifact-template-shuimu-qinglv-image-ppt`
- `$artifact-template-shuimu-yilan-ppt`
- `$ppt-image-blue-orange-blocks`
- `$ppt-image-deck`

## 运行要求

- 支持 Plugins 的 ChatGPT/Codex 桌面应用或 Codex CLI
- OpenAI `Presentations` 插件，用于读取、创建和验证演示文稿
- 内置 `image_gen`，用于图片型 PPT 工作流
- Node.js 与 Python 3；部分工作流会使用演示文稿运行时依赖

仅生成 Markdown 设计文档不依赖 `image_gen` 或 PPT 运行时。“可编辑 PPT 风格”制作阶段需要
Presentations 提供的 `@oai/artifact-tool` 演示文稿运行时。其流程为：自然语言/内容材料 → 共用设计文档
→ 模板绑定与逐页制作设计 → 素材设计文档 + 详细排版设计文档 → 独立素材 → 原生文字、图形、表格与
图表组装。已有完整设计时跳过重复整理。缺少运行时不能承诺完成最终 PPTX；不能用整页图片冒充可编辑内容。

指定 AIHIA、水木青绿等原生模板时，该流程复用模板原封面、章节过渡、标题栏、主题与结束页；仅有图片参考的风格按参考构图做可编辑重建，不声称具有原生模板结构。正文组装前必须生成并验收无字装饰素材，不支持跳过生图。默认采用疏朗柔和的专业排版，只有明确选择像素答辩时使用该风格。

正式页面不留“待补充/演示数据”等占位痕迹；缺少依据的数据省略或改定性表达，不编造临时数据冒充事实。缺项另列在独立审查文档中。

可编辑流程默认普通屏幕阅读：标题 28–34 pt、正文 18–22 pt、表格/提示词 18–20 pt、注释 14–16 pt，仅标题与重点适度加粗，允许高对比深灰正文。用户的设计文档与模板优先；只有明确要求远距离投影时才使用较大字号的 projection 档，投影档下限也较旧版降低 2 pt。内容放不下先调整布局，不自动缩小。

## 仓库结构

```text
.agents/plugins/marketplace.json   # Marketplace 入口
plugins/shuimu-ppt-suite/          # 插件主体
  .codex-plugin/plugin.json        # 插件清单
  skills/                           # 总入口、需求设计与九种 PPT 制作工作流
  tests/                            # 契约与可移植性测试
```

## 更新

获取 marketplace 的新版本：

```bash
codex plugin marketplace upgrade shuimu-ppt-marketplace
codex plugin add shuimu-ppt-suite@shuimu-ppt-marketplace
codex plugin list
```

在插件列表中确认 `shuimu-ppt-suite` 已安装。本次预期版本为 `0.1.0+codex.20260917082415`。更新后请新建任务；若桌面应用仍显示旧版，可重启应用后再新建任务。

可在新任务中输入：

```text
使用 $editable-ppt，套用 AIHIA 原模板封面、章节过渡和标题栏。
先输出逐页设计、素材设计和详细排版设计，再生成无字装饰素材并组装可编辑 PPT。
```

如果提示找不到市场，先执行安装章节中的 `codex plugin marketplace add doouuyu/shuimu-ppt-marketplace`，再安装插件。如果上述命令不受支持，请先更新 Codex CLI。

如果之前仅下载 ZIP 或手动复制了 Skill，以上命令不会替换原来的手动副本。建议改用本仓库的市场安装方式，并在确认新版可用后停用重复的旧副本，以免调用到旧技能。

## 许可

本仓库当前未附带开源许可证。
