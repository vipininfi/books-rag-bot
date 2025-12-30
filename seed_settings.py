from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.models.settings import SystemSetting
from app.db.database import Base

def seed_settings():
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        default_settings = {
            "OPENAI_API_KEY": "sk-placeholder",
            "PINECONE_API_KEY": "placeholder",
            "MAX_FILE_SIZE_MB": "100",
            "MAX_BOOKS_PER_AUTHOR": "10"
        }
        
        for key, value in default_settings.items():
            db_setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
            if not db_setting:
                setting = SystemSetting(key=key, value=value)
                db.add(setting)
        
        db.commit()
        print("Default settings seeded successfully.")
    except Exception as e:
        print(f"Error seeding settings: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_settings()
