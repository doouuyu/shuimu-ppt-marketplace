# 水木 PPT 插件市场

面向 ChatGPT 和 Codex 的水木 PPT 工作流插件。插件包含模板路由、原生可编辑模板、标题栏混合图片版和整页图片版等六种 PPT 工作流。

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

## 仓库结构

```text
.agents/plugins/marketplace.json   # Marketplace 入口
plugins/shuimu-ppt-suite/          # 插件主体
  .codex-plugin/plugin.json        # 插件清单
  skills/                           # 路由与六种 PPT 工作流
  tests/                            # 契约与可移植性测试
```

## 更新

获取 marketplace 的新版本：

```bash
codex plugin marketplace upgrade shuimu-ppt-marketplace
codex plugin add shuimu-ppt-suite@shuimu-ppt-marketplace
```

更新后请重新启动桌面应用，并在新任务中测试。

## 许可

本仓库当前未附带开源许可证。
