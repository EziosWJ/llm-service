from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from src.bootstrap import get_container

router = APIRouter(tags=["health"])


@router.get("/health")
def health(deep: bool = Query(default=False)) -> JSONResponse:
    container = get_container()
    checks: dict[str, dict[str, str]] = {}
    ok_count = 0
    total_checks = 1

    try:
        container.qdrant_store.client.get_collection(container.qdrant_store.collection_name)
        checks["qdrant"] = {"status": "ok", "detail": "reachable"}
        ok_count += 1
    except Exception as exc:
        checks["qdrant"] = {"status": "error", "detail": str(exc)}

    if deep:
        total_checks += 1
        try:
            container.llm_client.generate("health check")
            checks["llm"] = {"status": "ok", "detail": "reachable"}
            ok_count += 1
        except Exception as exc:
            checks["llm"] = {"status": "error", "detail": str(exc)}
    else:
        checks["llm"] = {"status": "skipped", "detail": "set deep=true to probe llm"}

    if ok_count == total_checks:
        status = "healthy"
        code = 200
    elif ok_count >= 1:
        status = "degraded"
        code = 503
    else:
        status = "unhealthy"
        code = 503

    return JSONResponse(status_code=code, content={"status": status, "checks": checks})
