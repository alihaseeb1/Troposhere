from fastapi import FastAPI
from .routers import login
from .database import Base, engine
from starlette.middleware.sessions import SessionMiddleware
from .config import settings

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

app.include_router(login.router)

# we don't need this as alembic will take care of it
# Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "Hello, World!"}


