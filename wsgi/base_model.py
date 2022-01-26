from enum import Enum

from flask_sqlalchemy import Model
from pytz import timezone
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import declarative_mixin
from sqlalchemy.schema import Column
from sqlalchemy.sql.sqltypes import DateTime, Integer
from datetime import datetime

tehran = timezone("Asia/Tehran")


@declarative_mixin
class IModel:
    has_id: bool = True
    has_created_at: bool = True
    has_updated_at: bool = True
    dict_ignore: list = []

    def to_dict(self):
        """ Reflects the attributes and values of current instance of model
            This class is used for declaration of base model for sqlalchemy models. It is directly referenced
            when initializing db in wsgi package
        """
        res = {}
        for key, value in self.__dict__.items():
            if not (key.startswith("__") or key.startswith("_") or key in self.dict_ignore):
                if issubclass(type(value), Enum):
                    value = {
                        "name": value.name,
                        "value": value.value
                    }
                res[key] = value
        return res


class BaseModel(IModel, Model):
    """ Base class for all models
    This is used to define constant columns for all models as well as some ancillary functions
    """

    @declared_attr
    def id(self):
        return Column(Integer, primary_key=True) if self.has_id else None

    @declared_attr
    def created_at(self):
        return Column(DateTime, default=datetime.now(tehran)) if self.has_created_at else None

    @declared_attr
    def updated_at(self):
        return Column(DateTime, default=datetime.now(tehran), onupdate=datetime.now(tehran)) \
            if self.has_updated_at else None
