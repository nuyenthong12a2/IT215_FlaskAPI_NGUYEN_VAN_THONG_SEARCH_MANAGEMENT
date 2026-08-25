import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# Cấu hình logger riêng cho module này - ghi log ra console (hoặc file nếu cần)
# để dev xem được lỗi THẬT trong lúc chạy, mà KHÔNG lộ chi tiết đó cho client.
logger = logging.getLogger("app.exception_handlers")
logging.basicConfig(level=logging.INFO)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Đăng ký toàn bộ exception handler cho app, phân theo TỪNG TẦNG LỖI
    từ cụ thể đến chung chung (thứ tự này không ảnh hưởng runtime vì
    FastAPI tự chọn handler khớp đúng nhất với loại Exception, nhưng
    sắp xếp theo tầng giúp code dễ đọc và bảo trì hơn):

    1. HTTPException      - lỗi nghiệp vụ CHỦ ĐỘNG raise (400/401/403/404...)
    2. RequestValidationError - lỗi Pydantic tự sinh khi request sai kiểu dữ liệu
    3. IntegrityError / SQLAlchemyError - lỗi Ở TẦNG DATABASE (vi phạm ràng buộc
       UNIQUE/FK mà tầng ứng dụng lỡ chưa check trước, hoặc lỗi kết nối DB)
    4. Exception (global)  - lưới hứng bọ cuối cùng cho MỌI lỗi không lường trước
    """

    @app.exception_handler(HTTPException)
    def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"status": "ERROR", "code": exc.status_code, "message": exc.detail},
        )

    @app.exception_handler(RequestValidationError)
    def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "status": "ERROR",
                "code": 422,
                "message": "Dữ liệu đầu vào không hợp lệ",
                "details": exc.errors(),
            },
        )

    # SIẾT CHẶT: bắt riêng lỗi vi phạm ràng buộc DB (vd 2 request cùng lúc
    # insert trùng email do race condition, lọt qua check ở tầng ứng dụng).
    # Đặt riêng để trả 409 Conflict (đúng ngữ nghĩa REST cho xung đột dữ liệu)
    # thay vì rơi vào 500 chung chung của global handler.
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

    # SIẾT CHẶT: bắt các lỗi SQLAlchemy khác (mất kết nối DB, timeout...)
    # KHÔNG phải IntegrityError - đặt sau IntegrityError vì IntegrityError
    # là con của SQLAlchemyError, FastAPI ưu tiên handler khớp cụ thể hơn trước.
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

    # SIẾT CHẶT: log đầy đủ traceback lỗi thật (exc_info=True) trước khi
    # trả về message chung chung cho client - giúp debug mà không lộ
    # chi tiết nội bộ (stack trace, tên bảng, tên biến...) ra ngoài.
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