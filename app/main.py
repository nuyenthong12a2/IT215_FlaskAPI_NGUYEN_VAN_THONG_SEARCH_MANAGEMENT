from fastapi import FastAPI

from db.database import engine, Base
import models.user
import models.research_project
import models.research_task

from routers import auth, users, research_project, research_task,research_document
from core.exception_handlers import register_exception_handlers

# Tạo bảng trong MySQL nếu chưa tồn tại
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Research Group Management API")

# Đăng ký hệ thống bẫy lỗi tập trung
register_exception_handlers(app)

# Đăng ký các router hiện tại
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(research_project.router)
app.include_router(research_task.router)
app.include_router(research_document.router)


@app.get("/health", tags=["Health Check "])
def healthy_check():
    return {"status": "OK", "code": 200, "message": "API hoạt động bình thường"}