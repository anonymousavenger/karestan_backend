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

def create_user(user_name:str, password:str, email:str, type:str = UserType.employee.name):
    ph = PasswordHasher()
    user = User(name=user_name, password=ph.hash(password), email=email,type=UserType[type])
    add_to_db(session=db_session,models=user)
    return generate_auth_token(identity=user)

def update_user(**kwargs):
    mapper = {
        "user_name": "name",
        "email": "email",
        "password": "password"
    }
    user:User = get_current_user()
    if len(kwargs) < 1:
        raise ValueError("At least one entry is needed to update user. Zero given")
    for key,value in kwargs.items():
        setattr(user,mapper[key],value)
    safe_commit(session=db_session)

def del_user():
    user:User =  get_current_user()
    del_from_db(session=db_session, model=user)
    return True

def get_user_info():
    user: User = get_current_user()
    return user.to_dict()