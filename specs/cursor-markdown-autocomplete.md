# Cursor Markdown 智能补全设置

**文件路径**：`C:\Users\<用户名>\AppData\Roaming\Cursor\User\settings.json`

## 完整配置

```json
{
    "cursor.cpp.disabledLanguages": [],
    "cursor.cpp.enablePartialAccepts": true,
    "[markdown]": {
        "editor.quickSuggestions": {
            "other": true,
            "comments": true,
            "strings": true
        },
        "editor.wordBasedSuggestions": "allDocuments",
        "editor.suggestOnTriggerCharacters": true,
        "editor.acceptSuggestionOnEnter": "on",
        "editor.inlineSuggest.enabled": true,
        "editor.inlineSuggest.showToolbar": "always"
    }
}
```

## 关键项说明

| 设置项 | 作用 |
|--------|------|
| `cursor.cpp.disabledLanguages: []` | 清空 AI 补全禁用列表，确保 Markdown 不被排除（**核心**） |
| `cursor.cpp.enablePartialAccepts` | 允许 `Ctrl+→` 逐词接受 AI 建议 |
| `editor.inlineSuggest.enabled` | 启用内联 AI 灰色补全提示 |
| `editor.quickSuggestions` | 输入时自动弹出补全候选框 |

## 快捷键

| 操作 | 快捷键 |
|------|--------|
| 接受全部建议 | `Tab` |
| 逐词接受 | `Ctrl+→` |
| 拒绝 | `Esc` |

修改后执行 `Ctrl+Shift+P` → `Reload Window` 生效。
