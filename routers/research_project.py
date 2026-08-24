from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
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


def validate_project_name(name: Optional[str]) -> str:
    if name is not None:
        cleaned = name.strip()
        if not cleaned:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tên đề tài không được để trống hoặc chỉ chứa khoảng trắng",
            )
        return cleaned
    return name


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo đề tài nghiên cứu mới",
    description="Người tạo tự động trở thành OWNER của đề tài.",
)
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    clean_name = validate_project_name(project_in.name)

    existing_project = (
        db.query(ResearchProject)
        .join(ResearchMember, ResearchMember.project_id == ResearchProject.id)
        .filter(
            ResearchMember.user_id == current_user.id,
            ResearchMember.role == "OWNER",
            ResearchProject.name == clean_name,
        )
        .first()
    )
    if existing_project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bạn đã sở hữu một đề tài nghiên cứu có tên này rồi!",
        )

    try:
        new_project = ResearchProject(
            name=clean_name,
            description=(
                project_in.description.strip() if project_in.description else None
            ),
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
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Không thể tạo đề tài: {str(e)}",
        )


@router.get(
    "",
    response_model=List[ProjectResponse],
    summary="Danh sách đề tài của tôi",
    description="Chỉ trả về đề tài mà user hiện tại là owner hoặc member. Hỗ trợ tìm theo tên.",
)
def list_projects(
    # SIẾT CHẶT: max_length chặn client gửi chuỗi search cực dài gây tốn
    # tài nguyên khi build câu lệnh ILIKE không cần thiết.
    search: Optional[str] = Query(
        None, max_length=255, description="Tìm theo tên đề tài"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        db.query(ResearchProject)
        .join(ResearchMember, ResearchMember.project_id == ResearchProject.id)
        .filter(ResearchMember.user_id == current_user.id)
    )

    if search:
        safe_search = search.strip().replace("%", r"\%").replace("_", r"\_")
        if safe_search:
            query = query.filter(ResearchProject.name.ilike(f"%{safe_search}%"))

    return query.all()


def get_member_or_403(db: Session, project_id: int, user_id: int) -> ResearchMember:
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


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Chi tiết đề tài",
    description="Chỉ thành viên (owner hoặc member) của đề tài mới xem được.",
)
def get_project_detail(
    # SIẾT CHẶT: gt=0 chặn project_id <= 0 ngay ở tầng FastAPI (trả 422),
    # không tốn 1 lượt query DB vô ích cho giá trị chắc chắn không tồn tại
    # (id trong DB luôn dương do autoincrement bắt đầu từ 1).
    project_id: int = Path(..., gt=0),
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


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Cập nhật đề tài",
    description="Chỉ OWNER được sửa. Chỉ cập nhật field client thực sự gửi lên.",
)
def update_project(
    project_update: ProjectUpdate,
    project_id: int = Path(..., gt=0),
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
            status_code=status.HTTP_403_FORBIDDEN, detail="Chỉ OWNER được sửa đề tài"
        )

    update_data = project_update.model_dump(exclude_unset=True)

    # SIẾT CHẶT: nếu client PATCH gửi body rỗng {} (không có field nào),
    # không cần chạm DB, trả lỗi rõ ràng thay vì commit() vô nghĩa.
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không có dữ liệu nào để cập nhật",
        )

    if "name" in update_data:
        update_data["name"] = validate_project_name(update_data["name"])

    if "name" in update_data and update_data["name"] != project.name:
        existing_name = (
            db.query(ResearchProject)
            .join(ResearchMember, ResearchProject.id == ResearchMember.project_id)
            .filter(
                ResearchMember.user_id == current_user.id,
                ResearchMember.role == "OWNER",
                ResearchProject.name == update_data["name"],
                ResearchProject.id != project_id,
            )
            .first()
        )
        if existing_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Đã có đề tài khác mang tên này rồi!",
            )

    if "description" in update_data and update_data["description"] is not None:
        cleaned_desc = update_data["description"].strip()
        update_data["description"] = cleaned_desc if cleaned_desc else None

    try:
        for field, value in update_data.items():
            setattr(project, field, value)

        db.commit()
        db.refresh(project)
        return project
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Lỗi cập nhật: {str(e)}"
        )


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa đề tài",
    description="Chỉ OWNER được xóa. Xóa kèm toàn bộ thành viên và nhiệm vụ thuộc đề tài.",
)
def delete_project(
    project_id: int = Path(..., gt=0),
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
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ OWNER được xóa đề tài",
        )

    try:
        from models.research_task import ResearchTask

        db.query(ResearchTask).filter(ResearchTask.project_id == project_id).delete()

        db.query(ResearchMember).filter(
            ResearchMember.project_id == project_id
        ).delete()

        db.delete(project)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Không thể xóa đề tài: {str(e)}",
        )


@router.get(
    "/{project_id}/members",
    response_model=List[MemberResponse],
    summary="Danh sách thành viên đề tài",
    description="Chỉ thành viên của đề tài mới xem được danh sách.",
)
def list_members(
    project_id: int = Path(..., gt=0),
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
    summary="Thêm thành viên vào đề tài",
    description="Chỉ OWNER được thêm. Không cho thêm trùng người đã là thành viên.",
)
def add_member(
    project_id: int = Path(..., gt=0),
    # SIẾT CHẶT: user_id truyền qua query cũng phải > 0
    user_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy đề tài"
        )

    current_member = get_member_or_403(db, project_id, current_user.id)
    if current_member.role != "OWNER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ OWNER được thêm thành viên",
        )

    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bạn không thể tự thêm chính mình vào làm thành viên",
        )

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy User"
        )

    if not target_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tài khoản này đang bị khóa, không thể thêm vào đề tài",
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

    try:
        new_member = ResearchMember(
            project_id=project_id, user_id=user_id, role="MEMBER"
        )
        db.add(new_member)
        db.commit()
        db.refresh(new_member)
        return new_member
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Không thể thêm thành viên: {str(e)}",
        )


@router.delete(
    "/{project_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa thành viên khỏi đề tài",
    description="Chỉ OWNER được xóa. Không cho xóa OWNER cuối cùng của đề tài.",
)
def remove_member(
    project_id: int = Path(..., gt=0),
    user_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy đề tài"
        )

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

    try:
        db.delete(target_member)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Không thể xóa thành viên: {str(e)}",
        )
