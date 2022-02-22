from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
from typing import Dict, Iterable, Literal, Optional, Tuple, Type, Callable, Any
from sqlalchemy import Column

from .exceptions import ValidationException
from models.base_model import Base
from models.main_models import City, Company, FeedbackType, Interview, InterviewResult, Review, User, UserType
from wsgi import FlaskApp
from controllers.auth import get_current_user

db_session = FlaskApp.db_session()

# In GET requests we cant have int or float as values, but we can check whether the input (if string)
                # is numeric and if true, we can cast it to the required type
def parse_int_float(strx, type_class):
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

def convert_to_feedback_type(route_name):
    if route_name == 'interviews':
        return FeedbackType.interview
    elif route_name == 'reviews':
        return FeedbackType.review
    else:
        return None
    
@dataclass
class ValidatorField():
    field_type: Type
    eval: Dict[str,Callable] = field(default_factory= lambda: {})
    optional: bool = field(default_factory= lambda: False)
    ignore: bool = field(default_factory= lambda: False)
    converter: Optional[Callable] = field(default_factory= lambda: None)

    def __post_init__(self):
        if self.field_type in [int, float] and self.converter is None:
            self.converter = lambda x: parse_int_float(x,self.field_type)
        self.check_type_and_subclass()
            
    def check_type_and_subclass(self):
        accepted_primitives = [str, int, float, bool, dict]
        accepted_classes = [Enum]
        if not self.__check_type(self.field_type, accepted_primitives) or not self.__check_subclass(self.field_type, accepted_classes):
            raise Exception(f"Field type of {self.field_type} must be one of the following:\
                {accepted_primitives + accepted_classes}")
        
    @staticmethod
    def __check_type(field_type, accepted_types):
        return field_type in accepted_types

    @staticmethod
    def __check_subclass(field_type, accepted_classes:list):
        for f_type in accepted_classes:
            if issubclass(field_type, f_type):
                return True
        return False

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
    def is_unique(x, main_column:Column, model:Type[Base], except_id = 0, filters: Optional[Dict[Column, Any]] = None):
        q = db_session.query(model)
        q = q.filter(main_column == x)
        q = q.filter(model.id != except_id) # type: ignore # ignore warning of not existing id in Base (model)
        if filters is not None:
            for col,val in filters.items():
                q = q.filter(col == val)
        if q.count() > 0:
            return f"The value {x} exists in the column '{main_column.name}' of table '{model.__tablename__}'" # type: ignore # ignoring __tablename__ error
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

    @staticmethod
    def date_compare(x,format:str ,date:str = "Now", order: Literal['before','after'] = 'before'):
        x_date = datetime.strptime(x,format)
        if date != "Now":
            y_date = datetime.strptime(date,format)
        else:
            y_date = datetime.now()
            
        if order == "before" and x_date > y_date:
            return f"Date must be before {date}"
        if order == "after" and x_date < y_date:
            return f"Date must be after {date}"
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

    def validate(self):
        self.inputs_check()
        error_bag = {}
        sanitized_input = {}

        # noinspection PyBroadException
        def evaluate(name:str, value: ValidatorField):
            if name not in self.inputs:
                if not value.optional:
                    return ["Missing required param"]
                return []
 
            val = self.inputs[name]
            converted = None

            if value.converter is not None:
                try:
                    converted = value.converter(value=val)
                except:
                    return ["Field conversion error"]
                if converted is not None:
                    self.inputs[name] = val = converted

            if type(val) != value.field_type and (converted is None or type(converted) != value.field_type):
                return [f"Invalid type. Expected {value.field_type}"]

            errors = []
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

class Login(BaseParamsValidator):

    password: ValidatorField
    email: ValidatorField

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.password = ValidatorField(
            field_type = str,
            optional = False,
        )

        self.email = ValidatorField(
            field_type = str,
            optional = False,
            eval = {
                "format": lambda x: Validators.email(x),
            }
        )

class CreateUser(BaseParamsValidator):

    name: ValidatorField
    password: ValidatorField
    email: ValidatorField
    user_type: ValidatorField

    def __init__(self,**kwargs) -> None:
        super().__init__(**kwargs)
        self.name = ValidatorField(
            field_type=str,
            optional=False,
            eval= {
                "lower_case": lambda x: None if re.match(r"[a-z\d]+_?[a-z\d]+",x) else "User name must only contain lower case letters, numbers and underline",
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
        self.name.optional = True
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

class GetFeedbacks(BaseParamsValidator):
    company_id: ValidatorField
    user_id: ValidatorField
    feedback_type: ValidatorField
    offset: ValidatorField
    limit: ValidatorField

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.company_id = ValidatorField(
            field_type=int,
            optional= False,
            eval={
                "has_id": lambda x: Validators.sql_model_id(x, Company)
            }
        )

        self.user_id = ValidatorField(
            field_type=int,
            optional= True,
            eval={
                "has_id": lambda x: Validators.sql_model_id(x, User)
            },
            ignore=True
        )

        self.feedback_type = ValidatorField(
            field_type=FeedbackType,
            optional= True,
            eval={
                "in": lambda x: Validators.is_in(x,list(FeedbackType.__members__.values()))
            },
            converter= convert_to_feedback_type
        )

        self.offset  = ValidatorField(
            field_type=int,
            optional= True,
            eval={
                "bigger": lambda x: "The offset value must be bigger than one" if x < 1 else None
            }            
        )

        self.limit = ValidatorField(
            field_type=int,
            optional= True,
            eval={
                "bigger": lambda x: "The limit value must be bigger than zero" if x < 0 else None
            }            
        )

class RegisterFeedback(BaseParamsValidator):
    title : ValidatorField
    body : ValidatorField
    job_title : ValidatorField
    score : ValidatorField
    salary : ValidatorField
    type : ValidatorField
    company_id: ValidatorField
    details : ValidatorField

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.title = ValidatorField(
            field_type=str,
            optional= False,
            eval={
                "bigger": lambda x: "The length of job title must be bigger than 4" if len(x) < 4 else None,
                "smaller": lambda x: "The length of job title can't be bigger than 32" if len(x) > 32 else None,
            }            
        )
        self.body = ValidatorField(
            field_type=str,
            optional= False,
            eval={
                "bigger": lambda x: "The length of feedback must be bigger than 20" if len(x) < 20 else None,
                "smaller": lambda x: "The length of feedback can't be bigger than 2000" if len(x) > 2000 else None,
            }                  
        )
        self.job_title = ValidatorField(
            field_type=str,
            optional= False,
            eval={
                "bigger": lambda x: "The length of job title must be bigger than 4" if len(x) < 4 else None,
                "smaller": lambda x: "The length of job title can't be bigger than 32" if len(x) > 32 else None,
            }            
        )
        self.score = ValidatorField(
            field_type =  int,
            optional =  False,
            eval =  {
                "between": lambda x: "The score must be btween 0 and 10" if x < 0 or x > 10 else None
            }
        )
        self.salary = ValidatorField(
            field_type=str,
            optional= False,
            eval={
                "is_int": lambda x: Validators.int_text(x),
                "order": lambda x: lambda x: "The salary must be btween 1 and 99 million tomans" if x < 1 or x > 99 else None
            }            
        )
        self.type = ValidatorField(
            field_type=FeedbackType,
            optional= False,
            eval={
                "in": lambda x: Validators.is_in(x,list(FeedbackType.__members__.values()))
            },
            converter= convert_to_feedback_type            
        )
        self.company_id = ValidatorField(
            field_type=int,
            optional= False,
            eval={
                "has_id": lambda x: Validators.sql_model_id(x, Company)
            }
        )

        self.details = ValidatorField(
            field_type=dict,
            optional= False,
            eval={
                "keys_in": lambda x: Validators.is_in(x.items().keys(),['some_key'])
            }
        )

class RegisterReview(RegisterFeedback):
    start_ts : ValidatorField
    end_ts : ValidatorField

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # message = "User has already reviewed this company"
        # user_reviewed = lambda x: Validators.is_unique(x, main_column=Review.company_id, model=Review, filters= {Review.user_id: self.inputs['user_id']})
        # self.company_id.eval["user_reviewed"] = lambda x: message if user_reviewed(x) is not None else None
        self.type.ignore = True
        date_fmt = "%d-%m-%Y"
        self.start_ts = ValidatorField(
            field_type=datetime,
            optional= False,
            eval={
                "format": lambda x: Validators.datetime_format(x,date_fmt),
                "before_now": lambda x: Validators.date_compare(x,format= date_fmt, date="Now", order='before')
            },
            converter= lambda x: datetime.strptime(x,date_fmt)
        )

        self.end_ts = ValidatorField(
            field_type=datetime,
            optional= True, # If false is given, thye are still employed
            eval={
                "format": lambda x: Validators.datetime_format(x,date_fmt),
                "before_now": lambda x: Validators.date_compare(x,format= date_fmt, date="Now", order='before'),
                "after_start": lambda x: Validators.date_compare(x,format= date_fmt, date=self.inputs['start_ts'], order='after')
            },
            converter= lambda x: datetime.strptime(x,date_fmt)
        )

class RegisterInterview(RegisterFeedback):
    int_ts : ValidatorField
    expected_salary : ValidatorField
    result : ValidatorField

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        def convert_to_interview_result(result:str):
            try:
                return InterviewResult[result]
            except:
                return None

        # message = "User has already registered an interview for this company"
        # user_reviewed = lambda x: Validators.is_unique(x, main_column=Interview.company_id, model=Interview, filters= {Interview.user_id: self.inputs['user_id']})
        # self.company_id.eval["user_interviewed"] = lambda x: message if user_reviewed(x) is not None else None
        self.type.ignore = True
        date_fmt = "%d-%m-%Y"
        self.int_ts = ValidatorField(
            field_type=datetime,
            optional= False,
            eval={
                "format": lambda x: Validators.datetime_format(x,date_fmt),
                "before_now": lambda x: Validators.date_compare(x,format= date_fmt, date="Now", order='before')
            },
            converter= lambda x: datetime.strptime(x,date_fmt)
        )

        self.expected_salary = self.salary # The expected_salary validator is the same as salary

        self.result = ValidatorField(
            field_type=FeedbackType,
            optional= False,
            eval={
                "in": lambda x: Validators.is_in(x,list(InterviewResult.__members__.values()))
            },
            converter= convert_to_interview_result   
        )