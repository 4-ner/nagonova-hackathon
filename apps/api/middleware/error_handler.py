"""
グローバルエラーハンドリングミドルウェア

全てのHTTP例外と予期しないエラーをキャッチし、適切なJSON形式でレスポンスします。
"""
import logging
import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException, RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    HTTPExceptionハンドラー

    Args:
        request: FastAPIリクエスト
        exc: HTTPException

    Returns:
        JSONResponse: エラーレスポンス
    """
    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail} "
        f"[{request.method} {request.url.path}]"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "path": str(request.url.path),
            }
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    バリデーションエラーハンドラー

    Args:
        request: FastAPIリクエスト
        exc: RequestValidationError

    Returns:
        JSONResponse: エラーレスポンス
    """
    logger.warning(
        f"Validation Error: {exc.errors()} [{request.method} {request.url.path}]"
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "message": "Validation Error",
                "details": exc.errors(),
                "path": str(request.url.path),
            }
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    予期しないエラーハンドラー

    Args:
        request: FastAPIリクエスト
        exc: Exception

    Returns:
        JSONResponse: エラーレスポンス
    """
    # トレースバックをログに出力
    error_trace = traceback.format_exc()
    logger.error(
        f"Unexpected Error: {str(exc)} [{request.method} {request.url.path}]\n{error_trace}"
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal Server Error",
                "path": str(request.url.path),
            }
        },
    )


def register_exception_handlers(app):
    """
    例外ハンドラーをアプリケーションに登録

    Args:
        app: FastAPIアプリケーション
    """
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
