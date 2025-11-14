from fastapi import FastAPI
from .routers import login, clubs, items, borrow, returns, users
from .database import Base, engine
from starlette.middleware.sessions import SessionMiddleware
from .config import settings
from .logger import setup_logging
import logging
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
from starlette.middleware.cors import CORSMiddleware

app.include_router(login.router)
app.include_router(clubs.router)
app.include_router(items.router)
app.include_router(borrow.router)
app.include_router(returns.router)
app.include_router(users.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.ALLOWED_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# we don't need this as alembic will take care of it
# Base.metadata.create_all(bind=engine)
setup_logging()
logger = logging.getLogger(__name__)

@app.get("/")
def root():
    return {"message": "Hello, World!"}


