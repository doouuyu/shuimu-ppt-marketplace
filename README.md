# 水木 PPT 插件市场

面向 ChatGPT 和 Codex 的水木 PPT 工作流插件。插件包含模板路由、原生可编辑模板、标题栏混合图片版和整页图片版等九种 PPT 工作流。

当前插件版本：`0.1.0+codex.20260917034842`。更新内容见 [CHANGELOG.md](CHANGELOG.md)。

## 安装

在安装了 Codex CLI 的环境中执行：

```bash
codex plugin marketplace add doouuyu/shuimu-ppt-marketplace
codex plugin add shuimu-ppt-suite@shuimu-ppt-marketplace
```

安装后重新启动 ChatGPT/Codex 桌面应用，并新建一个任务，让 Codex 加载插件中的 Skills。

也可以在桌面应用的 Plugins 页面选择“水木 PPT 插件市场”，然后安装“水木 PPT 套件 · Shuimu PPT Suite”。

## 使用

让 Codex 自动选择工作流：

```text
使用 $shuimu-ppt，根据我的内容和编辑性要求选择合适的水木 PPT 工作流。
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

“可编辑 PPT 风格”需要 Presentations 提供的 `@oai/artifact-tool` 演示文稿运行时。其流程为：Markdown 内容 → 逐页设计 → 素材设计文档 + 详细排版设计文档 → 独立素材 → 原生文字、图形、表格与图表组装。缺少运行时不能承诺完成最终 PPTX；不能用整页图片冒充可编辑内容。

指定 AIHIA、水木青绿等原生模板时，该流程复用模板原封面、章节过渡、标题栏、主题与结束页；仅有图片参考的风格按参考构图做可编辑重建，不声称具有原生模板结构。正文组装前必须生成并验收无字装饰素材，不支持跳过生图。默认采用疏朗柔和的专业排版，只有明确选择像素答辩时使用该风格。

正式页面不留“待补充/演示数据”等占位痕迹；缺少依据的数据省略或改定性表达，不编造临时数据冒充事实。缺项另列在独立审查文档中。

可编辑流程默认面向大屏投影：标题至少 36 pt、正文至少 24 pt、表格/图表标签至少 22 pt、必要脚注至少 20 pt，全部加粗。浅底使用黑色或高对比深品牌色，深底用白字，禁止灰字和半透明字；内容放不下时调整布局/精简文案，不自动缩小。模板原有小灰字同样需要适配，封面、标题栏和品牌结构保持不变。

## 仓库结构

```text
.agents/plugins/marketplace.json   # Marketplace 入口
plugins/shuimu-ppt-suite/          # 插件主体
  .codex-plugin/plugin.json        # 插件清单
  skills/                           # 路由与九种 PPT 工作流
  tests/                            # 契约与可移植性测试
```

## 更新

获取 marketplace 的新版本：

```bash
codex plugin marketplace upgrade shuimu-ppt-marketplace
codex plugin add shuimu-ppt-suite@shuimu-ppt-marketplace
codex plugin list
```

在插件列表中确认 `shuimu-ppt-suite` 已安装。本次预期版本为 `0.1.0+codex.20260917034842`。更新后请新建任务；若桌面应用仍显示旧版，可重启应用后再新建任务。

可在新任务中输入：

```text
使用 $editable-ppt，套用 AIHIA 原模板封面、章节过渡和标题栏。
先输出逐页设计、素材设计和详细排版设计，再生成无字装饰素材并组装可编辑 PPT。
```

如果提示找不到市场，先执行安装章节中的 `codex plugin marketplace add doouuyu/shuimu-ppt-marketplace`，再安装插件。如果上述命令不受支持，请先更新 Codex CLI。

如果之前仅下载 ZIP 或手动复制了 Skill，以上命令不会替换原来的手动副本。建议改用本仓库的市场安装方式，并在确认新版可用后停用重复的旧副本，以免调用到旧技能。

## 许可

本仓库当前未附带开源许可证。
