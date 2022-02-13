from enum import Enum
from typing import Type

from pytz import timezone
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.schema import Column
from sqlalchemy.sql.sqltypes import DateTime, Integer
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy.orm import registry
from datetime import datetime

from util import cap_to_kebab, pluralize

tehran = timezone("Asia/Tehran")

mapper_registry = registry()

class Base(metaclass=DeclarativeMeta):
    __abstract__ = True

    # these are supplied by the sqlalchemy2-stubs, so may be omitted
    # when they are installed
    registry = mapper_registry
    metadata = mapper_registry.metadata

    __init__ = mapper_registry.constructor


class BaseMixin(object):
    """ Base class for all models
    This is used to define constant columns for all models as well as some ancillary functions
    """
    accepted_serialization_types = [str,dict,list,int,float,bool,datetime, type(None), Type[Enum]]
    dict_ignore: list = []
    col_ignore: list = []

    @declared_attr
    def __tablename__(cls):
        return pluralize(cap_to_kebab(cls.__name__)) # type: ignore # ignored __name__ error


    @declared_attr
    def id(cls):
        return None if 'id' in cls.col_ignore else Column(Integer, primary_key=True)

    @declared_attr
    def created_at(cls):
        return None if 'created_at' in cls.col_ignore else Column(DateTime, default=datetime.now(tehran))

    
    @declared_attr
    def updated_at(cls):
        return None if 'updated_at' in cls.col_ignore else Column(DateTime, default=datetime.now(tehran), onupdate=datetime.now(tehran))
    

    def to_dict(self):
        """ Reflects the attributes and values of current instance of model
            This class is used for declaration of base model for sqlalchemy models. It is directly referenced
            when initializing db in wsgi package
        """
        res = {}
        for key, value in self.__dict__.items():
            key_is_valid = not (key.startswith("__") or key.startswith("_") or key in self.dict_ignore)
            value_is_valid = type(value) in self.accepted_serialization_types
            if key_is_valid and value_is_valid:
                # if issubclass(type(value), Enum):
                #     value = {
                #         "name": value.name,
                #         "value": value.value
                #     }
                res[key] = value
        return res
