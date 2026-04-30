from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./crm.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Database Model ---
class InteractionRecord(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    hcp_name = Column(String, index=True)
    interaction_type = Column(String)
    date = Column(String)
    time = Column(String)
    attendees = Column(String)
    topics = Column(Text)
    materials = Column(Text)  # Stored as JSON string
    samples = Column(Text)    # Stored as JSON string
    sentiment = Column(String)
    outcomes = Column(Text)
    follow_ups = Column(Text)

class FollowUpRecord(Base):
    __tablename__ = "follow_ups"

    id = Column(Integer, primary_key=True, index=True)
    hcp_name = Column(String, index=True)
    task_name = Column(String)
    date = Column(String)
    status = Column(String, default="Pending")

# Create the table in the database
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()