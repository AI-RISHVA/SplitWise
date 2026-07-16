from sqlmodel import create_engine, Session
from fastapi import Depends
from typing import Annotated
from app.models.user import User
from app.models.group import Group
from app.models.expense import Expense


sqlite_file = "database.db"
sqlite_url= f"sqlite:///{sqlite_file}"

connect_args ={"check_same_thread":False} #default ma ek time par ek thread chale atle false kariye ek time par alag-alag request access kari sake
engine = create_engine(sqlite_url,connect_args=connect_args)

def create_db_and_table():
    from sqlmodel import SQLModel 
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session: # Yeh database se ek temporary connection kholta hai.
        yield session

SessionDep = Annotated[Session,Depends(get_session)]


