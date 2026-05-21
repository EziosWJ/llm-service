"""应用异常层次结构，映射 HTTP 状态码与错误类型。"""

from __future__ import annotations


class AppError(Exception):
    """应用基础异常，对应 HTTP 500。"""
    status_code: int = 500
    error: str = "internal_error"

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class ValidationError(AppError):
    """请求参数校验失败，对应 HTTP 400。"""
    status_code = 400
    error = "validation_error"


class BusinessError(AppError):
    """业务逻辑错误（如素材不存在），对应 HTTP 422。"""
    status_code = 422
    error = "business_error"


class UpstreamError(Exception):
    """上游 LLM 服务不可用或超时，对应 HTTP 502。注意：不继承 AppError，单独处理。"""

    status_code = 502
    error = "upstream_error"

    def __init__(self, detail: str = "Upstream service failed") -> None:
        super().__init__(detail)
        self.detail = detail
