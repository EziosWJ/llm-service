# API 手动测试指南

使用 `test_api.py` 脚本手动测试所有端点。脚本基于项目已有的 `httpx`，无额外依赖。

## 前置条件

服务已启动：

```bash
uv run uvicorn src.main:app --reload
```

所有测试命令统一用 `uv run python` 执行，确保走项目虚拟环境：

```bash
uv run python test_api.py <command> [options]
```

## 全局选项

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `--base-url` | `http://localhost:8000` | 服务地址 |
| `--timeout` | `120` | 请求超时（秒） |

## 端点测试

### 1. GET / — 服务状态

```bash
uv run python test_api.py root
```

预期响应：

```json
{
  "service": "llm-service",
  "status": "ok"
}
```

### 2. GET /health — 健康检查

浅层检查（不探测 LLM）：

```bash
uv run python test_api.py health
```

深度检查（探测 LLM 连通性）：

```bash
uv run python test_api.py health --deep
```

预期响应：

```json
{
  "status": "healthy",
  "checks": {
    "qdrant": {"status": "ok", "detail": "reachable"},
    "llm": {"status": "ok", "detail": "reachable"}
  }
}
```

状态说明：`healthy`（全部正常）、`degraded`（部分正常）、`unhealthy`（全部失败）。

### 3. POST /materials/process — 上传材料

该接口采用覆盖语义：同一 `material_id` 和 `user_id` 重新处理时，会先删除旧向量，再写入新片段。

```bash
uv run python test_api.py process --file <文件路径> --material-id <材料ID> --user-id <用户ID>
```

示例：

```bash
uv run python test_api.py process --file ./demo.txt --material-id mat_001 --user-id user_1
```

支持格式：`.txt`、`.docx`、`.pdf`。

预期响应：

```json
{
  "deleted_count": 0,
  "chunk_count": 8
}
```

### 4. DELETE /materials/{id}/vectors — 删除向量

```bash
uv run python test_api.py delete --material-id <材料ID> --user-id <用户ID>
```

必须按用户过滤：

```bash
uv run python test_api.py delete --material-id mat_001 --user-id user_1
```

预期响应：

```json
{
  "deleted_count": 8
}
```

### 5. POST /generate — 内容生成

必填参数：

| 参数 | 说明 |
|------|------|
| `--type` | 生成类型：`outline`、`draft`、`polished`、`title` |
| `--topic` | 写作主题 |
| `--user-id` | 用户 ID |

可选参数：

| 参数 | 说明 |
|------|------|
| `--content` | 补充内容（`polished` 类型时必填） |
| `--material-ids` | 材料 ID 列表，逗号分隔；指定时必须非空 |
| `--top-k` | 返回片段数量，默认 5 |

示例：

```bash
# 生成提纲
uv run python test_api.py generate --type outline --topic "人工智能发展" --user-id user_1

# 生成初稿（指定材料）
uv run python test_api.py generate --type draft --topic "人工智能发展" --user-id user_1 --material-ids mat_001,mat_002

# 润色稿件（content 必填）
uv run python test_api.py generate --type polished --topic "润色" --user-id user_1 --content "原文内容..."

# 生成标题（限制片段数）
uv run python test_api.py generate --type title --topic "人工智能发展" --user-id user_1 --top-k 3
```

预期响应：

```json
{
  "generated_text": "生成的内容...",
  "sources": [
    {
      "text": "引用的片段内容",
      "material_id": "mat_001",
      "chunk_index": 3,
      "score": 0.85
    }
  ]
}
```

### 6. POST /ask — 知识问答

必填参数：

| 参数 | 说明 |
|------|------|
| `--query` | 用户问题 |
| `--user-id` | 用户 ID |

可选参数：

| 参数 | 说明 |
|------|------|
| `--material-ids` | 材料 ID 列表，逗号分隔；指定时必须非空 |
| `--top-k` | 返回片段数量，默认 3 |

示例：

```bash
# 基本问答
uv run python test_api.py ask --query "射击游戏有哪些" --user-id user_1

# 指定材料范围
uv run python test_api.py ask --query "帝国时代是什么类型" --user-id user_1 --material-ids mat_001

# 按用户过滤
uv run python test_api.py ask --query "有哪些赛车游戏" --user-id user_1

# 调整检索数量
uv run python test_api.py ask --query "独立游戏有哪些" --user-id user_1 --top-k 5
```

预期响应：

```json
{
  "answer": "根据材料，射击类游戏共有 4 款，分别是...",
  "sources": [
    {
      "text": "引用的片段内容",
      "material_id": "mat_001",
      "chunk_index": 3,
      "score": 0.85
    }
  ]
}
```

与 `/generate` 的区别：`/ask` 用于简短问答，输入是一个问句，返回简洁回答；`/generate` 用于内容创作，输入是写作主题，返回完整文章。

## 常见问题

### Thinking 模式导致超时

部分模型（如 Qwen 3.x）默认开启 thinking/reasoning 模式，会在生成正式内容前输出大量 reasoning tokens。这会导致：

- 请求耗时大幅增加（60 秒以上）
- 客户端超时断开，但服务端 LLM 仍在运行
- 再次请求又会重复相同过程

**现象**：LM Studio 日志中 `reasoning_content` 有大量内容，但 `content` 为空。

**解决**：服务默认已关闭 thinking 模式（`LLM_ENABLE_THINKING=false`）。如需开启，在 `.env` 中设置：

```
LLM_ENABLE_THINKING=true
```

并相应增大超时：

```bash
uv run python test_api.py --timeout 300 generate --type draft --topic "..."
```

## 错误场景测试

| 场景 | 命令 | 预期状态码 |
|------|------|-----------|
| `polished` 缺 `content` | `generate --type polished --topic "test"` | 422 |
| `topic` 为空 | `generate --type outline --topic ""` | 422 |
| 不支持的文件类型 | `process --file test.csv --material-id m1 --user-id u1` | 400/500 |
| 服务未启动 | 任意命令 | 连接失败提示 |
