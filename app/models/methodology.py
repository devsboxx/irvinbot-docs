from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base


class MethodologyChunk(Base):
    __tablename__ = "methodology_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    step = Column(Integer, nullable=False, index=True)
    step_name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    source = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
