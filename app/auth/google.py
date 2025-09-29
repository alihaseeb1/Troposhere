import requests
from fastapi import APIRouter, Depends, HTTPException
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from sqlalchemy.orm import Session
from ..config import settings
from ..database import get_db
from ..models import User
from datetime import datetime, timedelta, timezone
import jwt

oauth = OAuth()

oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


