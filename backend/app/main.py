from fastapi import FastAPI,Depends
from app.api.auth import router as auth_router   
from app.api import users as users_routes
from app.api import groups as groups_routes
from app.api import expenses as expenses_routes
from app.api.friend import router as friend_router
from app.api import settlement as settlement_routes 
from app.db.data import Base,engine


from app.db import data
from contextlib import asynccontextmanager


@asynccontextmanager 
async def lifespan_manager(app:FastAPI): #lifespan ma lakhelo code only 1 time run thay avo hoy, jya e server start thy k stop thy 
    data.create_db_and_table()
    yield 
Base.metadata.create_all(bind=engine)

app = FastAPI(title="This is Splitwise", lifespan=lifespan_manager)

app.include_router(auth_router)
app.include_router(users_routes.router)
app.include_router(groups_routes.router)
app.include_router(expenses_routes.router)
app.include_router(settlement_routes.router) 
app.include_router(friend_router)

@app.get("/")
async def welcome():
    return {
        "status": "success",
        "msg":"welcome to the splitewise server"
    }

