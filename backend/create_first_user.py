import os
import sys
import bcrypt
import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Get the absolute path to the backend directory
backend_dir = os.path.dirname(os.path.abspath(__file__))

# Add the backend directory to the Python path
sys.path.insert(0, backend_dir)

# Import the database models and configuration
from app.db.models import Base, User
from app.core.config import settings

# User credentials
username = "admin"
email = "admin@example.com"
password = "admin123"

def get_password_hash(password):
    """Generate a password hash using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def main():
    print(f"Creating admin user: {username}")
    
    # Create database engine
    engine = create_engine(settings.DATABASE_URL)
    
    # Create all tables if they don't exist
    Base.metadata.create_all(engine)
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Check if user already exists
    existing_user = session.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()
    
    if existing_user:
        print(f"User with username '{username}' or email '{email}' already exists!")
        print("\nYou can log in with:")
        print(f"Username: {username}")
        print(f"Password: {password}")
    else:
        # Generate user data
        user_id = str(uuid.uuid4())
        hashed_password = get_password_hash(password)
        now = datetime.utcnow()
        
        # Create new user
        new_user = User(
            id=user_id,
            username=username,
            email=email,
            hashed_password=hashed_password,
            created_at=now,
            updated_at=now,
            is_active=True,
            is_superuser=True
        )
        
        # Add user to database
        session.add(new_user)
        session.commit()
        
        print("Admin user created successfully!")
        print("\nYou can now log in with:")
        print(f"Username: {username}")
        print(f"Password: {password}")
    
if __name__ == "__main__":
    main()