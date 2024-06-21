from sqlalchemy.orm import Session
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))) # Note: Reason why done ~ https://stackoverflow.com/questions/4383571/importing-files-from-different-folder
from models.postgresModels import UserModel # has SQLAlchemy ORM models
from schemas.postgresSchemas import UserBaseSchema, UserCreateSchema, UserUpdateSchema, UserSchema # has Pydantic models
from datetime import datetime

#For Task12
def get_user(db: Session, user_id: int):
    # db: Session: The database session used to query the database; user_id: int: The ID of the user to retrieve.
    return db.query(UserModel).filter(UserModel.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 10):
    return db.query(UserModel).offset(skip).limit(limit).all()

def create_user(db: Session, user: UserCreateSchema):
    # The data for the new user, validated by Pydantic UserCreateSchema, later converted to dict below
    db_user = UserModel(**user.dict(), created_at=datetime.utcnow())
    # We are adding created_at=datetime.utcnow(), and UserCreateSchema looks like: name: str, type: str, phone: int, address: str. Note that we are not explicitly adding id, as the user_id is automatically generated by the database because it is defined as a primary key in the model.
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user: UserUpdateSchema):
    # The updated data for the user, validated by Pydantic.
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if db_user is None:
        return None
    for key, value in user.dict().items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if db_user is None:
        return None
    db.delete(db_user)
    db.commit()
    return db_user
