from sqlalchemy import Column, String, DateTime
from db.base import Base

class News(Base):
    __tablename__ = "news"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    url = Column(String)
    published_at = Column(DateTime)