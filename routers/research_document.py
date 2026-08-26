
import os
import uuid
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Path
from sqlalchemy.orm import Session

from db.database import get_db
from models.user import User
from models.research_project import ResearchProject, ResearchMember
from models.research_document import ResearchDocument
from schemas.research_document import DocumentResponse
from dependencies.auth import get_current_user

router = APIRouter(prefix="/research-projects/{project_id}/documents", tags=["Research Documents"])

UPLOAD_DIR = "uploads/documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# STEP1: Chỉ cho phép các định dạng tài liệu học tập/nghiên cứu thực sự cần thiết
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".xlsx", ".csv", ".zip", ".rar"}

# SIẾT CHẶT 2: Giới hạn dung lượng tối đa mỗi file là 5MB 
MAX_FILE_SIZE = 5 * 1024 * 1024  


def verify_project_membership(db: Session, project_id: int, user_id: int) -> ResearchMember:
    project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy đề tài nghiên cứu")
    
    member = db.query(ResearchMember).filter(
        ResearchMember.project_id == project_id, 
        ResearchMember.user_id == user_id
    ).first()
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền truy cập đề tài này")
    return member


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED, summary="Upload tài liệu ")
async def upload_document(
    project_id: int = Path(..., gt=0),
    file: UploadFile = File(..., description="File tài liệu cần upload"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_project_membership(db, project_id, current_user.id)

    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tên file không hợp lệ")

    # SIẾT CHẶT 3: Kiểm tra phần mở rộng file 
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Định dạng file '{ext}' không được phép. Hệ thống chỉ chấp nhận: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # SIẾT CHẶT 4: Kiểm tra dung lượng thực tế của file trước khi lưu
    file_content = await file.read()
    file_size = len(file_content)

    if file_size == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tệp tin tải lên bị rỗng")
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dung lượng file vượt quá giới hạn cho phép (Tối đa 5MB). File của bạn: {round(file_size / (1024*1024), 2)}MB"
        )

    #  Tránh xung đột, trùng lặp ghi đè
    unique_filename = f"proj_{project_id}_{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # Ghi file vật lý an toàn
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Không thể lưu trữ tệp tin lên server")

    # Lưu thông tin
    new_doc = ResearchDocument(
        project_id=project_id,
        file_name=file.filename,  
        file_path=file_path,     
        uploaded_by=current_user.id,
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    return new_doc


@router.get("", response_model=List[DocumentResponse], summary="Danh sách tài liệu của đề tài")
def list_documents(
    project_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_project_membership(db, project_id, current_user.id)
    return db.query(ResearchDocument).filter(ResearchDocument.project_id == project_id).all()


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Xóa tài liệu an toàn")
def delete_document(
    project_id: int = Path(..., gt=0),
    document_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_project_membership(db, project_id, current_user.id)

    doc = db.query(ResearchDocument).filter(
        ResearchDocument.id == document_id,
        ResearchDocument.project_id == project_id
    ).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tài liệu")

    # SIẾT CHẶT 5: Phân quyền xóa (Chỉ Chủ đề tài OWNER hoặc Chính người upload mới được quyền xóa)
    project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
    if project.owner_id != current_user.id and doc.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Bạn không có quyền xóa tài liệu này (Chỉ Owner đề tài hoặc Người tải lên mới được xóa)"
        )

    # Xóa file vật lý trên ổ đĩa để giải phóng bộ nhớ
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass

    db.delete(doc)
    db.commit()