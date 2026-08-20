from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException, RequestValidationError

from db.database import engine, get_db, Base
import models.user
import models.research_project
import models.research_task

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Research Group Management API") 


@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "ERROR", "code": exc.status_code, "message": exc.detail},
    )


# Validate dữ liệu đầu vào (default = 422)
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


# Bắt lỗi hệ thống
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "status": "ERROR",
            "code": 500,
            "message": "Lỗi hệ thống, vui lòng thử lại sau",
        },
    )


@app.get("/health", tags=["Core"])
def healthy_check():
    return {"status": "OK", "code": 200, "message": "API hoạt động bình thường "}
