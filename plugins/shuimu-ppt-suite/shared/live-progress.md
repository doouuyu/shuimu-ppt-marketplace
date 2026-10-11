# PPT Live 运行进度

三个制作模式共用同一个发布工具。读取完整设计后先调用 `node "$SKILL_DIR/../../shared/live_progress.mjs" status`；已配置时自动注册任务并发布各页进度。未配置则跳过同步，继续正常制作，不为此改变用户需求或质量检查。

用户先在网页生成个人凭据，再用 PPT Live CLI 的 `configure --server <地址> --token-stdin` 配置制作端。配置文件位于本机用户配置目录，包含 CLI 的 `cliPath`；也可用 `PPT_LIVE_CONFIG` 指定配置，或用绝对路径 `PPT_LIVE_CLI` 指定工具。不要将凭据写进设计文档、素材或构建源码。发布工具不依赖本机仓库位置。

## 注册与发布

`PROJECT` 是本次 PPT 的任务目录，续作沿用该目录及其中 `.ppt-live` 状态。完整页序、ID 和标题在开始制作前一次性注册；不要以“已完成页”作为任务页清单。图文混排可直接读取完整布局，其余模式提供同序的 `[{"id":"P01","title":"标题"}, …]` JSON 文件。

```bash
LIVE="$SKILL_DIR/../../shared/live_progress.mjs"
node "$LIVE" init --project "$PROJECT" --title "本次方案名称" --layout "$PROJECT/design/layout.json" --producer Codex
# 原生模板和纯图片模式：把 --layout 换成 --slides <完整页清单.json>
node "$LIVE" start --project "$PROJECT" --page P01 --stage "素材制作"
node "$LIVE" preview --project "$PROJECT" --page P01 --file <实际素材图.png> --kind asset
node "$LIVE" preview --project "$PROJECT" --page P01 --file <实际整页渲染.png> --kind page
# 查看渲染并完成该页检查后才发布通过
node "$LIVE" done --project "$PROJECT" --page P01 --reviewed
```

只上传实际可看的图片。素材图、正文局部图归 `asset`；原生封面、标题栏与正文全部合成后的整页渲染归 `page`。纯图片模式没有原生叠层时，经核对的整页生成图可直接发布为整页；带原生叠层时先发布素材，组装后再发布完整渲染。

修改已发布页面前再次 `start`，网页保留上一版并标记更新中；新整页上传后重新检查，不沿用旧版通过状态。失败时发布 `error --project "$PROJECT" --page P01 --message "简短失败原因"`。任务只有完整页清单，素材就绪也不等于整页完成。

发布工具先保存稳定事件 ID 与图片副本，再尝试联网；断网或服务暂时不可用会进入本地待传队列，后续调用或 `node "$LIVE" sync --project "$PROJECT"` 补传。不启动常驻同步程序。认证失效、身份不符或版本冲突须按返回提示处理，不能覆盖其他身份的任务或盲目重试旧版本。同步失败如实报告，不中止制作，不跳过 PPT 的质量检查，也不声称网页已更新。

## 图文混排单页预览

使用 `editable-ppt/scripts/preview_page.mjs`，先核验完整设计快照、文案、页序与结构，仅要求所选页引用的图片文件准备完毕。它不会截短计划或重编号；其余页面的设计错误仍须修复。模板源件在设计阶段即须可读。

```bash
node "$SKILL_DIR/scripts/preview_page.mjs" \
  --plan "$PROJECT/design/layout.json" --page P01 \
  --renderer "$PROJECT/build.mjs" --project "$PROJECT" \
  --out "$PROJECT/.build/previews/P01.png"
```

任务构建模块导出 `async assembleSlide({plan, slide, slideIndex, planPath, baseDir})`，返回 artifact-tool 的 `{presentation, slide}`。参数 `slide` 是完整计划中的当前页，`slideIndex` 保留原页序；返回 `slide` 是实际原生页面。模块导入时不运行最终构建，只有直接执行时才启动完整组装。单页和整套构建共用同一个组装函数，从布局读取文案、几何、图表数据和素材，复用实际模板对象，不返回 HTML 截图、另造预览版式或把原生正文烧进图片。

入口自行调用原生 `presentation.export` 生成 PNG，保存页码、计划和素材哈希，自动发布“制作中”和“整页预览”。它不会自动发布“检查通过”。可用 `--no-publish` 只渲染，用 `--python` 或 `PPT_LIVE_PYTHON` 选择 Python。任务模块按 presentations 的本地依赖说明从自己的 `node_modules` 解析运行时，正式工具不包含私人目录。

最终构建仍运行完整 `design_snapshot.py verify`、`validate_deck.py --require-assets` 和最终 `--pptx` 审查。最终导出后按实际播放顺序渲染，每页以 `preview --kind final --source-hash <最终PPTX的SHA256>` 更新，再检查并 `done --reviewed`。单页预览的计划哈希不能冒充最终文件哈希；所有终稿预览引用同一份最终文件。
