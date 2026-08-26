import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

logger = logging.getLogger("app.exception_handlers")
logging.basicConfig(level=logging.INFO)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"status": "ERROR", "code": exc.status_code, "message": exc.detail},
        )

    @app.exception_handler(RequestValidationError)
    def validation_exception_handler(request: Request, exc: RequestValidationError):
        # SỬA LỖI: exc.errors() có thể chứa OBJECT ValueError thật (không phải
        # chuỗi text) trong ctx.error, khi field_validator tự viết raise
        # ValueError("..."). json.dumps() KHÔNG serialize được object Exception
        # trực tiếp -> gây crash 500 dây chuyền. jsonable_encoder() của FastAPI
        # tự biết cách chuyển các object đặc biệt (bao gồm Exception) thành
        # dạng JSON-safe (chuỗi) trước khi đưa vào JSONResponse.
        return JSONResponse(
            status_code=422,
            content=jsonable_encoder(
                {
                    "status": "ERROR",
                    "code": 422,
                    "message": "Dữ liệu đầu vào không hợp lệ",
                    "details": exc.errors(),
                }
            ),
        )

    @app.exception_handler(IntegrityError)
    def integrity_error_handler(request: Request, exc: IntegrityError):
        logger.warning(f"IntegrityError: {str(exc.orig)}")
        return JSONResponse(
            status_code=409,
            content={
                "status": "ERROR",
                "code": 409,
                "message": "Dữ liệu bị xung đột (trùng lặp hoặc vi phạm ràng buộc)",
            },
        )

    @app.exception_handler(SQLAlchemyError)
    def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
        logger.error(f"SQLAlchemyError: {str(exc)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "ERROR",
                "code": 503,
                "message": "Hệ thống cơ sở dữ liệu đang gặp sự cố, vui lòng thử lại sau",
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception on {request.method} {request.url}: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "ERROR",
                "code": 500,
                "message": "Lỗi hệ thống, vui lòng thử lại sau",
            },
        )