from .database import engine
from .models_user import User
from sqlmodel import Session, select
from ..auth.security import get_password_hash
from color_utils import cp

def create_admin():
    import getpass
    username = input("Enter admin username: ").strip()
    while not username:
        username = input("Username cannot be empty. Enter admin username: ").strip()

    password = getpass.getpass("Enter admin password: ")
    while not password:
        password = getpass.getpass("Password cannot be empty. Enter admin password: ")

    with Session(engine) as session:
        # Check if the admin user already exists
        existing_admin = session.exec(select(User).where(User.role == "admin")).first()
        if existing_admin:
            cp.print_warning("Admin user already exists.")
            # return

        # Create a new admin user
        admin_user = User(
            username=username,
            hashed_password=get_password_hash(password),
            role="admin"
        )

        session.add(admin_user)
        session.commit()
        session.refresh(admin_user)
        cp.print_info(f"Admin user created: {admin_user.username}")

if __name__ == "__main__":
    create_admin()
    cp.print_info("Admin user creation script executed.")
