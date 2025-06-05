from sqlalchemy import Column, Integer, String, Enum as SQLEnum
from . import Base     
from enum import Enum

class Role(Enum):
    USER = "user"   
    AGENT = "agent"

class UnalteredHistory(Base):
    __tablename__ = 'unaltered_history'
    
    message_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(SQLEnum(Role), nullable=False)
    message = Column(String, nullable=False)
    role = Column(SQLEnum(Role), nullable=False)
