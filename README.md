Research Group Management System 
API quản lý nhóm nghiên cứu : đề tài, thành viên, nhiệm vụ nghiên cứu -> Xây dựng bằng FastAPI + MySQL 

I. Cài đặt 

B1 : Tạo môi trường ảo 
py -m venv venv 
B2: Kích hoạt môi trường ảo 
.\venv\Scripts\Activate 
B3: Cài đặt các thư viện cần thiết 
pip install -r requirement.txt 

B4. Tạo file.en từ .env.example,cập nhật DATABASE_URL , SECRET_KEY 

B5: Tạo DATABASE TỪ MYSQL 
CREATE TABLE research_db;

II. Chạy Project 
uvicorn app.main:app --reload 

III. Seed dữ liệu mẫu 
py -m app.seed 

IV. Tài khoản mẫu khi seed : 
Vai trò	           Email      	             Mật khẩu
Admin	       admin@gmail.com  	            Admin@123
User (owner)	gv_lead@gmail.com	    123456
User (member)	sinhvien@gmail.com	    123456

V. Cấu trúc thư mục 
research_management/
├── app/
│   ├── main.py
│   ├── core/         # config, security
│   ├── db/           # database, session
│   ├── models/        # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   ├── routers/        # API endpoints
│   ├── services/        # Business logic
│   ├── dependencies/     # get_current_user, permissions
│   └── utils/
├── tests/
├── .env.example
├── requirements.txt
└── README.md

VI. Công nghệ sử dụng 
FastAPI,SQLAlchemy,Pydantic v2 
MySQL + PyMySQL 
JWT (python-jose),passlib/bcrypt 

VII. Tính năng chính 
+Authentication:register/login,JWT 
+Quản lý đề tài nghiên cứu + thành viên(phân quyền Owner,Member)
+ Quản lý nhiệm vụ nghiên cứu : CRUD, giao việc,filter/search/pagination
+Exception handling & response thống nhất 

VIII. Nhật ký tiến độ (Progress Log)

Buổi 1 : Khởi tạo dự án & Database 
Ngày bắt đầu : 20/8/2026 
Giờ : 12:10 (AM)
Ngày kết thúc : 20/8/2026
Giờ :18:30(PM)
Đã hoàn thành : 
+ Cấu trúc thư mục theo module (routers/models/schemas/services/dependencies/core/db)
+ Cấu hình .env/.env.example, đọc config qua core/config.py 
+ Kết nối MySQL :engine,SessionLocal,get_db 
+ Model : User,ResearchProject,ResearchMember,ResearchTask 
+ Pydantic schema: Base/Create/Update/Response cho các entity chính 
+ Khởi tạo bảng thành công (Base.metadata.create_all)
Exception handler cơ bản (404/400/403) + healthcheck endpoin 


# Buổi 2 
Ngày bắt đầu : 21/8/2026 
Giờ : 12:45(PM)


Đã hoàn thành xong : 
+ Post/auth/register 
+ Hash password bằng bcrypt/passlib 
+ Post/auth/login trả JWT access token 
OAuth2PasswordBearer + get_current_user 
+ Role guard user/admin (require_admin)
+ Get/users/me,get/users(admin,search +filter is_active)
+ Xử lý lỗi token hết hạn/sai -> trả về 401,tài khoản không hoạt động 403

# Buổi 3 
Ngày bắt đầu : 22/08/2025 
Giờ : 12:45 AM 

Đã Hoàn Thành : 
- [x] POST /research-projects (tự động owner = OWNER)
  - [x] GET /research-projects (chỉ trả project user thuộc về, search theo tên)
  - [x] GET /research-projects/{id} (chỉ thành viên đề tài mới được xem)
  - [x] PUT/PATCH/DELETE đề tài; chỉ OWNER được sửa/xóa
  - [x] Thêm/xóa/danh sách member (không cho trùng, không xóa owner cuối)
  - [x] Validate dữ liệu đề tài
- **Vấn đề gặp phải / cách xử lý:**
  - Dùng nhầm `FastAPI()` thay vì `APIRouter()` khi khởi tạo router
  - Gõ nhầm `@router.path()` thay vì `.patch()`, thiếu dấu `/` đầu path ở route xóa
  - Logic đảo ngược `if member.role == "OWNER"` thay vì `!=` khi check quyền sửa
  - Sai cú pháp `ResearchMember.filter()` thay vì `db.query(ResearchMember).filter()`
  - Sai thụt lề khiến điều kiện chặn xóa OWNER cuối nằm ngoài khối kiểm tra, gây NameError
  - Dán nhầm code schema (`class ProjectBase(BaseModel)`) xuống cuối file router
  - Swagger UI không cập nhật nhóm route mới do cache trình duyệt — xác nhận bằng `python -c "from app.main import app; print(list(app.openapi()['paths'].keys()))"` để kiểm tra route thực tế đã đăng ký đúng trước khi kết luận

# Buổi 4 : 
Ngày 25/8/2026
Giờ : 10:55 PM 
Quản lý Nhiệm vụ Nghiên cứu (Research Tasks)
* **Tạo nhiệm vụ mới (`POST`):** Cho phép thành viên trong đề tài thêm mới task với các mức độ ưu tiên (`LOW`, `MEDIUM`, `HIGH`) và trạng thái (`TODO`, `IN_PROGRESS`, `DONE`).
* **Lấy danh sách & Lọc (`GET`):** Hỗ trợ phân trang (`skip`, `limit`), tìm kiếm theo tiêu đề, và lọc linh hoạt theo `status`, `priority`, hoặc `assignee_id`.
* **Xem chi tiết nhiệm vụ (`GET /{task_id}`):** Truy xuất thông tin cụ thể của một task, kèm kiểm tra quyền thành viên trong đề tài.
* **Cập nhật nhiệm vụ (`PATCH /{task_id}`):** Cho phép cập nhật linh hoạt các trường thông tin của task (tiêu đề, trạng thái, độ ưu tiên...).
* **Xóa nhiệm vụ (`DELETE /{task_id}`):** Xóa bỏ nhiệm vụ không còn cần thiết một cách an toàn.

Buổi 5 : Quản lý Tài liệu Đề tài & Kiến trúc Dịch vụ (Research Documents & Services)
* Xây dựng tầng **Service (`services/file_service.py`)** để cô lập logic xử lý file.
  * **Siết chặt bảo mật:** Kiểm tra nghiêm ngặt phần mở rộng file (chỉ chấp nhận `.pdf`, `.docx`, `.xlsx`, `.txt`, `.zip`, `.doc`, `.rar`, `.csv`).
  * **Chống trùng lặp:** Tự động đổi tên tệp sử dụng mã định danh `UUID` kết hợp `project_id` trước khi lưu trữ vật lý vào thư mục `uploads/documents/`.
* **Xem danh sách tài liệu (`GET`):** Quản lý và truy xuất danh sách tài liệu thuộc đề tài.
* **Xóa tài liệu (`DELETE`):** Xóa sạch thông tin metadata trong Database đồng thời dọn dẹp file vật lý trên ổ cứng server.

II. Cấu trúc thư mục và siết chặt bảo mật 
Dự án tuân thủ mô hình phân tầng chuẩn mực để đảm bảo tính bảo mật và dễ bảo trì:
* **`routers/`**: Chứa các API endpoints chính (xử lý request và response).
* **`services/`**: Cô lập logic nghiệp vụ phức tạp (ví dụ: `file_service.py` xử lý kiểm tra và lưu trữ file an toàn).
* **`schemas/`**: Sử dụng **Pydantic** để validate chặt chẽ dữ liệu đầu vào, chặn các giá trị không hợp lệ (lỗi `422 Unprocessable Entity`).
* **`tests/`**: Chứa các kịch bản kiểm thử tự động (`pytest`) chuẩn bị sẵn sàng cho việc kiểm tra chất lượng phần mềm.

III. Trạng thái hiện tại & Kế hoạch tiếp theo 
* **Trạng thái:** Toàn bộ mã nguồn, cấu trúc service và kịch bản test (`tests/test_py.py`) đã được hoàn thiện, viết gọn gàng và siết chặt bảo mật.
* **Kế hoạch tiếp theo (Sáng mai):** 
  1. Tiến hành chạy bộ kiểm thử (`pytest`) để kiểm tra tổng thể các kịch bản chặn lỗi (Validate, File Upload, Phân quyền).
  2. Hoàn tất kiểm thử thực tế trên Swagger UI.
  3. Thực hiện lệnh `git push` chính thức lên kho lưu trữ GitHub.

## 🧪 Hướng dẫn Kiểm thử Tự động (Automated Testing)

Dự án đã được tích hợp bộ test tự động toàn diện từ Tiết 1 đến Tiết 5 (kiểm tra từ khởi động, CSDL, Auth, Đề tài, Nhiệm vụ cho đến xử lý ngoại lệ). 

### 1. Điều kiện tiên quyết
- Đã kích hoạt môi trường ảo (`venv`).
- Đã cấu hình file `.env` kết nối Database MySQL thực tế.

### 2. Câu lệnh chạy Test
Mở Terminal tại thư mục gốc của project và chạy lệnh sau:

```bash
python -m pytest tests/test.py -v
