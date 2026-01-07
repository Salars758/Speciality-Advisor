# dependencies.py
from fastapi import Depends
from sqlalchemy.orm import Session
from .database import get_db
from .auth import get_current_user

def get_current_active_user(
    current_user: dict = Depends(get_current_user)
):
    return current_user