
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session

from db.database import get_db
from models.user import User
from models.research_project import ResearchProject, ResearchMember
from models.research_task import ResearchTask
from schemas.research_task import TaskCreate, TaskUpdate, TaskResponse
from dependencies.auth import get_current_user

router = APIRouter( prefix="/research-projects/{project_id}/research-tasks", tags=["Research Tasks"])


def verify_project_membership(db: Session, project_id: int, user_id: int) -> ResearchMember:
    """
    B1: Đề tài có tồn tại hay không  ->404 
    B2: User có phải thành viên/owner->403
    """ 
    # Kiểm sự tồn tại của đề tài    
    project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Không tìm thấy đề tài nghiên cứu")

    member = (db.query(ResearchMember).filter(ResearchMember.project_id == project_id, ResearchMember.user_id == user_id).first())
    # Kiểm tra xem user hiện tại có thuộc đề tài này không 
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền truy cập đề tài này")
    return member


#
# 1. TẠO NHIỆM VỤ NGHIÊN CỨU

@router.post( "",response_model=TaskResponse,status_code=status.HTTP_201_CREATED,summary="Tạo nhiệm vụ nghiên cứu mới")
def create_task(task_in: TaskCreate, project_id: int = Path(..., gt=0),db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    # Xác thực user phải thuộc đề tài mới được tạo task 
    verify_project_membership(db, project_id, current_user.id)
    # Phân công việc phải là thành viên trong đề tài 
    if task_in.assignee_id:
        assignee_member = (db.query(ResearchMember).filter(ResearchMember.project_id == project_id,ResearchMember.user_id == task_in.assignee_id).first())
        if not assignee_member:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Người được giao việc (assignee) phải là thành viên của đề tài này" )

    new_task = ResearchTask(project_id=project_id,title=task_in.title.strip(),description=task_in.description.strip() if task_in.description else None,status=task_in.status,priority=task_in.priority,assignee_id=task_in.assignee_id)
    
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

# 2. DANH SÁCH NHIỆM VỤ (Lọc, Tìm kiếm, Phân trang & Sắp xếp)

@router.get( "", response_model=List[TaskResponse], summary="Danh sách nhiệm vụ của đề tài")
def list_tasks(project_id: int = Path(..., gt=0),status_filter: Optional[str] = Query(None, alias="status", description="Lọc theo trạng thái: TODO, IN_PROGRESS, DONE"),priority_filter: Optional[str] = Query(None, alias="priority", description="Lọc theo độ ưu tiên: LOW, MEDIUM, HIGH" ), assignee_id: Optional[int] = Query(None, description="Lọc theo ID người thực hiện"), search: Optional[str] = Query(None, max_length=255, description="Tìm kiếm theo tiêu đề task"),skip: int = Query(0, ge=0, description="Số lượng bản ghi bỏ qua (offset)"),limit: int = Query(10, ge=1, le=100, description="Số lượng bản ghi tối đa (limit)"),sort_by: str = Query("created_at", description="Sắp xếp theo trường: created_at hoặc due_date"),order: str = Query("desc", description="Thứ tự sắp xếp: asc hoặc desc"),db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    # Xác thực quyền xem danh sách task của đề tài
    verify_project_membership(db, project_id, current_user.id)

    query = db.query(ResearchTask).filter(ResearchTask.project_id == project_id)
# Lọc theo trạng thái task
    if status_filter:
        query = query.filter(ResearchTask.status == status_filter)
# Lọc theo mức độ ưu tiên 
    if priority_filter:
        query = query.filter(ResearchTask.priority == priority_filter)
# Lọc theo người thực hiện 
    if assignee_id:
        query = query.filter(ResearchTask.assignee_id == assignee_id)
# Tìm kiếm gần đúng theo tiêu đề task 
    if search:
        safe_search = search.strip().replace("%", r"\%").replace("_", r"\_")
        query = query.filter(ResearchTask.title.ilike(f"%{safe_search}%"))

    sort_column = ResearchTask.created_at
    if sort_by == "due_date" and hasattr(ResearchTask, "due_date"):
        sort_column = ResearchTask.due_date
# Sắp xếp tăng/giảm dần theo cột chỉ định 
    if order.lower() == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    return query.offset(skip).limit(limit).all()



# 3. CHI TIẾT NHIỆM VỤ

@router.get("/{task_id}", response_model=TaskResponse, summary="Chi tiết nhiệm vụ nghiên cứu")
def get_task_detail(project_id: int = Path(..., gt=0),task_id: int = Path(..., gt=0),db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    verify_project_membership(db, project_id, current_user.id)

    task = (db.query(ResearchTask).filter(ResearchTask.id == task_id, ResearchTask.project_id == project_id).first())
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Không tìm thấy nhiệm vụ nghiên cứu",)
    return task


# 4. CẬP NHẬT NHIỆM VỤ

@router.patch("/{task_id}", response_model=TaskResponse, summary="Cập nhật nhiệm vụ nghiên cứu")
def update_task(task_update: TaskUpdate,project_id: int = Path(..., gt=0),task_id: int = Path(..., gt=0),db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    # Xác thực quyền thành viên 
    verify_project_membership(db, project_id, current_user.id)

    task = (db.query(ResearchTask).filter(ResearchTask.id == task_id, ResearchTask.project_id == project_id).first())
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Không tìm thấy nhiệm vụ nghiên cứu")
# Chỉ lấy các trường dữ liệu thực sự cần cập nhật
    update_data = task_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không có dữ liệu nào để cập nhật",
        )

    if "assignee_id" in update_data and update_data["assignee_id"] is not None:
        assignee_member = ( db.query(ResearchMember) .filter( ResearchMember.project_id == project_id, ResearchMember.user_id == update_data["assignee_id"], ) .first()
        )
        # Kiểm tra người mới được gán việc có thuộc đề tài không
        if not assignee_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Người được giao việc mới phải là thành viên của đề tài",
            )

    for field, value in update_data.items():
        setattr(task, field, value) # Cập nhật các trường dữ liệu dữ liệu thay đổi 

    db.commit()
    db.refresh(task)
    return task



# 5. XÓA NHIỆM VỤ

@router.delete("/{task_id}",status_code=status.HTTP_204_NO_CONTENT,summary="Xóa nhiệm vụ nghiên cứu")
def delete_task(
    project_id: int = Path(..., gt=0),
    task_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Xác thực quyền thành viên 
    verify_project_membership(db, project_id, current_user.id)

    task = (db.query(ResearchTask).filter(ResearchTask.id == task_id, ResearchTask.project_id == project_id).first())
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy nhiệm vụ nghiên cứu")
# Thực hiện xóa task khỏi cơ sở dữ liệu liệu
    db.delete(task)
    db.commit()