from fastapi import FastAPI,Depends
from app.api.auth import router as auth_router   
from app.api.users import router as users_router
from app.api.groups import router as groups_router
from app.api.expenses import router as expenses_router
from app.api.friend import router as friend_router
from app.api.settlement import router as settlement_router

from app.api.google import router as google_auth_router


from app.db.data import Base,engine
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.middleware import exception_middleware
import os

from starlette.middleware.sessions import SessionMiddleware

from app.db import data
from contextlib import asynccontextmanager
from dotenv import load_dotenv
load_dotenv()

@asynccontextmanager 
async def lifespan_manager(app:FastAPI): #lifespan ma lakhelo code only 1 time run thay avo hoy, jya e server start thy k stop thy 
    data.create_db_and_table()
    yield 
Base.metadata.create_all(bind=engine)

app = FastAPI(title="This is Splitwise", lifespan=lifespan_manager)

app.middleware("http")(exception_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          #atyre am thik jyre deploy kariye tyre frontend ni url nakhvani (like "http://localhost:5173")
    allow_credentials=True,
    allow_methods=["*"],          # GET, POST, PUT, DELETE - allow
    allow_headers=["*"]
)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY")
)


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(google_auth_router)
app.include_router(groups_router)
app.include_router(expenses_router)
app.include_router(settlement_router) 
app.include_router(friend_router)

@app.get("/")
async def welcome():
    return {
        "status": "success",
        "msg":"welcome to the splitewise server"
    }

