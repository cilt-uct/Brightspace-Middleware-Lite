
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated, List

from auth.dependencies import authenticate_user
from schemas import datatables
from db import crud, database, models, schemas
from db.database import get_db

# from db.repository.users import create_new_user
# from db.session import get_db
# from schemas.users import ShowUser
# from schemas.users import UserCreate

# @router.post("/", response_model=ShowUser)
# def create_user(user: UserCreate, db: Session = Depends(get_db)):
#     user = create_new_user(user=user, db=db)
#     return user

router = APIRouter()

@router.get("/me")
def read_current_user(username: Annotated[str, Depends(authenticate_user)]):
    return {"username": username}

@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, eid=user.eid)
    if db_user:
        raise HTTPException(status_code=400, detail="EID already registered")
    return crud.create_user(db=db, user=user)

@router.get("/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/{eid}", response_model=schemas.User)
def read_user(eid: str, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, eid=eid)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
