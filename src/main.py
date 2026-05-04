from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.generate import router as generate_router
from src.api.health import router as health_router
from src.api.materials import router as materials_router
from src.bootstrap import get_container
from src.models.errors import AppError, BusinessError, UpstreamError, ValidationError
from src.models.responses import ErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    container = get_container()
    container.qdrant_store.ensure_collection()
    yield


app = FastAPI(title="llm-service", lifespan=lifespan)
app.include_router(materials_router)
app.include_router(generate_router)
app.include_router(health_router)


def _err(status_code: int, error: str, detail: str) -> JSONResponse:
    payload = ErrorResponse(error=error, detail=detail).model_dump()
    return JSONResponse(status_code=status_code, content=payload)


@app.exception_handler(ValidationError)
async def handle_validation_error(_: Request, exc: ValidationError) -> JSONResponse:
    return _err(400, "validation_error", exc.detail)


@app.exception_handler(BusinessError)
async def handle_business_error(_: Request, exc: BusinessError) -> JSONResponse:
    return _err(422, "business_error", exc.detail)


@app.exception_handler(UpstreamError)
async def handle_upstream_error(_: Request, exc: UpstreamError) -> JSONResponse:
    return _err(502, "upstream_error", exc.detail)


@app.exception_handler(AppError)
async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
    return _err(exc.status_code, exc.error, exc.detail)


@app.exception_handler(RequestValidationError)
async def handle_request_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
    return _err(400, "validation_error", str(exc))


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "llm-service", "status": "ok"}
