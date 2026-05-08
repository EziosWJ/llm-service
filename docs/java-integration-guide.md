# Java 后端对接指南

本文档供 Java 后端和后端 agent 对接 Python AI 服务使用。Java 后端以本文档和 Python 服务 `/openapi.json` 为接口契约来源。

## 职责边界

Java 后端负责：

- 材料 CRUD、材料标题、上传人、业务状态和权限校验
- 原始文件存储和下载
- 用户身份、材料归属和前端访问控制
- 调用 Python 服务完成材料向量维护、写作任务和问答

Python 服务负责：

- 解析材料文件，切分片段并写入向量库
- 按 `user_id + material_id` 删除或覆盖材料向量
- 基于材料片段执行写作任务和问答
- 返回来源片段供 Java 或前端展示参考来源

Python 服务不提供材料列表、材料详情、业务权限校验、异步任务状态查询或材料 CRUD。

## 通用规则

- `material_id` 只在 `user_id` 下唯一，不承诺全局唯一。
- 所有材料向量维护、写作任务和问答请求都必须携带 `user_id`。
- Java 调用 Python 前必须完成业务权限校验，Python 只用 `user_id` 做向量隔离。
- `material_ids` 不传或为 `null` 时，按当前 `user_id` 的全部材料检索。
- `material_ids` 传入时必须是非空数组，并按 `user_id + material_ids` 精确检索。
- `material_ids: []` 是参数错误。
- Python 服务为同步阻塞调用，Java 应设置合理 HTTP 超时。
- Python 的自动 OpenAPI 地址为 `/openapi.json`，Swagger UI 地址为 `/docs`。

## 错误响应

统一错误响应：

```json
{
  "error": "validation_error",
  "detail": "错误详情"
}
```

常见 HTTP 状态码：

- `400`: 参数错误，例如缺少 `user_id`、空 `material_ids`、不支持的文件类型
- `422`: 业务校验错误
- `502`: Python 调用上游 LLM 或 embedding 服务失败
- `500`: Python 服务内部错误

Java 建议统一封装 Python 错误响应，不要按接口分别解析错误格式。

## 接口

### 健康检查

```http
GET /health
```

默认健康检查不会触发 LLM 推理。需要深度检查时：

```http
GET /health?deep=true
```

Java 可用于启动探活、运维检查或集成测试前置检查。

### 上传并覆盖材料向量

```http
POST /materials/process
Content-Type: multipart/form-data
```

表单字段：

| 字段 | 必填 | 说明 |
|------|------|------|
| `file` | 是 | 原始材料文件 |
| `material_id` | 是 | Java 材料 ID |
| `user_id` | 是 | 当前用户 ID |

当前支持文件类型：

- `.txt`
- `.docx`
- `.pdf`

请求示例：

```bash
curl -s -X POST "http://127.0.0.1:8000/materials/process" \
  -F "file=@/absolute/path/sample.txt" \
  -F "material_id=mat-001" \
  -F "user_id=user-001"
```

响应示例：

```json
{
  "deleted_count": 0,
  "chunk_count": 8
}
```

语义：

- 该接口采用覆盖语义。
- 同一个 `user_id + material_id` 重新处理时，Python 会先删除旧向量，再写入新片段。
- Java 可用 `deleted_count` 判断本次是否覆盖了旧片段。
- Java 可记录 `chunk_count` 作为材料处理结果。

Java 推荐流程：

1. 校验当前用户是否允许上传或更新材料。
2. 保存原始文件和材料记录。
3. 将材料状态置为 `processing`。
4. 调用 `/materials/process`。
5. 成功后将材料状态置为 `available`，记录 `chunk_count`。
6. 失败后将材料状态置为 `failed`，记录错误详情。

注意：当前覆盖语义是先删后写。若删除旧向量后新文件解析、embedding 或写入失败，该材料可能临时没有可检索片段。Java 必须把材料标记为 `failed`，避免前端继续视为可用材料。

### 删除材料向量

```http
DELETE /materials/{material_id}/vectors?user_id={user_id}
```

路径和查询参数：

| 参数 | 必填 | 说明 |
|------|------|------|
| `material_id` | 是 | Java 材料 ID |
| `user_id` | 是 | 当前用户 ID |

请求示例：

```bash
curl -s -X DELETE "http://127.0.0.1:8000/materials/mat-001/vectors?user_id=user-001"
```

响应示例：

```json
{
  "deleted_count": 8
}
```

Java 推荐流程：

1. 校验当前用户是否允许删除材料。
2. 调用 Python 删除 `user_id + material_id` 对应向量。
3. 删除或软删 Java 自己的材料记录。

不要省略 `user_id`，Python 会将缺少 `user_id` 视为参数错误。

### 内容生成

```http
POST /generate
Content-Type: application/json
```

请求字段：

| 字段 | 必填 | 说明 |
|------|------|------|
| `type` | 是 | `outline`、`draft`、`polished`、`title` |
| `topic` | 是 | 写作主题 |
| `user_id` | 是 | 当前用户 ID |
| `content` | `polished` 时必填 | 原文或补充内容 |
| `material_ids` | 否 | 非空材料 ID 数组 |
| `top_k` | 否 | 返回来源片段数量，默认 `5`，范围 `1-20` |

请求示例：

```json
{
  "type": "draft",
  "topic": "人工智能发展",
  "content": "可选补充要求",
  "user_id": "user-001",
  "material_ids": ["mat-001", "mat-002"],
  "top_k": 5
}
```

响应示例：

```json
{
  "generated_text": "生成的内容...",
  "sources": [
    {
      "text": "引用的片段内容",
      "material_id": "mat-001",
      "chunk_index": 3,
      "score": 0.85
    }
  ]
}
```

规则：

- `user_id` 必填。
- `material_ids` 传入时必须非空。
- 未传 `material_ids` 时，Python 会按该 `user_id` 的所有材料检索。
- Java 在传入 `material_ids` 前必须校验这些材料属于当前用户且允许用于本次写作任务。
- `polished` 类型必须传 `content`，其他类型可选。
- 没有命中来源片段时，写作任务仍会调用大模型。

### 材料问答

```http
POST /ask
Content-Type: application/json
```

请求字段：

| 字段 | 必填 | 说明 |
|------|------|------|
| `query` | 是 | 用户问题 |
| `user_id` | 是 | 当前用户 ID |
| `material_ids` | 否 | 非空材料 ID 数组 |
| `top_k` | 否 | 返回来源片段数量，默认 `3`，范围 `1-20` |

请求示例：

```json
{
  "query": "材料中提到了哪些产品？",
  "user_id": "user-001",
  "material_ids": ["mat-001"],
  "top_k": 3
}
```

响应示例：

```json
{
  "answer": "根据材料，...",
  "sources": [
    {
      "text": "引用的片段内容",
      "material_id": "mat-001",
      "chunk_index": 3,
      "score": 0.85
    }
  ]
}
```

规则：

- `user_id` 必填。
- `material_ids` 传入时必须非空。
- 未传 `material_ids` 时，Python 会按该 `user_id` 的所有材料检索。
- Java 在传入 `material_ids` 前必须校验这些材料属于当前用户且允许用于本次问答。
- 没有命中来源片段时，问答仍会调用大模型，但 Prompt 会要求说明材料不足并避免编造。

## Java 侧建议模型

材料状态建议：

- `processing`: 已保存材料，正在调用 Python 处理
- `available`: Python 处理成功，可用于写作任务和问答
- `failed`: Python 处理失败，不应作为可用材料
- `deleted`: 材料已删除或软删

材料记录建议字段：

- `id`
- `user_id`
- `title`
- `file_path`
- `status`
- `chunk_count`
- `error_message`
- `created_at`
- `updated_at`

Python 客户端建议封装成独立组件，例如 `PythonAiClient` 或 `LlmServiceClient`。业务代码不要散落 HTTP 调用细节。

## 最小联调闭环

建议 Java 后端先跑通以下闭环：

1. 上传 `.txt` 材料。
2. Java 保存材料记录并调用 `/materials/process`。
3. Java 将材料置为 `available`。
4. 调用 `/ask`，指定该 `material_id` 和 `user_id`。
5. 确认返回 `answer` 和 `sources`。
6. 调用 `/materials/{material_id}/vectors?user_id=...` 删除向量。
7. Java 删除或软删材料记录。

该闭环通过后，再接入生成接口、前端展示和更多文件类型。

## 当前 TODO

- 当前材料处理采用先删后写的覆盖语义，处理失败时可能出现材料暂无可检索片段的空窗状态。未来如需保留旧片段直到新片段写入成功，应引入版本化或批次切换机制。
- 后续需要明确 Python 侧最大文件大小或最大解析文本长度，当前先由 Java 上传链路控制。
- `.xlsx` 和 `.pptx` 支持尚未实现，相关任务见 GitHub issue #19-#22。
