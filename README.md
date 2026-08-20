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


