# AIHIA 汇总清单格式

`manifest.json` 使用以下结构：

```json
{
  "slides": [
    {
      "role": "cover",
      "title": "项目汇报标题",
      "subtitle": "PROJECT PRESENTATION",
      "presenter": "张三",
      "date": "2026年8月"
    },
    {
      "role": "content",
      "image": "02.png",
      "title": "项目背景与建设目标"
    }
  ]
}
```

## 字段

- `slides`：非空数组，顺序即最终 PPT 页序。
- 第一项必须是唯一的 `cover`。
- `cover.title`：必填、单行，建议不超过 18 个中文字符。
- `cover.subtitle`：可选、单行；不需要时传空字符串。
- `cover.presenter`、`cover.date`：可选，脚本保留“汇报人：”“时间：”标签。
- `content.image`：相对于 `--images` 目录的 PNG、JPEG 或 WebP 文件名，不得重复。
- `content.title`：必填、单行，最多 20 个字符，作为原生可编辑标题写入标题栏。

正文页使用原生标题栏；封面不需要生成图片。当前脚本只接受 `cover` 与 `content` 两种角色，避免把
全页图片误当成 AIHIA 原生封面。
