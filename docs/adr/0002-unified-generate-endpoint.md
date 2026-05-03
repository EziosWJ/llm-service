# 四种生成类型共用统一端点

提纲、初稿、润色稿、标题四种生成类型共用 `POST /generate` 端点，通过请求体中的 `type` 字段区分，内部根据类型选择不同的 Prompt 模板。

## Considered Options

- **A: 统一端点** — 一个 `/generate`，`type` 字段区分类型。
- **B: 四个独立端点** — `/generate/outline`、`/generate/draft` 等，各有独立的请求/响应模型。

## Consequences

- Java 端调用方式统一，只需切换 `type` 字段，减少集成代码。
- 新增生成类型时，Python 端只需加一个 Jinja2 模板，不需要新增端点和路由。
- 润色类型需要额外的 `content` 字段，通过 Pydantic 的 `model_validator` 校验，略微增加请求模型复杂度。
- 如果未来某类生成的输入差异很大（比如需要完全不同的参数），统一模型可能变得臃肿——届时可拆分。
