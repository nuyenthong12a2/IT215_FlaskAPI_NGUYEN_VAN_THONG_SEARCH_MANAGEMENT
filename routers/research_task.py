"""
FILE: routers/research_task.py
VAI TRÒ: Quản lý Nhiệm vụ nghiên cứu (Research Tasks) có đầy đủ Lọc, Tìm kiếm, Phân trang & Sắp xếp.
"""

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
    prefix="/research-projects/{project_id}/research-tasks", tags=["Research Tasks"]
)


def verify_project_membership(
    db: Session, project_id: int, user_id: int
) -> ResearchMember:
    project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy đề tài nghiên cứu",
        )

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
            detail="Bạn không có quyền truy cập đề tài này",
        )
    return member


# ============================================================
# 1. TẠO NHIỆM VỤ NGHIÊN CỨU
# ============================================================
@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo nhiệm vụ nghiên cứu mới",
)
def create_task(
    project_id: int = Path(..., gt=0),
    task_in: TaskCreate = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_project_membership(db, project_id, current_user.id)

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
                detail="Người được giao việc (assignee) phải là thành viên của đề tài này",
            )

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


# ============================================================
# 2. DANH SÁCH NHIỆM VỤ (Hỗ trợ Lọc, Tìm kiếm, Phân trang & Sắp xếp)
# ============================================================
@router.get(
    "", response_model=List[TaskResponse], summary="Danh sách nhiệm vụ của đề tài"
)
def list_tasks(
    project_id: int = Path(..., gt=0),
    status_filter: Optional[str] = Query(
        None, alias="status", description="Lọc theo trạng thái: TODO, IN_PROGRESS, DONE"
    ),
    priority_filter: Optional[str] = Query(
        None, alias="priority", description="Lọc theo độ ưu tiên: LOW, MEDIUM, HIGH"
    ),
    assignee_id: Optional[int] = Query(None, description="Lọc theo ID người thực hiện"),
    search: Optional[str] = Query(
        None, max_length=255, description="Tìm kiếm theo tiêu đề task"
    ),
    # CÁC THAM SỐ PHÂN TRANG VÀ SẮP XẾP BẮT BUỘC PHẢI CÓ ĐÂY:
    skip: int = Query(0, ge=0, description="Số lượng bản ghi bỏ qua (offset)"),
    limit: int = Query(10, ge=1, le=100, description="Số lượng bản ghi tối đa (limit)"),
    sort_by: str = Query(
        "created_at", description="Sắp xếp theo trường: created_at hoặc due_date"
    ),
    order: str = Query("desc", description="Thứ tự sắp xếp: asc hoặc desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_project_membership(db, project_id, current_user.id)

    query = db.query(ResearchTask).filter(ResearchTask.project_id == project_id)

    # 1. Lọc và Tìm kiếm
    if status_filter:
        query = query.filter(ResearchTask.status == status_filter)
    if priority_filter:
        query = query.filter(ResearchTask.priority == priority_filter)
    if assignee_id:
        query = query.filter(ResearchTask.assignee_id == assignee_id)
    if search:
        safe_search = search.strip().replace("%", r"\%").replace("_", r"\_")
        query = query.filter(ResearchTask.title.ilike(f"%{safe_search}%"))

    # 2. Sắp xếp
    sort_column = ResearchTask.created_at
    if sort_by == "due_date" and hasattr(ResearchTask, "due_date"):
        sort_column = ResearchTask.due_date

    if order.lower() == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # 3. Phân trang
    return query.offset(skip).limit(limit).all()


# ============================================================
# 3. CHI TIẾT NHIỆM VỤ
# ============================================================
@router.get(
    "/{task_id}", response_model=TaskResponse, summary="Chi tiết nhiệm vụ nghiên cứu"
)
def get_task_detail(
    project_id: int = Path(..., gt=0),
    task_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_project_membership(db, project_id, current_user.id)

    task = (
        db.query(ResearchTask)
        .filter(ResearchTask.id == task_id, ResearchTask.project_id == project_id)
        .first()
    )
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy nhiệm vụ nghiên cứu",
        )
    return task


# ============================================================
# 4. CẬP NHẬT NHIỆM VỤ
# ============================================================
@router.patch(
    "/{task_id}", response_model=TaskResponse, summary="Cập nhật nhiệm vụ nghiên cứu"
)
def update_task(
    task_update: TaskUpdate,
    project_id: int = Path(..., gt=0),
    task_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_project_membership(db, project_id, current_user.id)

    task = (
        db.query(ResearchTask)
        .filter(ResearchTask.id == task_id, ResearchTask.project_id == project_id)
        .first()
    )
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy nhiệm vụ nghiên cứu",
        )

    update_data = task_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không có dữ liệu nào để cập nhật",
        )

    if "assignee_id" in update_data and update_data["assignee_id"] is not None:
        assignee_member = (
            db.query(ResearchMember)
            .filter(
                ResearchMember.project_id == project_id,
                ResearchMember.user_id == update_data["assignee_id"],
            )
            .first()
        )
        if not assignee_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Người được giao việc mới phải là thành viên của đề tài",
            )

    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


# ============================================================
# 5. XÓA NHIỆM VỤ
# ============================================================
@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa nhiệm vụ nghiên cứu",
)
def delete_task(
    project_id: int = Path(..., gt=0),
    task_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_project_membership(db, project_id, current_user.id)

    task = (
        db.query(ResearchTask)
        .filter(ResearchTask.id == task_id, ResearchTask.project_id == project_id)
        .first()
    )
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy nhiệm vụ nghiên cứu",
        )

    db.delete(task)
    db.commit()
