# database import

from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("ERROR: DATABASE_URL not found in .env file!")

if DATABASE_URL.startswith("sqlite"):
    # if sqlite use add check_same_thread , if not remove it
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False,bind=engine)
Base = declarative_base()
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_db_and_table():
    from app.models.group import Group
    from app.models.user import User
    from app.models.expense import Expense
    from app.models.friend import Friend
    from app.models.settlement import Settlement 
    from app.models.token_blacklist import BlacklistedToken 
    Base.metadata.create_all(bind=engine)
