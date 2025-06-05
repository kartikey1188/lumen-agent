from sqlalchemy.orm import Session
from fastapi import Depends
from models.sqlite import get_db
from models.sqlite.models import UnalteredHistory, Role