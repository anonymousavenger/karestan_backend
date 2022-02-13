from typing import Optional
from models.main_models import Company
from argon2 import PasswordHasher
from copy import copy
from sqlalchemy.orm import Query

from .auth import db_session
from util.db_operations import add_to_db, del_from_db, safe_commit

q = db_session.query(Company)

def query_companies(**kwargs) -> Query:
    qe = copy(q)
    for attr,val in kwargs.items():
        qe = qe.where(getattr(Company,attr) == val)
    return qe

def find_company(company_name) -> Optional[Company]:
    company:Optional[Company] = q.where(Company.fa_name == company_name).first()


def create_company(fa_name:str, en_name:str, email:str, website:str, national_id:str, phone: str, 
city_id: int, is_verified:bool = False, info:dict=None):
    company = Company(fa_name=fa_name, en_name=en_name, email=email,website=website, national_id=national_id, phone=phone,
    city_id=city_id, is_verified=is_verified, info=info)
    add_to_db(session=db_session,models=company)
    return company.to_dict()

def update_company(company_id:int,**kwargs):
    company:Optional[Company] = q.get(company_id) 
    if company is None:
        return None
    if len(kwargs) < 1:
        raise ValueError("At least one entry is needed to update user. Zero given")
    for key,value in kwargs.items():
        setattr(company,key,value)
    db_session.merge(company)
    safe_commit(session=db_session)
    company.id # TEMP This is used to refresh the instance. Need to find a proper way to refresh
    return company.to_dict()

def del_company(company_id:int):
    company:Optional[Company] = q.get(company_id)
    if company is not None:
        del_from_db(session=db_session, model=company)
        return True
    else:
        return "Company not found"

def get_company_info(company_id:int):
    company:Optional[Company] = q.get(company_id)
    if company is not None:
        return company.to_dict()
    else:
        return "Company not found"
    