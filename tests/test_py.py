from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


TOKEN_TEST = "Bearer YOUR_TOKEN_HERE"
HEADERS = {"Authorization": TOKEN_TEST}


def test_create_task_invalid_priority():
   
    response = client.post(
        "/research-projects/1/research-tasks",
        json={
            "title": "Nhiệm vụ kiểm thử bảo mật",
            "description": "Mô tả chi tiết",
            "status": "TODO",
            "priority": "SUPER_HIGH",  # Cố tình truyền sai chuẩn để test validate
            "assignee_id": 1
        },
        headers=HEADERS
    )
    # Kỳ vọng Pydantic chặn ngay lập tức với mã 422
    assert response.status_code == 422


def test_upload_invalid_file_extension():

    files = {"file": ("script.py", b"print('hack')", "text/x-python")}
    
    response = client.post(
        "/research-projects/1/documents",
        files=files,
        headers=HEADERS
    )
    
    # Kỳ vọng trả về lỗi 400 Bad Request
    assert response.status_code == 400


def test_access_nonexistent_project():
   
    response = client.get(
        "/research-projects/999999/research-tasks",
        headers=HEADERS
    )
    
    # Kỳ vọng bị chặn lại với 403 (không có quyền) hoặc 404 (không tìm thấy)
    assert response.status_code in [403, 404]