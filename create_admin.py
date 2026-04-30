from app import create_app
from database import db, bcrypt
from models import User

app = create_app()

with app.app_context():
    # Check if admin user already exists
    admin_user = User.query.filter_by(email="theadmin@gmail.com").first()
    
    if admin_user:
        # Update existing user to admin
        admin_user.role = "admin"
        db.session.commit()
        print("✅ Admin role updated successfully")
        print(f"📧 Email: {admin_user.email}")
        print(f"👤 Role: {admin_user.role}")
    else:
        # Create new admin user
        hashed_password = bcrypt.generate_password_hash("admin1234").decode('utf-8')
        
        new_admin = User(
            full_name="ADMIN",
            email="theadmin@gmail.com",
            phone="08000000000",
            password_hash=hashed_password,
            role="admin",
            is_active=True
        )
        
        db.session.add(new_admin)
        db.session.commit()
        print("✅ Admin user created successfully")
        print(f"📧 Email: {new_admin.email}")
        print(f"👤 Role: {new_admin.role}")
        print(f"🔑 Password: admin1234")
