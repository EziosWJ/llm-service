# 问题追踪：GitHub

本仓库的问题和 PRD 以 GitHub Issues 的形式管理。所有操作通过 `gh` CLI 完成。

## 约定

- **创建问题**：`gh issue create --title "..." --body "..."`。多行内容使用 heredoc。
- **查看问题**：`gh issue view <number> --comments`，可用 `jq` 过滤评论并获取标签。
- **列出问题**：`gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'`，可配合 `--label` 和 `--state` 过滤。
- **评论问题**：`gh issue comment <number> --body "..."`
- **添加/移除标签**：`gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **关闭问题**：`gh issue close <number> --comment "..."`

仓库信息从 `git remote -v` 自动推断——`gh` 在 clone 目录内运行时会自动识别。

## 当技能说"发布到问题追踪器"

创建一个 GitHub Issue。

## 当技能说"获取相关工单"

运行 `gh issue view <number> --comments`。
