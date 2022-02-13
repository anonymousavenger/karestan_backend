from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import Dict, Iterable, List, Literal, Tuple, Type, Callable
from sqlalchemy import Column

from .exceptions import ValidationException
from models.base_model import Base
from models.main_models import City, Company, User, UserType
from wsgi import FlaskApp
from controllers.auth import get_current_user

db_session = FlaskApp.db_session()

@dataclass
class ValidatorField():
    field_type: Type
    eval: Dict[str,Callable]
    optional: bool = field(default_factory= lambda: False)
    ignore: bool = field(default_factory= lambda: False)

    def __post_init__(self):
        if self.field_type not in [str, int, float, bool, dict]:
            raise Exception("Field type must be one of the following: str, int, float, bool, dict")

class Validators:
    @staticmethod
    def sql_model_id(x, model: Type[Base]):
        m_id = x
        if db_session.query(model).get(m_id) is None: # type: ignore
            return f"Entry with id={x} does not exist!"
        return None

    # @staticmethod
    # def in_mongo_collection(x: dict, collection_name: str):
    #     col = mongo_db.get_collection(collection_name)
    #     if col is None:
    #         raise Exception(f"Collection {collection_name} is not created in MongoDb")
    #     doc = col.find_one(filter=x)
    #     if doc is None:
    #         return f"Entry with {x} does not exist!"

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
    def digits_length(x, digits_number):
        if len(str(x)) != int(digits_number):
            return f"The number must have exactly {digits_number} digits"
        return None

    @staticmethod
    def ir_mobile(x):
        if re.compile(r"09\d{9}").match(x) is None:
            return f"Invalid mobile number format.Correct format must be: 09XXXXXXXXX"
        return None
    @staticmethod
    def is_unique(x, column:Column, model:Type[Base], except_id = 0):
        count = db_session.query(model).filter(column == x).filter(model.id != except_id).count() # type: ignore # ignore warning of not existing id in Base (model)
        if count > 0:
            return f"The value {x} exists in the column '{column.name}' of table '{model.__tablename__}'" # type: ignore # ignoring __tablename__ error
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

    @staticmethod
    def fa_text(x):
        regex = re.compile(r"^[۱-۹آ-ی\s\d]+$")
        if not regex.match(x):
            return "Text must only contain farsi letters, digits, space and english digits"
        return None

    @staticmethod
    def en_text(x):
        regex = re.compile(r"^[A-Za-z\s\d\-.]+$")
        if not regex.match(x):
            return "Text must only contain english letters, digits, space and dash"
        return None

    @staticmethod
    def int_text(x):
        if not re.match(r"^\d+$",x):
            return "Text must only contain integers"
        return None

    @staticmethod
    def float_text(x):
        if not re.match(r"^\d*\.\d+$",x):
            return "Text must only contain floating point numbers"
        return None

    @staticmethod
    def website(x):
        regex =  re.compile(r"^(www\.)?[a-z\d_]{3,}\.[a-z]{2,6}$")
        if not regex.match(x):
            return "Invalid website address"
        return None

class BaseParamsValidator:

    inputs: dict

    def __init__(self, **kwargs) -> None:
        self.inputs = kwargs

    def get_fields(self) -> Iterable[Tuple[str, ValidatorField]]:
        for key, value in self.__dict__.items():
            if type(value) == ValidatorField:
                yield key, value

    def inputs_check(self):
        if len(self.inputs) < 1:
            raise ValidationException(bag={}, message="Payload cannot be empty")

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

    def validate(self):
        self.inputs_check()
        error_bag = {}
        sanitized_input = {}

        # noinspection PyBroadException
        def evaluate(name:str, value: ValidatorField):
            errors = []
            if name not in self.inputs:
                if not value.optional:
                    errors.append("Missing required param")
                return errors

            val = self.inputs[name]
            if type(val) != value.field_type:
                # In GET requests we cant have int or float as values, but we can check whether the input (if string)
                # is numeric and if true, we can cast it to the required type
                parsed = self.parse_int_float(val, value.field_type)
                if parsed is not None:
                    self.inputs[name] = val = parsed
                else:
                    errors.append(f"Invalid type. Expected {value.field_type}")
                    return errors

            for name,func in value.eval.items():
                msg = func(x=val)
                if msg:
                    errors.append(msg)
            return errors

        for name, value in self.get_fields():

            if value.ignore:
                continue

            errs = evaluate(name, value)
            if len(errs) > 0:
                error_bag[name] = errs
            else:
                if name in self.inputs.keys():
                    sanitized_input[name] = self.inputs[name]

        if len(error_bag) > 0:
            raise ValidationException(bag=error_bag)
        return sanitized_input

class CreateUser(BaseParamsValidator):

    user_name: ValidatorField
    password: ValidatorField
    email: ValidatorField
    user_type: ValidatorField

    def __init__(self,**kwargs) -> None:
        super().__init__(**kwargs)
        self.user_name = ValidatorField(
            field_type=str,
            optional=False,
            eval= {
                "lower_case": lambda x: None if re.match(r"[a-z\d]+_?[a-z\d]+",x) else "User name must only contain lower case letters, numbers and underline",
                "unique": lambda x: Validators.is_unique(x, User.name, User),
                "bigger": lambda x: "The length of user name must be bigger than 5" if len(x) < 5 else None
            })
        self.password = ValidatorField(
            field_type = str,
            optional = False,
            eval = {
                "strong_pass": lambda x: Validators.strong_pass(x),
                "bigger": lambda x: "The length of pasword must be bigger than 8" if len(x) < 8 else None,
                "smaller": lambda x: "The length of pasword can't be bigger than 32" if len(x) > 32 else None
            }
        )

        self.email = ValidatorField(
            field_type = str,
            optional = False,
            eval = {
                "format": lambda x: Validators.email(x),
                "unique": lambda x: Validators.is_unique(x, User.email, User),
            }
        )

        self.user_type = ValidatorField(
            field_type = str,
            optional = False,
            eval = {
                "in": lambda x: Validators.is_in(x, [UserType.employee.name, UserType.manager.name]),
            }
        )

class EditUser(CreateUser):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.user_name.optional = True
        self.user_name.eval["unique"] = lambda x: Validators.is_unique(x, User.name, User, get_current_user().id)
        self.password.optional = True
        self.email.optional = True
        self.email.eval["unique"] = lambda x: Validators.is_unique(x, User.email, User, get_current_user().id)
        self.user_type.ignore = True


class CreateCompany(BaseParamsValidator):
    fa_name: ValidatorField
    en_name: ValidatorField
    email: ValidatorField
    website: ValidatorField
    national_id: ValidatorField
    city_id: ValidatorField
    phone: ValidatorField

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.fa_name = ValidatorField(
            field_type =  str,
            optional =  False,
            eval =  {
                "fa": lambda x: Validators.fa_text(x),
                "bigger": lambda x: "The length of company name must be bigger than 4" if len(x) < 4 else None,
                "smaller": lambda x: "The length of company name can't be bigger than 32" if len(x) > 32 else None,
                "unique": lambda x: Validators.is_unique(x, Company.fa_name, Company),
            }
        )

        self.en_name = ValidatorField(
            field_type =  str,
            optional =  False,
            eval =  {
                "en": lambda x: Validators.en_text(x),
                "bigger": lambda x: "The length of company name must be bigger than 4" if len(x) < 4 else None,
                "smaller": lambda x: "The length of company name can't be bigger than 32" if len(x) > 32 else None,
                "unique": lambda x: Validators.is_unique(x, Company.en_name, Company),
            }
        )

        self.email = ValidatorField(
            field_type =  str,
            optional =  False,
            eval =  {
                "format": lambda x: Validators.email(x),
                "unique": lambda x: Validators.is_unique(x, Company.email, Company),
                "length": lambda x: "Email length can't be more than 60 chars" if len(x) > 60 else None
            }
        )

        self.national_id = ValidatorField(
            field_type =  str,
            optional =  False,
            eval =  {
                "is_numeric": lambda x: Validators.int_text(x),
                "length": lambda x: Validators.digits_length(x, 11),
                "unique": lambda x: Validators.is_unique(x, Company.national_id, Company)
            }
        )

        # self.score = ValidatorField(
        #     field_type =  int,
        #     optional =  False,
        #     eval =  {
        #         "length": lambda x: Validators.digits_length(x, 1),
        #         "between": lambda x: "The score must be btween 0 and 10" if x < 0 or x > 10 else None
        #     }
        # )

        self.city_id = ValidatorField(
            field_type =  int,
            optional =  False,
            eval =  {
                "has_id": lambda x: Validators.sql_model_id(x, City)
            }
        )
        self.website = ValidatorField(
            field_type =  str,
            optional =  False,
            eval =  {
                "format": lambda x: Validators.website(x),
                "unique": lambda x: Validators.is_unique(x, Company.website, Company),
                "length": lambda x: "Website length can't be more than 60 chars" if len(x) > 60 else None
            }
        )

        self.phone = ValidatorField(
            field_type =  str,
            optional =  False,
            eval =  {
                "format": lambda x: Validators.int_text(x),
                "unique": lambda x: Validators.is_unique(x, Company.phone, Company),
                "length": lambda x: "Phone length can't be more than 15 chars" if len(x) > 15 else None,
                "no_zero": lambda x: "Phone number must not start with zero" if x[0] == '0' else None
            }
        )

class EditCompany(CreateCompany):
    company_id: ValidatorField
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.company_id = ValidatorField(
            field_type=int,
            optional= False,
            eval={
                "has_id": lambda x: Validators.sql_model_id(x, Company)
            }
        )
        self.city_id.optional = True
        self.email.optional = True
        self.fa_name.optional = True
        self.en_name.optional = True
        self.national_id.optional = True
        self.website.optional = True
        self.phone.optional = True
    
    def inputs_check(self):
        if len(self.inputs) < 2 or "company_id" not in self.inputs:
            raise ValidationException(bag={}, message="Payload must contain the field company_id and at least one other field to edit")

class GetCompany(BaseParamsValidator):
    company_id: ValidatorField
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.company_id = ValidatorField(
            field_type=int,
            optional= False,
            eval={
                "has_id": lambda x: Validators.sql_model_id(x, Company)
            }
        )