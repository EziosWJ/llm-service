#!/usr/bin/env python3
"""手动 API 测试脚本。

用法:
    python test_api.py root
    python test_api.py health [--deep]
    python test_api.py process --file <path> --material-id <id> --user-id <id>
    python test_api.py delete --material-id <id> [--user-id <id>]
    python test_api.py generate --type <type> --topic <topic> [--content <text>] [--material-ids <id,...>] [--user-id <id>] [--top-k <n>]

全局选项:
    --base-url <url>   服务地址，默认 http://localhost:8000
"""

import argparse
import json
import sys

import httpx


def pp(data):
    """格式化打印 JSON。"""
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_root(args):
    with httpx.Client(base_url=args.base_url, timeout=args.timeout) as c:
        r = c.get("/")
    print(f"[{r.status_code}]")
    pp(r.json())


def cmd_health(args):
    params = {"deep": str(args.deep).lower()}
    with httpx.Client(base_url=args.base_url, timeout=args.timeout) as c:
        r = c.get("/health", params=params)
    print(f"[{r.status_code}]")
    pp(r.json())


def cmd_process(args):
    with httpx.Client(base_url=args.base_url, timeout=args.timeout) as c, open(args.file, "rb") as f:
        files = {"file": (args.file, f)}
        data = {"material_id": args.material_id, "user_id": args.user_id}
        r = c.post("/materials/process", files=files, data=data)
    print(f"[{r.status_code}]")
    pp(r.json())


def cmd_delete(args):
    params = {}
    if args.user_id:
        params["user_id"] = args.user_id
    with httpx.Client(base_url=args.base_url, timeout=args.timeout) as c:
        r = c.delete(f"/materials/{args.material_id}/vectors", params=params)
    print(f"[{r.status_code}]")
    pp(r.json())


def cmd_generate(args):
    payload = {
        "type": args.type,
        "topic": args.topic,
    }
    if args.content:
        payload["content"] = args.content
    if args.material_ids:
        payload["material_ids"] = [s.strip() for s in args.material_ids.split(",")]
    if args.user_id:
        payload["user_id"] = args.user_id
    if args.top_k:
        payload["top_k"] = args.top_k

    with httpx.Client(base_url=args.base_url, timeout=args.timeout) as c:
        r = c.post("/generate", json=payload)
    print(f"[{r.status_code}]")
    pp(r.json())


def main():
    parser = argparse.ArgumentParser(description="llm-service API 测试脚本")
    parser.add_argument("--base-url", default="http://localhost:8000", help="服务地址")
    parser.add_argument("--timeout", type=float, default=120.0, help="请求超时（秒），默认 120")
    sub = parser.add_subparsers(dest="command", required=True)

    # root
    sub.add_parser("root", help="GET /")

    # health
    p = sub.add_parser("health", help="GET /health")
    p.add_argument("--deep", action="store_true", help="深度检查（探测 LLM）")

    # process
    p = sub.add_parser("process", help="POST /materials/process")
    p.add_argument("--file", required=True, help="材料文件路径")
    p.add_argument("--material-id", required=True, help="材料 ID")
    p.add_argument("--user-id", required=True, help="用户 ID")

    # delete
    p = sub.add_parser("delete", help="DELETE /materials/{id}/vectors")
    p.add_argument("--material-id", required=True, help="材料 ID")
    p.add_argument("--user-id", default=None, help="用户 ID（可选）")

    # generate
    p = sub.add_parser("generate", help="POST /generate")
    p.add_argument("--type", required=True, choices=["outline", "draft", "polished", "title"], help="生成类型")
    p.add_argument("--topic", required=True, help="写作主题")
    p.add_argument("--content", default=None, help="补充内容（polished 时必填）")
    p.add_argument("--material-ids", default=None, help="材料 ID 列表，逗号分隔")
    p.add_argument("--user-id", default=None, help="用户 ID")
    p.add_argument("--top-k", type=int, default=None, help="返回片段数量")

    args = parser.parse_args()

    dispatch = {
        "root": cmd_root,
        "health": cmd_health,
        "process": cmd_process,
        "delete": cmd_delete,
        "generate": cmd_generate,
    }
    try:
        dispatch[args.command](args)
    except httpx.ConnectError:
        print(f"连接失败: {args.base_url}，请确认服务已启动", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
