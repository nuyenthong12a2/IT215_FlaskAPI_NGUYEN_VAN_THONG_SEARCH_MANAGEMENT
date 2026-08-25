import os
import uuid
from fastapi import UploadFile, HTTPException

# Danh sách các định dạng file được phép (Siết chặt bảo mật)
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".txt", ".zip", ".doc", ".rar", ".csv"}
UPLOAD_DIR = "uploads/documents"

def save_upload_file(file: UploadFile, project_id: int) -> str:
    """
    """
    # 1. Kiểm tra phần mở rộng của file
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Định dạng file '{ext}' không được phép. Hệ thống chỉ chấp nhận: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 2. Tạo thư mục lưu trữ nếu chưa tồn tại
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # 3. UUID để bảo mật và tránh trùng tên
    unique_filename = f"proj_{project_id}_{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # 4. Ghi file xuống ổ cứng
    try:
        with open(file_path, "wb") as buffer:
            contents = file.file.read()
            buffer.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lưu file trên server: {str(e)}")

    return file_path