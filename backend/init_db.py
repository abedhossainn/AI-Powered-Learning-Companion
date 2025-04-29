"""
Database initialization script for the AI-Powered Learning Companion.
This script creates all required tables in the database.
"""
import os
import sys
import bcrypt
import uuid
from datetime import datetime
import traceback

# Add current directory to the path so we can import modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    # Import database models and engine
    print("Importing database models...")
    from app.db.models import Base, User
    from app.db.session import engine
    from app.core.config import settings
    
    print(f"Database URL: {settings.DATABASE_URL}")
    
    def initialize_database():
        """Create all database tables."""
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")
    
    def create_admin_user():
        """Create an admin user if one doesn't exist."""
        from sqlalchemy.orm import sessionmaker
        
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Admin user details
        username = "admin"
        email = "admin@example.com"
        password = "admin123"
        
        # Check if admin user exists
        user = session.query(User).filter(User.username == username).first()
        
        if user:
            print(f"Admin user '{username}' already exists.")
            
            # Verify password works
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            
            test_result = bcrypt.checkpw(password.encode('utf-8'), user.hashed_password.encode('utf-8'))
            if not test_result:
                print("Updating admin password...")
                user.hashed_password = hashed.decode('utf-8')
                session.commit()
        else:
            print(f"Creating admin user: {username}")
            
            # Generate password hash
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
            
            # Create new user
            new_user = User(
                id=str(uuid.uuid4()),
                username=username,
                email=email,
                hashed_password=hashed_password,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                is_active=True,
                is_superuser=True
            )
            
            session.add(new_user)
            session.commit()
            print("Admin user created successfully!")
        
        print("\nYou can now log in with:")
        print(f"Username: {username}")
        print(f"Password: {password}")
    
    def main():
        """Run the initialization process."""
        print("Initializing database...")
        initialize_database()
        print("\nSetting up admin user...")
        create_admin_user()
        print("\nDatabase initialization complete!")
    
    if __name__ == "__main__":
        main()
        
except Exception as e:
    print(f"Error: {str(e)}")
    print(traceback.format_exc())