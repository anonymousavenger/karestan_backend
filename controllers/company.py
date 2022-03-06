from typing import List, Optional, Union
from models.main_models import Company, Feedback, FeedbackType, Interview, Review
from copy import copy
from sqlalchemy.orm import Query, with_polymorphic
from sqlalchemy import desc
from random import randint

from .auth import db_session
from util.db_operations import add_to_db, del_from_db, safe_commit
from util.validation import create_dir_name

q = db_session.query(Company)

def create_unqiue_dirname(en_name):
    """Since we may later edit company's en_name, we need to make sure that dir name is always unique"""
    alt_dir_name = dir_name = create_dir_name(en_name)
    c = q.filter(Company.dirname == dir_name).count()
    while c > 1:
        alt_dir_name = dir_name + "_" + str(randint(0,10000))
        c = q.filter(Company.dirname == alt_dir_name).count()
    return alt_dir_name


def query_companies(**kwargs) -> Query:
    qe = copy(q)
    for attr,val in kwargs.items():
        qe = qe.where(getattr(Company,attr) == val)
    return qe

def get_company(company_id:int) -> Company:
    company:Optional[Company] = q.get(company_id)
    if company is not None:
        return company
    else:
        raise ValueError


def create_company(fa_name:str, en_name:str, email:str, website:str, national_id:str, phone: str, \
city_id: int, is_verified:bool = False, info:dict=None):
    dirname = create_unqiue_dirname(en_name)
    company = Company(fa_name=fa_name, en_name=en_name, email=email,website=website, national_id=national_id, phone=phone,
    city_id=city_id, dirname=dirname, is_verified=is_verified, info=info)
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
    company:Company = get_company(company_id=company_id)
    return company.to_dict()

def get_company_feedback_info(company_id:int, feedback_type: Optional[FeedbackType] = None, offset: Optional[int] = None) -> Optional[Union[dict, List[dict]]]:
    ftype = [feedback_type]
    if feedback_type is None:
        subclass = '*'
        ftype = [FeedbackType.interview, FeedbackType.review]
    elif feedback_type == FeedbackType.interview:
        subclass = Interview
    elif feedback_type == FeedbackType.review:
        subclass = Review
    else:
        raise TypeError

    wpm = with_polymorphic(Feedback, subclass)
    q = db_session.query(wpm).filter(Feedback.company_id == company_id, Feedback.type.in_(ftype)).order_by(desc(Feedback.created_at))

    if offset is not None:
        if offset < 1:
            raise ValueError
        feedback: Optional[Feedback] = q.filter(wpm.id).offset(offset).first()
        if feedback is None:
            return None
        return feedback.to_dict()
    else:
        feedbacks = q.all()
        if feedbacks is None:
            return None
        return [feedback.to_dict() for feedback in feedbacks]
