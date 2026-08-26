"""
FILE: test.py
VAI TRÒ: Automated test cho toàn bộ API, chạy từ Tiết 1 đến Tiết 5.

CÁCH CHẠY:
    Đặt file này ở THƯ MỤC GỐC project (ngang hàng với thư mục app/, venv/).
    Kích hoạt venv, rồi chạy:
        pytest test.py -v

LƯU Ý QUAN TRỌNG:
    - Test này gọi THẲNG vào app thật qua TestClient, dùng CHUNG database
      MySQL thật đang cấu hình trong .env - mỗi lần chạy sẽ tạo dữ liệu
      thật (user mới, project mới...). Email test được sinh ngẫu nhiên
      bằng uuid mỗi lần chạy để tránh lỗi trùng email giữa các lần chạy.
    - Các test được viết theo THỨ TỰ TRONG FILE (trên xuống dưới) vì nhiều
      test phụ thuộc dữ liệu tạo ra từ test trước đó (vd cần có project_id
      mới tạo được task) - pytest mặc định chạy test theo đúng thứ tự khai
      báo trong file, không cần cài thêm plugin nào.
"""

import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# "state" dùng để LƯU LẠI dữ liệu tạo ra ở test trước, cho test sau dùng lại
# (vd project_id tạo ở Tiết 3 được Tiết 4 dùng để tạo task bên trong).
state = {}


def unique_email(prefix: str) -> str:
    """Sinh email ngẫu nhiên để tránh lỗi trùng email (400) giữa các lần chạy test."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}@gmail.com"


# ============================================================
# TIẾT 1 — HEALTH CHECK (xác nhận app khởi động và kết nối DB thành công)
# ============================================================

class TestTiet1_KhoiTao:
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "OK"


# ============================================================
# TIẾT 2 — AUTHENTICATION & AUTHORIZATION
# ============================================================

class TestTiet2_Auth:
    def test_01_register_success(self):
        state["user_a_email"] = unique_email("usera")
        response = client.post(
            "/auth/register",
            json={
                "email": state["user_a_email"],
                "full_name": "User A Test",
                "password": "Password123!",
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["email"] == state["user_a_email"]
        assert body["role"] == "USER"
        assert "password_hash" not in body  # đảm bảo không lộ mật khẩu đã hash
        state["user_a_id"] = body["id"]

    def test_02_register_duplicate_email_fails(self):
        response = client.post(
            "/auth/register",
            json={
                "email": state["user_a_email"],  # dùng lại email vừa đăng ký ở trên
                "full_name": "User A Duplicate",
                "password": "Password123!",
            },
        )
        assert response.status_code == 400

    def test_03_register_invalid_email_format(self):
        response = client.post(
            "/auth/register",
            json={
                "email": "khong-phai-email",
                "full_name": "Invalid Email",
                "password": "Password123!",
            },
        )
        assert response.status_code == 422

    def test_04_login_success(self):
        response = client.post(
            "/auth/login",
            data={"username": state["user_a_email"], "password": "Password123!"},
        )
        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        state["user_a_token"] = body["access_token"]
        state["user_a_headers"] = {"Authorization": f"Bearer {body['access_token']}"}

    def test_05_login_wrong_password_fails(self):
        response = client.post(
            "/auth/login",
            data={"username": state["user_a_email"], "password": "SaiMatKhau"},
        )
        assert response.status_code == 401

    def test_06_get_me_with_token(self):
        response = client.get("/users/me", headers=state["user_a_headers"])
        assert response.status_code == 200
        assert response.json()["email"] == state["user_a_email"]

    def test_07_get_me_without_token_fails(self):
        response = client.get("/users/me")
        assert response.status_code == 401

    def test_08_list_users_forbidden_for_normal_user(self):
        # user_a chỉ là role=USER thường, không phải ADMIN -> phải bị chặn 403
        response = client.get("/users", headers=state["user_a_headers"])
        assert response.status_code == 403


# ============================================================
# TIẾT 3 — QUẢN LÝ ĐỀ TÀI NGHIÊN CỨU & THÀNH VIÊN
# ============================================================

class TestTiet3_ResearchProject:
    def test_01_create_project_success(self):
        state["project_name"] = f"Du an test {uuid.uuid4().hex[:6]}"
        response = client.post(
            "/research-projects",
            json={"name": state["project_name"], "description": "Mo ta du an test"},
            headers=state["user_a_headers"],
        )
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == state["project_name"]
        assert body["owner_id"] == state["user_a_id"]
        state["project_id"] = body["id"]

    def test_02_create_duplicate_project_name_fails(self):
        response = client.post(
            "/research-projects",
            json={"name": state["project_name"], "description": "Trung ten"},
            headers=state["user_a_headers"],
        )
        assert response.status_code == 400

    def test_03_create_project_empty_name_fails(self):
        response = client.post(
            "/research-projects",
            json={"name": "   ", "description": "Ten rong"},
            headers=state["user_a_headers"],
        )
        assert response.status_code in (400, 422)

    def test_04_list_projects_contains_created(self):
        response = client.get("/research-projects", headers=state["user_a_headers"])
        assert response.status_code == 200
        ids = [p["id"] for p in response.json()]
        assert state["project_id"] in ids

    def test_05_get_project_detail_success(self):
        response = client.get(
            f"/research-projects/{state['project_id']}", headers=state["user_a_headers"]
        )
        assert response.status_code == 200

    def test_06_get_project_invalid_id_fails(self):
        response = client.get(
            "/research-projects/0", headers=state["user_a_headers"]
        )
        assert response.status_code == 422  # gt=0 chặn ngay ở tầng FastAPI

    def test_07_get_project_not_found(self):
        response = client.get(
            "/research-projects/999999999", headers=state["user_a_headers"]
        )
        assert response.status_code == 404

    def test_08_stranger_cannot_view_project(self):
        # Tạo 1 user hoàn toàn không liên quan tới project
        stranger_email = unique_email("stranger")
        client.post(
            "/auth/register",
            json={"email": stranger_email, "full_name": "Stranger", "password": "Pass123!"},
        )
        login_resp = client.post(
            "/auth/login", data={"username": stranger_email, "password": "Pass123!"}
        )
        stranger_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

        response = client.get(
            f"/research-projects/{state['project_id']}", headers=stranger_headers
        )
        assert response.status_code == 403

    def test_09_update_project_success(self):
        response = client.patch(
            f"/research-projects/{state['project_id']}",
            json={"description": "Mo ta da cap nhat"},
            headers=state["user_a_headers"],
        )
        assert response.status_code == 200
        assert response.json()["description"] == "Mo ta da cap nhat"

    def test_10_update_project_empty_body_fails(self):
        response = client.patch(
            f"/research-projects/{state['project_id']}",
            json={},
            headers=state["user_a_headers"],
        )
        assert response.status_code == 400

    def test_11_add_member_success(self):
        # Tạo user_b để làm thành viên
        state["user_b_email"] = unique_email("userb")
        reg = client.post(
            "/auth/register",
            json={"email": state["user_b_email"], "full_name": "User B", "password": "Pass123!"},
        )
        state["user_b_id"] = reg.json()["id"]
        login_resp = client.post(
            "/auth/login", data={"username": state["user_b_email"], "password": "Pass123!"}
        )
        state["user_b_headers"] = {
            "Authorization": f"Bearer {login_resp.json()['access_token']}"
        }

        response = client.post(
            f"/research-projects/{state['project_id']}/members",
            params={"user_id": state["user_b_id"]},
            headers=state["user_a_headers"],
        )
        assert response.status_code == 201
        assert response.json()["role"] == "MEMBER"

    def test_12_add_duplicate_member_fails(self):
        response = client.post(
            f"/research-projects/{state['project_id']}/members",
            params={"user_id": state["user_b_id"]},
            headers=state["user_a_headers"],
        )
        assert response.status_code == 400

    def test_13_member_can_now_view_project(self):
        response = client.get(
            f"/research-projects/{state['project_id']}", headers=state["user_b_headers"]
        )
        assert response.status_code == 200

    def test_14_non_owner_member_cannot_update_project(self):
        response = client.patch(
            f"/research-projects/{state['project_id']}",
            json={"description": "User B co gang sua"},
            headers=state["user_b_headers"],
        )
        assert response.status_code == 403

    def test_15_cannot_remove_last_owner(self):
        response = client.delete(
            f"/research-projects/{state['project_id']}/members/{state['user_a_id']}",
            headers=state["user_a_headers"],
        )
        assert response.status_code == 400

    def test_16_remove_member_success(self):
        response = client.delete(
            f"/research-projects/{state['project_id']}/members/{state['user_b_id']}",
            headers=state["user_a_headers"],
        )
        assert response.status_code == 204


# ============================================================
# TIẾT 4 — QUẢN TRỊ NHIỆM VỤ NGHIÊN CỨU (TASKS)
# ============================================================

class TestTiet4_ResearchTask:
    def test_01_create_task_success(self):
        response = client.post(
            f"/research-projects/{state['project_id']}/research-tasks",
            json={
                "title": "Nhiem vu test",
                "description": "Mo ta nhiem vu",
                "status": "TODO",
                "priority": "MEDIUM",
            },
            headers=state["user_a_headers"],
        )
        assert response.status_code == 201
        body = response.json()
        assert body["title"] == "Nhiem vu test"
        state["task_id"] = body["id"]

    def test_02_create_task_invalid_priority_fails(self):
        response = client.post(
            f"/research-projects/{state['project_id']}/research-tasks",
            json={
                "title": "Nhiem vu sai priority",
                "priority": "SUPER_HIGH",  # giá trị không hợp lệ, field_validator phải chặn
            },
            headers=state["user_a_headers"],
        )
        assert response.status_code == 422

    def test_03_assign_task_to_non_member_fails(self):
        response = client.post(
            f"/research-projects/{state['project_id']}/research-tasks",
            json={
                "title": "Giao viec cho nguoi ngoai",
                "assignee_id": 999999999,  # id chắc chắn không phải thành viên
            },
            headers=state["user_a_headers"],
        )
        assert response.status_code == 400

    def test_04_list_tasks_contains_created(self):
        response = client.get(
            f"/research-projects/{state['project_id']}/research-tasks",
            headers=state["user_a_headers"],
        )
        assert response.status_code == 200
        ids = [t["id"] for t in response.json()]
        assert state["task_id"] in ids

    def test_05_list_tasks_with_filter(self):
        response = client.get(
            f"/research-projects/{state['project_id']}/research-tasks",
            params={"status": "TODO", "priority": "MEDIUM"},
            headers=state["user_a_headers"],
        )
        assert response.status_code == 200

    def test_06_get_task_detail(self):
        response = client.get(
            f"/research-projects/{state['project_id']}/research-tasks/{state['task_id']}",
            headers=state["user_a_headers"],
        )
        assert response.status_code == 200

    def test_07_update_task_partial_keeps_other_fields(self):
        response = client.patch(
            f"/research-projects/{state['project_id']}/research-tasks/{state['task_id']}",
            json={"status": "DONE"},
            headers=state["user_a_headers"],
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "DONE"
        assert body["title"] == "Nhiem vu test"  # field không gửi phải GIỮ NGUYÊN

    def test_08_update_task_empty_body_fails(self):
        response = client.patch(
            f"/research-projects/{state['project_id']}/research-tasks/{state['task_id']}",
            json={},
            headers=state["user_a_headers"],
        )
        assert response.status_code == 400

    def test_09_delete_task_success(self):
        response = client.delete(
            f"/research-projects/{state['project_id']}/research-tasks/{state['task_id']}",
            headers=state["user_a_headers"],
        )
        assert response.status_code == 204

    def test_10_get_deleted_task_not_found(self):
        response = client.get(
            f"/research-projects/{state['project_id']}/research-tasks/{state['task_id']}",
            headers=state["user_a_headers"],
        )
        assert response.status_code == 404



# TIẾT 5 — KIỂM TRA FORMAT LỖI THỐNG NHẤT & DỌN DẸP DỮ LIỆU TEST


class TestTiet5_ErrorHandlingVaDonDep:
    def test_01_404_error_has_unified_format(self):
        response = client.get(
            "/research-projects/999999999", headers=state["user_a_headers"]
        )
        assert response.status_code == 404
        body = response.json()
        assert body["status"] == "ERROR"
        assert body["code"] == 404
        assert "message" in body

    def test_02_422_error_has_details_field(self):
        response = client.post(
            "/auth/register",
            json={"email": "sai-dinh-dang", "full_name": "X", "password": "123"},
        )
        assert response.status_code == 422
        body = response.json()
        assert body["status"] == "ERROR"
        assert "details" in body

    def test_03_403_error_has_unified_format(self):
        response = client.get("/users", headers=state["user_a_headers"])
        assert response.status_code == 403
        body = response.json()
        assert body["status"] == "ERROR"
        assert body["code"] == 403

    def test_99_cleanup_delete_project(self):
        """Dọn dữ liệu test - xóa project đã tạo để không rác database thật."""
        response = client.delete(
            f"/research-projects/{state['project_id']}", headers=state["user_a_headers"]
        )
        assert response.status_code == 204