#!/usr/bin/env python3
"""
Create sample data for testing the Book RAG System
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.author import Author
from app.models.user import User
from app.core.config import settings
from app.api.v1.endpoints.auth import get_password_hash

def create_sample_data():
    """Create sample authors and users for testing."""
    print("🔧 Creating sample data...")
    
    # Create database session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Create sample authors
        authors = [
            Author(
                name="Daniel Kahneman",
                bio="Nobel Prize-winning psychologist and economist, author of 'Thinking, Fast and Slow'. Expert in behavioral economics and cognitive biases."
            ),
            Author(
                name="Nassim Nicholas Taleb",
                bio="Lebanese-American essayist, scholar, and former trader. Author of 'The Black Swan' and 'Antifragile'. Expert in risk and uncertainty."
            ),
            Author(
                name="Robert Cialdini",
                bio="American psychologist known for his work on persuasion and influence. Author of 'Influence: The Psychology of Persuasion'."
            ),
            Author(
                name="Malcolm Gladwell",
                bio="Canadian journalist and author. Known for books like 'Outliers', 'Blink', and 'The Tipping Point'."
            ),
            Author(
                name="Yuval Noah Harari",
                bio="Israeli historian and philosopher. Author of 'Sapiens', 'Homo Deus', and '21 Lessons for the 21st Century'."
            ),
            Author(
                name="Steven Pinker",
                bio="Canadian-American cognitive psychologist and linguist. Author of 'The Better Angels of Our Nature' and 'Enlightenment Now'."
            )
        ]
        
        for author in authors:
            existing = db.query(Author).filter(Author.name == author.name).first()
            if not existing:
                db.add(author)
                print(f"✅ Added author: {author.name}")
            else:
                print(f"⚠️  Author already exists: {author.name}")
        
        # Create sample users with simple password
        users = [
            {
                "email": "demo@user.com",
                "username": "demouser",
                "password": "demo123"
            },
            {
                "email": "author@demo.com", 
                "username": "demoauthor",
                "password": "demo123"
            }
        ]
        
        for user_data in users:
            existing = db.query(User).filter(User.email == user_data["email"]).first()
            if not existing:
                # Simple hash for demo
                import hashlib
                simple_hash = hashlib.sha256(user_data["password"].encode()).hexdigest()
                
                user = User(
                    email=user_data["email"],
                    username=user_data["username"],
                    hashed_password=simple_hash
                )
                db.add(user)
                print(f"✅ Added user: {user_data['email']}")
            else:
                print(f"⚠️  User already exists: {user_data['email']}")
        
        db.commit()
        print("\n🎉 Sample data created successfully!")
        
        print("\n📋 Test Accounts:")
        print("User Account:")
        print("  Email: demo@user.com")
        print("  Password: demo123")
        print("\nAuthor Account:")
        print("  Email: author@demo.com")
        print("  Password: demo123")
        
        print(f"\n👥 Created {len(authors)} sample authors")
        print("You can now test the web interface!")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data()