from sqlalchemy import Column, String, Text
from app.db.database import Base

class SystemSetting(Base):
    __tablename__ = "system_settings"

    key = Column(String, primary_key=True, index=True)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
