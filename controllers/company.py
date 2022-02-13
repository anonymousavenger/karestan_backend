from typing import Optional
from models.main_models import Company
from argon2 import PasswordHasher
from copy import copy
from sqlalchemy.orm import Query

from .auth import generate_auth_token, get_current_user, db_session
from util.db_operations import add_to_db, del_from_db, safe_commit

q = db_session.query(Company)

def query_companies(**kwargs) -> Query:
    qe = copy(q)
    for attr,val in kwargs.items():
        qe = qe.where(getattr(Company,attr) == val)
    return qe

def find_company(company_name) -> Optional[Company]:
    company:Optional[Company] = q.where(Company.fa_name == company_name).first()

def authenticate_user(user_name, password):
    user = find_company(user_name)
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
        "new_user_name": "name",
        "new_email": "email",
        "new_password": "password"
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