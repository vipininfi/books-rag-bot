#!/usr/bin/env python3
"""
Setup script for Book RAG System
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return None


def check_prerequisites():
    """Check if required tools are installed."""
    print("🔍 Checking prerequisites...")
    
    requirements = {
        "python3": "python3 --version",
        "pip": "pip --version",
        "postgresql": "psql --version",
    }
    
    missing = []
    for tool, command in requirements.items():
        if not run_command(command, f"Checking {tool}"):
            missing.append(tool)
    
    if missing:
        print(f"\n❌ Missing prerequisites: {', '.join(missing)}")
        print("Please install the missing tools and run setup again.")
        sys.exit(1)
    
    print("✅ All prerequisites found")


def setup_environment():
    """Setup environment file."""
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if not env_file.exists() and env_example.exists():
        print("\n📝 Creating .env file from template...")
        env_file.write_text(env_example.read_text())
        print("✅ .env file created")
        print("⚠️  Please update .env with your actual configuration values")
    else:
        print("✅ .env file already exists")


def install_dependencies():
    """Install Python dependencies."""
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        print("❌ Failed to install dependencies")
        sys.exit(1)


def setup_database():
    """Setup database and run migrations."""
    print("\n🗄️  Setting up database...")
    
    # Check if database exists
    db_check = run_command(
        "psql -lqt | cut -d \\| -f 1 | grep -qw bookrag", 
        "Checking if database exists"
    )
    
    if db_check is None:
        # Create database
        if not run_command("createdb bookrag", "Creating database"):
            print("❌ Failed to create database")
            print("Please ensure PostgreSQL is running and you have permissions")
            sys.exit(1)
    
    # Run migrations
    if not run_command("alembic upgrade head", "Running database migrations"):
        print("❌ Failed to run migrations")
        sys.exit(1)


def check_pinecone():
    """Check if Pinecone API key is configured."""
    print("\n🔍 Checking Pinecone configuration...")
    
    # Try to connect to Pinecone
    test_script = """
import os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('PINECONE_API_KEY')
if not api_key:
    print('❌ PINECONE_API_KEY not found in .env file')
    print('Please add your Pinecone API key to .env file')
else:
    try:
        from pinecone import Pinecone
        pc = Pinecone(api_key=api_key)
        indexes = pc.list_indexes()
        print('✅ Pinecone connection successful')
        print(f'Available indexes: {[idx.name for idx in indexes]}')
    except Exception as e:
        print(f'❌ Pinecone connection failed: {str(e)}')
        print('Please check your API key and internet connection')
"""
    
    run_command(f"python3 -c \"{test_script}\"", "Testing Pinecone connection")


def create_sample_data():
    """Create sample authors for testing."""
    print("\n👥 Creating sample data...")
    
    sample_script = """
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.author import Author
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Create sample authors
authors = [
    Author(name="Daniel Kahneman", bio="Nobel Prize winner, author of Thinking, Fast and Slow"),
    Author(name="Nassim Nicholas Taleb", bio="Author of The Black Swan and Antifragile"),
    Author(name="Robert Cialdini", bio="Author of Influence: The Psychology of Persuasion"),
]

for author in authors:
    existing = db.query(Author).filter(Author.name == author.name).first()
    if not existing:
        db.add(author)

db.commit()
db.close()
print("✅ Sample authors created")
"""
    
    run_command(f"python3 -c \"{sample_script}\"", "Creating sample authors")


def main():
    """Main setup function."""
    print("🚀 Setting up Book RAG System")
    print("=" * 50)
    
    # Check prerequisites
    check_prerequisites()
    
    # Setup environment
    setup_environment()
    
    # Install dependencies
    install_dependencies()
    
    # Setup database
    setup_database()
    
    # Check Pinecone
    check_pinecone()
    
    # Create sample data
    create_sample_data()
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Update .env file with your OpenAI API key")
    print("2. Pinecone will automatically create the index on first use")
    print("3. Start the application: uvicorn app.main:app --reload")
    print("4. Visit http://localhost:8000/docs for API documentation")


if __name__ == "__main__":
    main()