from fastapi import FastAPI

from db.database import engine, Base
import models.user
import models.research_project
import models.research_task
import models.research_document

from routers import auth, users, research_project, research_task, research_document
from core.exception_handlers import register_exception_handlers

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Research Group Management API")

register_exception_handlers(app)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(research_project.router)
app.include_router(research_task.router)
app.include_router(research_document.router)


@app.get("/health", tags=["Core"])
def healthy_check():
    return {"status": "OK", "code": 200, "message": "API hoạt động bình thường"}