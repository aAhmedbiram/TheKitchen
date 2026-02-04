#!/usr/bin/env python3
"""
Create admin user script for The Kitchen
Run this script to create an admin user for the application
"""

from app import create_app
from models import User
from werkzeug.security import generate_password_hash
from extensions import db

def create_admin_user():
    """Create an admin user"""
    app = create_app()
    
    with app.app_context():
        # Check if admin already exists
        existing_admin = User.query.filter_by(email='admin@thekitchen.com').first()
        if existing_admin:
            print("⚠️  Admin user already exists!")
            print(f"   Email: {existing_admin.email}")
            print("   To create another admin, modify this script or use the admin panel.")
            return
        
        # Create admin user
        admin = User(
            name="System Administrator",
            email="admin@thekitchen.com",
            password_hash=generate_password_hash("admin123"),
            is_admin=True
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print("✅ Admin user created successfully!")
        print("   Email: admin@thekitchen.com")
        print("   Password: admin123")
        print("   ⚠️  Please change the password after first login!")

if __name__ == "__main__":
    create_admin_user()
