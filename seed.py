from passlib.context import CryptContext
from db.database import SessionLocal
from models.user import User
from models.research_project import ResearchProject, ResearchMember
from models.research_task import ResearchTask

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def seed():
    db = SessionLocal()
    try:
        # Kiểm tra xem đã có dữ liệu chưa
        if db.query(User).filter(User.email == "admin@gmail.com").first():
            print("Database already seeded!")
            return

        # 1. Tạo Users
        admin = User(
            email="admin@gmail.com",
            password_hash=pwd_context.hash("Admin@123"),
            full_name="Admin System",
            role="ADMIN",
            is_active=True
        )
        user1 = User(
            email="gv_lead@gmail.com",
            password_hash=pwd_context.hash("123456"),
            full_name="Giang Vien Huong Dan",
            role="USER",
            is_active=True
        )
        user2 = User(
            email="sinhvien@gmail.com",
            password_hash=pwd_context.hash("123456"),
            full_name="Sinh Vien Nghien Cuu",
            role="USER",
            is_active=True
        )
        db.add_all([admin, user1, user2])
        db.commit()

        # 2. Tạo Project
        project = ResearchProject(
            name="Nghien cuu AI trong Y Te",
            description="De tai phan tich anh X-Quang phoi bang Deep Learning",
            owner_id=user1.id
        )
        db.add(project)
        db.commit()

        # 3. Thêm Members vào Project
        member1 = ResearchMember(project_id=project.id, user_id=user1.id, role="OWNER")
        member2 = ResearchMember(project_id=project.id, user_id=user2.id, role="MEMBER")
        db.add_all([member1, member2])
        db.commit()

        # 4. Tạo Task mẫu
        task = ResearchTask(
            project_id=project.id,
            title="Thu thap du lieu anh X-Quang",
            description="Tai tap du lieu tu Kaggle va tien xu ly",
            assignee_id=user2.id,
            status="IN_PROGRESS",
            priority="HIGH"
        )
        db.add(task)
        db.commit()

        print("Seeded database successfully with Users, Projects, Members, and Tasks!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()