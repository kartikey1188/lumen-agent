from sqlalchemy import Column, Integer, String, Enum as SQLEnum
from . import Base     
from enum import Enum
from sqlalchemy import DateTime
from datetime import datetime, timezone

class Role(Enum):
    USER = "user"   
    AGENT = "agent"

class UnalteredHistory(Base):
    __tablename__ = 'unaltered_history'
    
    message_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    message = Column(String, nullable=False)
    role = Column(SQLEnum(Role), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

