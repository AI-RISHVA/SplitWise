# database import

from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(DATABASE_URL,connect_args={"check_same_thread":False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
Base.metadata.create_all(bind=engine)
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
    Base.metadata.create_all(bind=engine)
