from .database import engine
from .models import User
from sqlmodel import Session, select
from .security import get_password_hash

def create_admin():
    with Session(engine) as session:
        # Check if the admin user already exists
        existing_admin = session.exec(select(User).where(User.username == "admin")).first()
        if existing_admin:
            print("Admin user already exists.")
            return
        
        # Create a new admin user
        admin_user = User(
            username="admin",
            hashed_password=get_password_hash("admin123"),  # Use a secure password
            role="admin"
        )
        
        session.add(admin_user)
        session.commit()
        session.refresh(admin_user)
        print(f"Admin user created: {admin_user.username}")

if __name__ == "__main__":
    create_admin()
    print("Admin user creation script executed.")