"""统一错误处理中间件 — 确保所有 API 错误响应格式一致。"""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


async def unified_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """全局异常处理：将 HTTPException 和未捕获异常统一为 JSON 格式。

    注意：此 handler 仅作为兜底，不替代各路由中显式抛出的 HTTPException。
    """
    if isinstance(exc, StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.status_code,
                    "message": exc.detail,
                }
            },
        )
    # 未捕获异常 → 500（不暴露内部细节到生产环境）
    is_debug = (
        getattr(request.app, "debug", None)
        or getattr(request.app.state, "debug", None)
    )
    detail = str(exc) if is_debug else "Internal server error"
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": detail,
            }
        },
    )
