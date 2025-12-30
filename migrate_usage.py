import json
import os
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.models.usage import UsageLog
from app.db.database import Base

def migrate_logs():
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    logs_dir = Path("logs")
    if not logs_dir.exists():
        print("❌ No logs directory found.")
        return
    
    db = SessionLocal()
    try:
        log_files = list(logs_dir.glob("token_usage_*.jsonl"))
        print(f"📂 Found {len(log_files)} log files.")
        
        total_migrated = 0
        for log_file in log_files:
            print(f"📖 Processing {log_file.name}...")
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        
                        # Check if already exists (basic check by timestamp and user_id)
                        # This is not perfect but helps prevent duplicates if run multiple times
                        timestamp = datetime.fromisoformat(data["timestamp"])
                        exists = db.query(UsageLog).filter(
                            UsageLog.timestamp == timestamp,
                            UsageLog.user_id == data["user_id"],
                            UsageLog.operation_type == data["operation_type"]
                        ).first()
                        
                        if not exists:
                            db_log = UsageLog(
                                timestamp=timestamp,
                                user_id=data["user_id"],
                                operation_type=data["operation_type"],
                                query=data.get("query", ""),
                                model_name=data["model_name"],
                                prompt_tokens=data["prompt_tokens"],
                                completion_tokens=data["completion_tokens"],
                                total_tokens=data["total_tokens"],
                                cost_estimate=data["cost_estimate"],
                                response_time=data["response_time"],
                                success=data["success"],
                                error_message=data.get("error_message")
                            )
                            db.add(db_log)
                            total_migrated += 1
                            
                            # Commit in batches
                            if total_migrated % 100 == 0:
                                db.commit()
                                print(f"✅ Migrated {total_migrated} entries...")
                                
                    except Exception as e:
                        print(f"⚠️ Error processing line: {e}")
        
        db.commit()
        print(f"🎉 Migration complete! Total entries migrated: {total_migrated}")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_logs()
