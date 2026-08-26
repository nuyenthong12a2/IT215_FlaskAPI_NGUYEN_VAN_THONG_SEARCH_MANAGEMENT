

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy import func
from sqlalchemy.orm import Session

from db.database import get_db
from models.user import User
from models.research_project import ResearchProject, ResearchMember
from models.research_task import ResearchTask
from schemas.research_project import (ProjectCreate,ProjectUpdate, ProjectResponse,MemberResponse)
from dependencies.auth import get_current_user

router = APIRouter(prefix="/research-projects", tags=["Research Projects"])





def validate_project_name(name: Optional[str]) -> str:
    """Chuẩn hóa và chặn tên rỗng hoặc chỉ chứa khoảng trắng."""
    if name is not None:
        cleaned = name.strip()
        if not cleaned:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tên đề tài không được để trống hoặc chỉ chứa khoảng trắng",
            )
        return cleaned
    return name


def verify_project_membership(db: Session, project_id: int, user_id: int, require_owner: bool = False) -> ResearchMember:
    """
    1. Đề tài có tồn tại không? (Nếu không -> 404 Not Found)
    2. User có phải thành viên/owner không? (Nếu không -> 403 Authorization)
    """
    project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy đề tài")

    member = (db.query(ResearchMember).filter(ResearchMember.project_id == project_id, ResearchMember.user_id == user_id).first())
# Kiểm tra xem user hiện tại có thuộc đề tài này không 
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không thuộc về đề tài này",
        )

    if require_owner and member.role != "OWNER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ OWNER mới có quyền thực hiện hành động này",
        )

    return member





@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project( project_in: ProjectCreate,db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    # Làm sạch và kiểm tra tên đề tài hợp lệ
    clean_name = validate_project_name(project_in.name)

    existing_project = (db.query(ResearchProject).join(ResearchMember, ResearchMember.project_id == ResearchProject.id).filter(ResearchMember.user_id == current_user.id,ResearchMember.role == "OWNER",func.lower(ResearchProject.name) == clean_name.lower()).first()
    )
    # Kiểm tra đề tài có tồn tại 
    if existing_project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bạn đã sở hữu một đề tài nghiên cứu có tên này rồi!",
        )

    new_project = ResearchProject(
        name=clean_name,
        description=project_in.description.strip() if project_in.description else None,
        owner_id=current_user.id,
    )
    db.add(new_project)
    db.flush() # flush để id của project vừa tạo trước commit 

    owner_member = ResearchMember(project_id=new_project.id,user_id=current_user.id,role="OWNER")
    # Tự động thêm người tạo thành viên với vai trò owner 
    db.add(owner_member)
    db.commit()
    db.refresh(new_project)
    return new_project


@router.get("", response_model=List[ProjectResponse])
# Lấy danh sách các đề tài mà user hiện tại đang là thành viên 
def list_projects(search: Optional[str] = Query(None, max_length=255),db: Session = Depends(get_db),current_user: User = Depends(get_current_user),):
    query = ( db.query(ResearchProject).join(ResearchMember, ResearchMember.project_id == ResearchProject.id).filter(ResearchMember.user_id == current_user.id))

    if search:
        safe_search = search.strip().replace("%", r"\%").replace("_", r"\_")
        if safe_search:
            query = query.filter(ResearchProject.name.ilike(f"%{safe_search}%"))

    return query.all()


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project_detail(project_id: int = Path(..., gt=0),db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
# Kiểm tra quyền xem đề tài (phải tồn tại và là thành viên)
    verify_project_membership(db, project_id, current_user.id)
    return db.query(ResearchProject).filter(ResearchProject.id == project_id).first()


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(project_update: ProjectUpdate,project_id: int = Path(..., gt=0), db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    # Chỉ owner mới được phép cập nhật đề tài 
    verify_project_membership(db, project_id, current_user.id, require_owner=True)
    project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()

    update_data = project_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="Không có dữ liệu nào để cập nhật")

    if "name" in update_data:
        update_data["name"] = validate_project_name(update_data["name"])

    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int = Path(..., gt=0),db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    # Chỉ owner mới có quyền xóa đê tài 
    verify_project_membership(db, project_id, current_user.id, require_owner=True) 

    project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
    db.query(ResearchTask).filter(ResearchTask.project_id == project_id).delete()
    db.query(ResearchMember).filter(ResearchMember.project_id == project_id).delete()
    db.delete(project) # xóa chính đề tài đó 
    db.commit()


@router.get("/{project_id}/members", response_model=List[MemberResponse])
def list_members(project_id: int = Path(..., gt=0),db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    # Thành viên của project mới xem được ds 
    verify_project_membership(db, project_id, current_user.id)
    return (
        db.query(ResearchMember).filter(ResearchMember.project_id == project_id).all()
    )


@router.post("/{project_id}/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED,summary="Thêm thành viên mới vào đề tài")
def add_member(project_id: int = Path(..., gt=0),user_id: int = Query(..., gt=0),db: Session = Depends(get_db),current_user: User = Depends(get_current_user),
):
    # Chỉ owner mới có quyền thêm thành viên mới 
    verify_project_membership(db, project_id, current_user.id, require_owner=True)
# Kiểm tra xem user được thêm có tồn tại và đang hoạt động không 
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Bạn không thể tự thêm chính mình")
   
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user or not target_user.is_active:
        raise HTTPException(
            status_code=400, detail="User không tồn tại hoặc đang bị khóa"
        )

    existing = (
        db.query(ResearchMember)
        .filter_by(project_id=project_id, user_id=user_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="User đã là thành viên")

    new_member = ResearchMember(project_id=project_id, user_id=user_id, role="MEMBER")
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return new_member


@router.delete(
    "/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_member( project_id: int = Path(..., gt=0), user_id: int = Path(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user),):
    verify_project_membership(db, project_id, current_user.id, require_owner=True)

    target_member = (db.query(ResearchMember).filter_by(project_id=project_id, user_id=user_id).first())
    if not target_member:
        raise HTTPException(status_code=404, detail="Thành viên không tồn tại")

    if target_member.role == "OWNER":
        owner_count = (
            db.query(ResearchMember)
            .filter_by(project_id=project_id, role="OWNER")
            .count()
        )
        if owner_count <= 1:
            raise HTTPException(status_code=400, detail="Không thể xóa OWNER cuối cùng")

    db.delete(target_member)
    db.commit()