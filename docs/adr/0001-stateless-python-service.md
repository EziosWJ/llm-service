# Python 服务无状态，不访问业务数据库

Python AI 服务不直接访问 Java 后端的业务数据库（如 MySQL/PostgreSQL），所有业务上下文（用户 ID、材料 ID、检索范围等）由 Java 后端通过 HTTP 请求参数传入。Python 服务只管理自己的向量库（Qdrant）。

## Considered Options

- **A: Python 直接连接业务数据库** — 可以直接查询用户、材料表，减少 Java 端传参量。
- **B: Python 完全无状态** — 所有业务数据由 Java 通过请求传入。

## Consequences

- Python 服务独立部署，不依赖业务数据库 schema，双方可独立演进。
- Java 端需要在每次调用时组装完整的业务上下文，接口参数较多。
- Python 服务的数据库依赖仅限 Qdrant，部署和运维更简单。
- 未来如果 Python 服务需要扩展为多实例，无状态天然支持水平扩展。
