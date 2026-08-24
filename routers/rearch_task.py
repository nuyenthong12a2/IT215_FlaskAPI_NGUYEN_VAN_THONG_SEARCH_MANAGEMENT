from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from db.database import get_db
from models.user import User
from models.research_project import ResearchProject, ResearchMember
from models.research_task import ResearchTask
from schemas.research_task import TaskCreate, TaskUpdate, TaskResponse
from dependencies.auth import get_current_user

router = APIRouter(
    prefix="/research-projects{project_id}/research-tasks", tags=["Research Tasks"]
)


def verify_project_member(db: Session, project_id: int, user_id: int) -> ResearchMember:
    """Kiểm tra xem user có thuộc đề tài này không"""
    member = (
        db.query(ResearchMember)
        .filter(
            ResearchMember.project_id == project_id, ResearchMember.user_id == user_id
        )
        .first()
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Bạn không có quyền truy cập vào đề tài này",
        )
    return member


router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo nhiệm vụ nghiên cứu mới",
)


def create_task(
    project_id: int = Path(..., gt=0),
    task_in: TaskCreate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Kiểm tra đề tài tồn tại
    project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy đề tài"
        )

    # Kiểm tra quyền thành viên
    verify_project_member(db, project_id, current_user.id)

    # Nếu có gán assignee_id, kiểm tra xem user đó có thuộc đề tài không
    if task_in.assignee_id:
        assignee_member = (
            db.query(ResearchMember)
            .filter(
                ResearchMember.project_id == project_id,
                ResearchMember.user_id == task_in.assignee_id,
            )
            .first()
        )
        if not assignee_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Người được giao việc phải là thành viên của đề tài",
            )

    try:
        new_task = ResearchTask(
            project_id=project_id,
            title=task_in.title.strip(),
            description=task_in.description.strip() if task_in.description else None,
            status=task_in.status,
            priority=task_in.priority,
            assignee_id=task_in.assignee_id,
        )
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        return new_task
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Không thể tạo task: {str(e)}",
        )


@router.get(
    "", response_model=List[TaskResponse], summary="Danh sách nhiệm vụ của đề tài"
)
def list_tasks(
    project_id: int = Path(..., gt=0),
    status_filter: Optional[str] = Query(None, alias="status"),
    priority_filter: Optional[str] = Query(None, alias="priority"),
    assignee_id: Optional[int] = Query(None, gt=0),
    search: Optional[str] = Query(None, max_length=255),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_project_member(db, project_id, current_user.id)

    query = db.query(ResearchTask).filter(ResearchTask.project_id == project_id)

    if status_filter:
        query = query.filter(ResearchTask.status == status_filter)
    if priority_filter:
        query = query.filter(ResearchTask.priority == priority_filter)
    if assignee_id:
        query = query.filter(ResearchTask.assignee_id == assignee_id)
    if search:
        safe_search = search.strip().replace("%", r"\%").replace("_", r"\_")
        query = query.filter(ResearchTask.title.ilike(f"%{safe_search}%"))

    return query.all()


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa nhiệm vụ nghiên cứu",
)
def delete_task(
    project_id: int = Path(..., gt=0),
    task_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_project_member(db, project_id, current_user.id)

    task = (
        db.query(ResearchTask)
        .filter(ResearchTask.id == task_id, ResearchTask.project_id == project_id)
        .first()
    )

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy nhiệm vụ"
        )

    try:
        db.delete(task)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Không thể xóa task: {str(e)}",
        )
