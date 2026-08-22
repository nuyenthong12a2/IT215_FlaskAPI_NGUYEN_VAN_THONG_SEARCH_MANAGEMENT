from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from db.database import get_db
from models.user import User
from models.research_project import ResearchProject, ResearchMember
from schemas.research_project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    MemberResponse,
)
from dependencies.auth import get_current_user

router = APIRouter(prefix="/research-projects", tags=["Research Projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tạo project mới, người tạo tự động trở thành owner."""
    new_project = ResearchProject(
        name=project_in.name,
        description=project_in.description,
        owner_id=current_user.id,
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    owner_member = ResearchMember(
        project_id=new_project.id,
        user_id=current_user.id,
        role="OWNER",
    )
    db.add(owner_member)
    db.commit()

    return new_project


@router.get("", response_model=List[ProjectResponse])
def list_projects(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Chỉ trả project mà user hiện tại là owner/member."""
    query = (
        db.query(ResearchProject)
        .join(ResearchMember, ResearchMember.project_id == ResearchProject.id)
        .filter(ResearchMember.user_id == current_user.id)
    )
    if search:
        query = query.filter(ResearchProject.name.ilike(f"%{search}%"))
    return query.all()


def get_member_or_403(db: Session, project_id: int, user_id: int) -> ResearchMember:
    """Hàm dùng chung: lấy dòng ResearchMember, raise 403 nếu không phải thành viên."""
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
            detail="Bạn không thuộc về đề tài này",
        )
    return member


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project_detail(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy đề tài"
        )

    get_member_or_403(db, project_id, current_user.id)
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy đề tài"
        )

    member = get_member_or_403(db, project_id, current_user.id)
    # SỬA: phải là "!=" - chặn người KHÔNG PHẢI OWNER, không phải chặn OWNER
    if member.role != "OWNER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Chỉ OWNER được sửa đề tài"
        )

    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy đề tài"
        )

    member = get_member_or_403(db, project_id, current_user.id)
    if member.role != "OWNER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Chỉ OWNER được xóa đề tài"
        )

    db.delete(project)
    db.commit()


@router.get("/{project_id}/members", response_model=List[MemberResponse])
def list_members(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_member_or_403(db, project_id, current_user.id)
    return (
        db.query(ResearchMember).filter(ResearchMember.project_id == project_id).all()
    )


@router.post(
    "/{project_id}/members",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_member(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_member = get_member_or_403(db, project_id, current_user.id)
    if current_member.role != "OWNER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ OWNER được thêm thành viên",
        )

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy User"
        )

    existing = (
        db.query(ResearchMember)
        .filter(
            ResearchMember.project_id == project_id, ResearchMember.user_id == user_id
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User đã là thành viên"
        )

    new_member = ResearchMember(project_id=project_id, user_id=user_id, role="MEMBER")
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return new_member


@router.delete(
    "/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_member(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_member = get_member_or_403(db, project_id, current_user.id)
    if current_member.role != "OWNER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ OWNER được phép xóa thành viên",
        )

    target_member = (
        db.query(ResearchMember)
        .filter(
            ResearchMember.project_id == project_id, ResearchMember.user_id == user_id
        )
        .first()
    )
    if not target_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Thành viên không tồn tại"
        )

    if target_member.role == "OWNER":
        owner_count = (
            db.query(ResearchMember)
            .filter(
                ResearchMember.project_id == project_id, ResearchMember.role == "OWNER"
            )
            .count()
        )
        if owner_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể xóa OWNER cuối cùng của đề tài",
            )

    db.delete(target_member)
    db.commit()
