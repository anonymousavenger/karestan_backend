from datetime import datetime
import email
import re
from typing import Type
from sqlalchemy import Column

from .exceptions import ValidationException
from models.base_model import Base
from models.main_models import User
from wsgi import FlaskApp
from base_conf import BaseConfig

db_session = FlaskApp.db_session()


class Validators:
    @staticmethod
    def sql_model_id(x, model: Type[Base]):
        m_id = x
        if db_session.query(model).get(m_id) is None: # type: ignore
            return f"Entry with id={x} does not exist!"
        return None

    @staticmethod
    def in_mongo_collection(x: dict, collection_name: str):
        col = mongo_db.get_collection(collection_name)
        if col is None:
            raise Exception(f"Collection {collection_name} is not created in MongoDb")
        doc = col.find_one(filter=x)
        if doc is None:
            return f"Entry with {x} does not exist!"

    @staticmethod
    def datetime_format(x, datetime_format):
        try:
            datetime.strptime(x, datetime_format)
        except (TypeError, ValueError):
            return f"Invalid format. Expected {datetime_format}"
        return None

    @staticmethod
    def is_in(x, a_list: list):
        if x not in a_list:
            return f"Invalid argument. Must be one of the {a_list}"
        return None

    @staticmethod
    def digits(x, digits_number):
        if len(str(x)) != int(digits_number):
            return f"The number must have exactly {digits_number} digits"
        return None

    @staticmethod
    def ir_mobile(x):
        if re.compile(r"09\d{9}").match(x) is None:
            return f"Invalid mobile number format.Correct format must be: 09XXXXXXXXX"
        return None
    @staticmethod
    def is_unique(x, column:Column, model:Type[Base]):
        if db_session.query(model).filter(column == x).exists():
            return f"The value {x} exists in the column {column} of model {model}"
        return None
    @staticmethod
    def strong_pass(x):
        pass_regex = re.compile(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[#@_%?*!])[A-Za-z\d#@_%?*!]{8,}$")
        if pass_regex.match(x) is None:
            return f"The password must contain at least one lower and upper case, digit and special characters"\
                "(#@_%?*!)"
    @staticmethod
    def email(x):
        regex = re.compile(r"^([a-z1-9]+_?\.?[a-z1-9]+)@([a-z_-]{3,})\.([a-z]{2,6})$")
        if not regex.match(x):
            return "Invalid email address"
        return None        



class BaseParamsValidator:

    @classmethod
    def to_dict(cls):
        res = {}
        for key, value in cls.__dict__.items():
            if not (key.startswith("__") or key.startswith("_")):
                res[key] = value
        return res

    @staticmethod
    def parse_int_float(strx: str, type_class):
        if type(strx) != str:
            return None
        if type_class == int:
            match = re.compile(r"^\d+$").match(strx)
        elif type_class == float:
            match = re.compile(r"^\d+\.\d+$").match(strx)
        else:
            return None
        if match is None:
            return None
        return type_class(strx)

    @classmethod
    def validate(cls, inputs: dict):
        error_bag = {}
        sanitized_input = {}

        # noinspection PyBroadException
        def evaluate():
            errors = []
            if name not in inputs:
                if not optional:
                    errors.append("Missing required param")
                return errors

            val = inputs[name]
            if type(val) != type_class:
                # In GET requests we cant have int or float as values, but we can check whether the input (if string)
                # is numeric and if true, we can cast it to the required type
                parsed = cls.parse_int_float(val, type_class)
                if parsed is not None:
                    inputs[name] = val = parsed
                else:
                    errors.append(f"Invalid type. Expected {type_class}")
                    return errors

            for func in eval_funcs:
                msg = func(x=val)
                if msg:
                    errors.append(msg)
            return errors

        for name, value in cls.to_dict().items():

            optional = value["optional"]
            type_class = value["type"]
            eval_funcs = value["eval"] if "eval" in value else []

            errs = evaluate()
            if len(errs) > 0:
                error_bag[name] = errs
            else:
                if name in inputs.keys():
                    sanitized_input[name] = inputs[name]

        if len(error_bag) > 0:
            raise ValidationException(bag=error_bag)
        return sanitized_input


class CrawlParams(BaseParamsValidator):
    end_date = {
        "type": str,
        "optional": True,
        "eval": [
            lambda x: Validators.datetime_format(x, "%d-%m-%Y")
        ]
    }
    days_ago = {
        "type": int,
        "optional": False,
        "eval": [
            lambda x: "The value must be bigger than 0" if x < 1 else None
        ]
    }

class CreateUserParams(BaseParamsValidator):
    user_namme = {
        "type": str,
        "optional": False,
        "eval": [
            lambda x: Validators.is_unique(x, User.name, User),
            lambda x: "The length of user name must be bigger than 5" if len(x) < 5 else None
        ]
    }
    password = {
        "type": str,
        "optional": False,
        "eval": [
            lambda x: Validators.strong_pass(x),
            lambda x: "The length of pasword must be bigger than 8" if len(x) < 8 else None
        ]
    }

    email = {
        "type": str,
        "optional": False,
        "eval": [
            lambda x: Validators.email(x),
        ]
    }


class PricesParams(BaseParamsValidator):
    end_date = {
        "type": str,
        "optional": True,
        "eval": [
            lambda x: Validators.datetime_format(x, "%d-%m-%Y")
        ]
    }
    days_ago = {
        "type": int,
        "optional": False,
        "eval": [
            lambda x: "The value must be bigger than 0" if x < 1 else None
        ]
    }
    commodity = {
        "type": str,
        "optional": False,
        "eval": [
            lambda x: Validators.in_mongo_collection({"name": x}, BaseConfig.COMMODITY_COLLECTION_NAME)
        ]
    }


class PeriodicPricesParams(BaseParamsValidator):
    frequency = {
        "type": str,
        "optional": False,
        "eval": [
            lambda x: Validators.is_in(x, a_list=["daily", "weekly", "monthly"])
        ]
    }
    commodity = {
        "type": str,
        "optional": False,
        "eval": [
            lambda x: Validators.in_mongo_collection({"name": x}, BaseConfig.COMMODITY_COLLECTION_NAME)
        ]
    }
    tolerance = {
        "type": int,
        "optional": True,
        "eval": [
            lambda x: "The value must be bigger than 0" if x < 1 else None
        ]
    }
