from typing import Optional

from jwt import ExpiredSignatureError
from models.main_models import User, UserType
from argon2 import PasswordHasher

from util.exceptions import ResponseException
from .auth import generate_auth_token, get_current_user, db_session, q
from util.db_operations import add_to_db, del_from_db, safe_commit

# TODO Add logout functionality and add token invalidator to it

def login(email, password):
    try:
        token = authenticate_user(email=email, password=password)
        return {"token":token}
    except ValueError:
        raise ResponseException(code=400,message="User or password is incorrect")

def find_user(email, password) -> Optional[User]:
    user:Optional[User] = q.where(User.email == email).first()
    ph = PasswordHasher()
    if user is not None and ph.verify(hash = str(user.password), password=password):
        return user
    return None

def authenticate_user(email, password):
    user = find_user(email, password)
    if user is not None:
        return generate_auth_token(identity=user)
    else:
        raise ValueError

def create_user(user_name:str, password:str, email:str, type:str = UserType.employee.name):
    ph = PasswordHasher()
    user = User(name=user_name, password=ph.hash(password), email=email,type=UserType[type])
    add_to_db(session=db_session,models=user)
    return {'token': generate_auth_token(identity=user)}

def update_user(**kwargs):
    user:User = get_current_user()
    if len(kwargs) < 1:
        raise ValueError("At least one entry is needed to update user. Zero given")
    for key,value in kwargs.items():
        setattr(user,key,value)
    safe_commit(session=db_session)
    user.id
    return user.to_dict()

def del_user():
    user:User =  get_current_user()
    del_from_db(session=db_session, model=user)
    return True

def get_user_info():
    try:
        user: User = get_current_user()
        return user.to_dict()
    except ExpiredSignatureError:
        raise ResponseException(code=400, message='User session expired')