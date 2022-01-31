from typing import Optional
from models.main_models import User, UserType
from argon2 import PasswordHasher

from .auth import generate_auth_token, get_current_user, db_session, q
from util.db_operations import add_to_db, del_from_db, safe_commit


def find_user(user_name, password) -> Optional[User]:
    user:Optional[User] = q.where(User.name == user_name).first()
    ph = PasswordHasher()
    if user is not None and ph.verify(hash = str(user.password), password=password):
        return user
    return None

def authenticate_user(user_name, password):
    user = find_user(user_name, password)
    if user is not None:
        return generate_auth_token(identity=user)
    else:
        raise ValueError

def add_user(name:str, password:str, email:str, type:UserType = UserType.employee):
    ph = PasswordHasher()
    user = User(name=name, password=ph.hash(password), email=email,type=type)
    add_to_db(session=db_session,models=user)
    return generate_auth_token(identity=user)


def update_user(**kwargs):
    user:User = get_current_user() 
    for key,value in kwargs:
        setattr(user,key,value)
    safe_commit(session=db_session)

def del_user():
    user:User =  get_current_user()
    del_from_db(session=db_session, model=user)

def get_user_info():
    user: User = get_current_user()
    return user.to_dict()