from typing import Callable, List, Union
from psycopg2.errors import InFailedSqlTransaction
from sqlalchemy.orm import Session
from models.base_model import Base

def safe_commit(session:Session):
    try:
        session.commit()
    except InFailedSqlTransaction as e:
        # TODO Add logger
        session.rollback()
        raise e

def add_to_db(session:Session, models:Union[List[Base],Base]):
    if type(models) == list:
        session.add_all(models)
    else:
        session.add(models)
    safe_commit(session=session)

def del_from_db(session:Session, model:Base):
    session.delete(model)
    safe_commit(session=session)

def add_to_db_dec(session:Session):
    def decorator(func:Callable) -> Callable:
        def add_and_commit(*args, **kwargs):
            models = func(*args, **kwargs)
            if type(models) == list:
                    session.add_all(models)
            else:
                session.add(models)
            safe_commit(session)
        return add_and_commit
    return decorator

def remove_from_db_dec(session:Session):
    def decorator(func:Callable) -> Callable:
        def del_and_commit(*args, **kwargs):
            model = func(*args, **kwargs)
            session.delete(model)
            safe_commit(session)
        return del_and_commit
    return decorator