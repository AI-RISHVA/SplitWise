from fastapi import FastAPI,Depends
from app.api import users as users_routes
from app.api import groups as groups_routes
from app.api import expenses as expenses_routes


from app.db import session
from contextlib import asynccontextmanager


@asynccontextmanager 
async def lifespan_manager(app:FastAPI): #lifespan ma lakhelo code only 1 time run thay avo hoy, jya e server start thy k stop thy 
    session.create_db_and_table()
    yield 

app = FastAPI(title="This is Splitwise", lifespan=lifespan_manager)

app.include_router(users_routes.router)
app.include_router(groups_routes.router)
app.include_router(expenses_routes.router)


@app.get("/")
async def welcome():
    return {
        "status": "success",
        "msg":"welcome to the splitewise server"
    }

