from sqlalchemy import Column, Integer, String, Text, DateTime
from database import Base
import datetime

class SearchDossier(Base):
    __tablename__ = "search_dossiers"

    id = Column(Integer, primary_key=True, index=True)
    query_type = Column(String, index=True) # email, phone, ip, username
    query_value = Column(String, index=True)
    results_json = Column(Text) # Store results as JSON string
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
