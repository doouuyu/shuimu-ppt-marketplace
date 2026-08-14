# 汇总清单格式

`manifest.json` 使用以下结构：

```json
{
  "slides": [
    {
      "image": "01.png",
      "role": "cover",
      "header": false
    },
    {
      "image": "02.png",
      "role": "content",
      "header": true,
      "title": "项目背景与建设目标"
    }
  ]
}
```

## 字段

- `slides`：非空数组，顺序即最终 PPT 页序。
- `image`：相对于 `--images` 目录的 PNG、JPEG 或 WebP 文件名；不得重复。
- `role`：页面角色，如 `cover`、`content`、`section`、`ending`，用于核对，不改变脚本逻辑。
- `header`：是否覆盖清华长庚原生标题栏。
- `title`：`header: true` 时必填；必须为单行非空文字，建议不超过 24 个中文字符。

普通内容页默认应设置 `header: true`。封面、章节页和结束页默认设置 `header: false`。
