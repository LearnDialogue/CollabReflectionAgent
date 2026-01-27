#!/usr/bin/env python3
"""
Seed script to create an admin user.

Usage:
    python seed_admin.py [username] [password]

Default credentials: admin / admin123 (change in production!)
"""

import sys
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.models.student import Student, UserRole
from app.core.security import get_password_hash


def seed_admin(
    db: Session,
    username: str = "admin",
    password: str = "admin123",
) -> Student | None:
    """Create admin user if it doesn't exist."""
    
    # Check if admin already exists
    existing = db.query(Student).filter(Student.username == username).first()
    if existing:
        print(f"User '{username}' already exists (id={existing.id}, role={existing.role.value})")
        return existing
    
    # Create admin
    admin = Student(
        username=username,
        password_hash=get_password_hash(password),
        role=UserRole.ADMIN,
        display_name="Administrator",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    print(f"Created admin user: {username} (id={admin.id})")
    return admin


def main():
    """Main entry point."""
    # Parse CLI args
    username = sys.argv[1] if len(sys.argv) > 1 else "admin"
    password = sys.argv[2] if len(sys.argv) > 2 else "admin123"
    
    print(f"Seeding admin user: {username}")
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Seed admin
    db = SessionLocal()
    try:
        seed_admin(db, username, password)
    finally:
        db.close()
    
    print("Done!")


if __name__ == "__main__":
    main()
