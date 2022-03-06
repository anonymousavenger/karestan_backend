from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
from typing import Dict, Iterable, Literal, Optional, Tuple, Type, Callable, Any, Union 
from sqlalchemy import Column

from .exceptions import InternalException, ValidationException
from models.base_model import Base
from models.main_models import City, Company, FeedbackType, Interview, InterviewResult, Review, User, UserType
from wsgi import FlaskApp
from controllers.auth import get_current_user



db_session = FlaskApp.db_session()

# In GET requests we cant have int or float as values, but we can check whether the input (if string)
                # is numeric and if true, we can cast it to the required type
def parse_int_float(strx, type_class):
    if type(strx) != str:
        return strx
    if type_class == int:
        match = re.compile(r"^\d+$").match(strx)
    elif type_class == float:
        match = re.compile(r"^\d+\.\d+$").match(strx)
    else:
        raise InternalException(error=f"{__name__} conversion function, invalid type supplied")
    if match is None:
        raise InternalException(error=f"Cannot convert {strx} to type {type_class}")
    return type_class(strx)

def convert_to_feedback_type(route_name):
    if route_name == 'interviews':
        return FeedbackType.interview
    elif route_name == 'reviews':
        return FeedbackType.review
    else:
        raise InternalException(error="Invalid feedback type provided")

def convert_to_datetime(date:str,format:str):
    try:
        return datetime.strptime(date,format)
    except (ValueError, TypeError) as e:
        raise InternalException(error=e.args[0])

def remove_bad_persian_letters(strx:str) -> str:
    bad_reg = re.compile(r"[ؤئًٌٍَِّْ»ة»ءٰٔٓأأإأ\u200f]")
    s = bad_reg.sub("",strx)
    s = re.sub(r"[\u200c]"," ",s)
    return s

def remove_inside_parantheses(strx:str) -> str:
    reg1 = re.compile(r"\s*\(.*\)")
    reg2 = re.compile(r"\s*\(.*\(")
    reg3 = re.compile(r"\s*\).*\)")
    s = reg1.sub("",strx)
    s = reg2.sub("",s)
    s = reg3.sub("",s)
    return s

def create_dir_name(strx:str):
    s = strx.lower()
    s = re.sub(r"[\s\-]","_",s)
    s = re.sub(r"[\\\/\r\+@^&%$#!]","",s)
    return s
    
def create_en_name(strx:str):
    s = re.sub(r"[\-\_]"," ",strx)
    s = re.sub(r"[\\\/\r\+@^&%$#!]","",s)
    s = re.sub(r"\s{2,}"," ",s)
    s = s.split(" ")
    s = " ".join([st.capitalize() for st in s])
    return s
    
@dataclass
class ModelField():
    field_type: Type
    eval: Dict[str,Callable] = field(default_factory= lambda: {})
    optional: bool = field(default_factory= lambda: False)
    ignore: bool = field(default_factory= lambda: False)
    preconverter: Optional[Callable] = field(default_factory= lambda: None)
    postconverter: Optional[Callable] = field(default_factory= lambda: None)

    def __post_init__(self):
        if self.field_type in [int, float] and self.preconverter is None:
            self.preconverter = lambda x: parse_int_float(x,self.field_type)
        self.check_type_and_subclass()
            
    def check_type_and_subclass(self):
        accepted_primitives = [str, int, float, bool, dict, datetime]
        accepted_classes = [Enum, BaseParamsSchema]
        if not self.__check_type(self.field_type, accepted_primitives) and not self.__check_subclass(self.field_type, accepted_classes):
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
        regex = re.compile(r"^[۱-۹آ-ی\s\d\.]+$")
        if not regex.match(x):
            return "Text must only contain farsi letters, digits, space and english digits"
        return None

    @staticmethod
    def fa_company_name(x):
        regex = re.compile(r"^[۱-۹آ-ی\s\d\.\-\*,،]+$")
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
    def en_company_name(x):
        regex = re.compile(r"^[A-Za-z\s\d\-.&!',@]+$")
        if not regex.match(x):
            return "Text must only contain english letters, digits, space and dash"
        return None

    @staticmethod
    def en_dirname(x):
        regex = re.compile(r"^[a-z\d\_]+$")
        if not regex.match(x):
            return "Text must only contain lowercase, digits and/or underline"
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
        # Up to 3 long subdomains are supported e.g. www.shitless.someone.co.ir
        regex =  re.compile(r"^(www\.)?[a-z\d_]{3,}(\.[a-z]{2,10}){0,3}\.[a-z]{2,6}$")
        if not regex.match(x):
            return "Invalid website address"
        return None

    @staticmethod
    def date_compare(x_date:Union[datetime,int,float],format:Optional[str] = None ,date:Optional[Union[str,datetime]] = None, order: Literal['before','after'] = 'before'):
        if date is not None:
            if type(date) == str:
                if format is None:
                    raise Exception("'format' can't be None for a text date")
                try:
                    y_date:datetime = datetime.strptime(date,format) # type: ignore 
                except ValueError as e:
                    return f"Error in date conversion for comparison: {e.args[0]}"
            elif type(date) == datetime:
                y_date = date # type: ignore # Complains about str|datetime incompatibility that is illogical because I already put the condition
            else:
                raise Exception("Incorrect date form supplied for comparison")
        else:
            y_date = datetime.now()
            date = "Now"
        if type(x_date) in [int,float]:
            x_date = datetime.fromtimestamp(x_date) # type: ignore
            
        if order == "before" and x_date > y_date:
            return f"Date must be before {date}"
        if order == "after" and x_date < y_date:
            return f"Date must be after {date}"
        return None

class BaseParamsSchema:

    inputs: dict
    error_bag: dict = {}
    has_errors: Optional[bool] = None
    sanitized: dict = {}
    only_optional_errors_exist:bool = True
    children: dict = {} # If we have nested structures, we'll save their validator instances here
    level:int = 1 # This is used to count how many depth levels we can go
    MAX_LEVEL = 2 # Maximum depth level

    def __init__(self, **kwargs) -> None:
        self.inputs = kwargs
        self.children = {}
        self.has_errors = None
        self.only_optional_errors_exist = True

    def get_fields(self) -> Iterable[Tuple[str, ModelField]]:
        for key, value in self.__dict__.items():
            if type(value) == ModelField:
                yield key, value

    def inputs_check(self):
        if len(self.inputs) < 1:
            raise ValidationException(message="Payload cannot be empty")

    def __check_presence(self, name:str, field: ModelField):
        """Check if required and present"""
        if name not in self.inputs and not field.optional:
            raise InternalException(error = {"_required":"Missing required param"})

    def __get_or_preconvert(self, name:str, field: ModelField):
        """Get value and if it has converter, return the converted value. Otherwise, return the original value"""
        val = self.inputs.get(name)
        if val is not None and field.preconverter is not None:
            try:
                return field.preconverter(val)
            except InternalException as e:
                raise InternalException(error={"_preconversion":f"{e.error}"})
        else:
            return val

    def __check_nested(self, name:str, inp:dict, field:ModelField):
        if not issubclass(field.field_type, BaseParamsSchema):
            return None
        if type(inp) != dict:
            raise InternalException(error="Params supplied for nested must be dict")
        if self.level > self.MAX_LEVEL:
            raise InternalException({"_depth":"Maximum depth level reached for nested values"})
        instance = field.field_type(**inp)
        instance.level = self.level + 1
        val_instance = instance.check()
        self.children[name] = val_instance
        if val_instance.only_optional_errors_exist:
            return val_instance.sanitized
        else:
            raise InternalException(error=val_instance.error_bag)

    @staticmethod
    def __type_check(value, field:ModelField):
        """Check the type of the original or converted value"""
        if type(value) != field.field_type:
                raise InternalException(error={"_type":f"Invalid type. Expected {field.field_type}"})
        return None

    @staticmethod
    def __perform_evaluations(value, field:ModelField):
        """Perform the evaluations that are defined in 'eval' """
        errors = {}
        for func_name,func in field.eval.items():
            try:
                msg = func(x=value)
            except Exception as e:
                msg = e.args[0]
            if msg is not None:
                errors[func_name] = msg
        if len(errors) > 0:
            raise InternalException(error=errors)

    @staticmethod
    def __postconvert(value, field: ModelField):
        if value is not None and field.postconverter is not None:
            try:
                return field.postconverter(value)
            except InternalException as e:
                raise InternalException(error={"_postconversion":f"{e.error}"})
        return value

    def check(self):
        self.inputs_check()
        error_bag = {}
        sanitized_input = {}
        only_optional = True

        for name, field in self.get_fields():
            if field.ignore:
                continue
            try:
                self.__check_presence(name,field)
                value  = self.__get_or_preconvert(name, field)
                if value is None:
                    continue
                sanitized_nested = self.__check_nested(name, value, field)
                if sanitized_nested is None:
                    self.__type_check(value, field)
                    self.__perform_evaluations(value, field)
                    value = self.__postconvert(value, field)
                    self.__type_check(value,field)
                    if value is None:
                        continue
                else:
                    value = sanitized_nested
            except InternalException as e:
                # TODO Nested only_optional_errors must be added. ony optinals must be checked recursively
                error_bag[name] = e.error
                if not field.optional:
                    only_optional = False
                continue
            sanitized_input[name] = value
        
        
        self.sanitized = sanitized_input
        self.only_optional_errors_exist = only_optional

        if len(error_bag) > 0:
            self.error_bag = error_bag
            self.has_errors = True
        else:
            self.has_errors = False
        return self

    def validate(self):
        if self.has_errors is None: # if has_errors is None, that would indicate that checking process is not started
            self.check()

        if self.has_errors:
            raise ValidationException(error_bag=self.error_bag)
        return self.sanitized

class Login(BaseParamsSchema):

    password: ModelField
    email: ModelField

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.password = ModelField(
            field_type = str,
            optional = False,
        )

        self.email = ModelField(
            field_type = str,
            optional = False,
            eval = {
                "_format": lambda x: Validators.email(x),
            }
        )

class CreateUser(BaseParamsSchema):

    name: ModelField
    password: ModelField
    email: ModelField
    user_type: ModelField

    def __init__(self,**kwargs) -> None:
        super().__init__(**kwargs)
        self.name = ModelField(
            field_type=str,
            optional=False,
            eval= {
                "_lower_case": lambda x: None if re.match(r"[a-z\d]+_?[a-z\d]+",x) else "User name must only contain lower case letters, numbers and underline",
                "_bigger": lambda x: "The length of user name must be bigger than 5" if len(x) < 5 else None
            })
        self.password = ModelField(
            field_type = str,
            optional = False,
            eval = {
                "_strong_pass": lambda x: Validators.strong_pass(x),
                "_bigger": lambda x: "The length of pasword must be bigger than 8" if len(x) < 8 else None,
                "_smaller": lambda x: "The length of pasword can't be bigger than 32" if len(x) > 32 else None
            }
        )

        self.email = ModelField(
            field_type = str,
            optional = False,
            eval = {
                "_format": lambda x: Validators.email(x),
                "_unique": lambda x: Validators.is_unique(x, User.email, User),
            }
        )

        self.user_type = ModelField(
            field_type = str,
            optional = False,
            eval = {
                "_in": lambda x: Validators.is_in(x, [UserType.employee.name, UserType.manager.name]),
            }
        )

class EditUser(CreateUser):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.name.optional = True
        self.password.optional = True
        self.email.optional = True
        self.email.eval["_unique"] = lambda x: Validators.is_unique(x, User.email, User, get_current_user().id) # type: ignore
        self.user_type.ignore = True


class CreateCompany(BaseParamsSchema):
    fa_name: ModelField
    en_name: ModelField
    email: ModelField
    website: ModelField
    national_id: ModelField
    city_id: ModelField
    phone: ModelField
    brand_name: ModelField

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.fa_name = ModelField(
            field_type =  str,
            optional =  False,
            eval =  {
                "_fa": lambda x: Validators.fa_company_name(x),
                "_bigger": lambda x: "The length of company name must be bigger than 4" if len(x) < 4 else None,
                "_smaller": lambda x: "The length of company name can't be bigger than 70" if len(x) > 70 else None,
                "_unique": lambda x: Validators.is_unique(x, Company.fa_name, Company),
            }
        )

        self.en_name = ModelField(
            field_type =  str,
            optional =  False,
            eval =  {
                "_en": lambda x: Validators.en_company_name(x),
                "_bigger": lambda x: "The length of company name must be bigger than 4" if len(x) < 4 else None,
                "_smaller": lambda x: "The length of company name can't be bigger than 60" if len(x) > 60 else None,
                "_unique": lambda x: Validators.is_unique(x, Company.en_name, Company),
            }
        )

        self.email = ModelField(
            field_type =  str,
            optional =  False,
            eval =  {
                "_format": lambda x: Validators.email(x),
                "_unique": lambda x: Validators.is_unique(x, Company.email, Company),
                "_length": lambda x: "Email length can't be more than 60 chars" if len(x) > 60 else None
            }
        )

        self.national_id = ModelField(
            field_type =  str,
            optional =  False,
            eval =  {
                "_is_numeric": lambda x: Validators.int_text(x),
                "_length": lambda x: Validators.digits_length(x, 11),
                "_unique": lambda x: Validators.is_unique(x, Company.national_id, Company)
            }
        )

        # self.score = ValidatorField(
        #     field_type =  int,
        #     optional =  False,
        #     eval =  {
        #         "_length": lambda x: Validators.digits_length(x, 1),
        #         "_between": lambda x: "The score must be btween 0 and 10" if x < 0 or x > 10 else None
        #     }
        # )

        self.city_id = ModelField(
            field_type =  int,
            optional =  False,
            eval =  {
                "_has_id": lambda x: Validators.sql_model_id(x, City)
            }
        )
        self.website = ModelField(
            field_type =  str,
            optional =  False,
            eval =  {
                "_format": lambda x: Validators.website(x),
                "_unique": lambda x: Validators.is_unique(x, Company.website, Company),
                "_length": lambda x: "Website length can't be more than 60 chars" if len(x) > 60 else None
            }
        )

        self.phone = ModelField(
            field_type =  str,
            optional =  False,
            eval =  {
                "_format": lambda x: Validators.int_text(x),
                "_unique": lambda x: Validators.is_unique(x, Company.phone, Company),
                "_length": lambda x: "Phone length can't be more than 15 chars" if len(x) > 15 else None,
                "_no_zero": lambda x: "Phone number must not start with zero" if x[0] == '0' else None
            }
        )

        self.brand_name = ModelField(
            field_type =  str,
            optional =  True,
            eval =  {
                "_fa": lambda x: Validators.fa_company_name(x),
                "_bigger": lambda x: "The length of company name must be bigger than 4" if len(x) < 4 else None,
                "_smaller": lambda x: "The length of company name can't be bigger than 10" if len(x) > 10 else None,
                "_unique": lambda x: Validators.is_unique(x, Company.fa_name, Company),
            }
        )

class EditCompany(CreateCompany):
    company_id: ModelField
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.company_id = ModelField(
            field_type=int,
            optional= False,
            eval={
                "_has_id": lambda x: Validators.sql_model_id(x, Company)
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
            raise ValidationException(message="Payload must contain the field company_id and at least one other field to edit")

class GetCompany(BaseParamsSchema):
    company_id: ModelField
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.company_id = ModelField(
            field_type=int,
            optional= False,
            eval={
                "_has_id": lambda x: Validators.sql_model_id(x, Company)
            }
        )

class GetFeedbacks(BaseParamsSchema):
    company_id: ModelField
    user_id: ModelField
    feedback_type: ModelField
    offset: ModelField
    limit: ModelField

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.company_id = ModelField(
            field_type=int,
            optional= False,
            eval={
                "_has_id": lambda x: Validators.sql_model_id(x, Company)
            }
        )

        self.user_id = ModelField(
            field_type=int,
            optional= True,
            eval={
                "_has_id": lambda x: Validators.sql_model_id(x, User)
            },
            ignore=True
        )

        self.feedback_type = ModelField(
            field_type=FeedbackType,
            optional= True,
            eval={
                "_in": lambda x: Validators.is_in(x,list(FeedbackType.__members__.values()))
            },
            preconverter= convert_to_feedback_type
        )

        self.offset  = ModelField(
            field_type=int,
            optional= True,
            eval={
                "_bigger": lambda x: "The offset value must be bigger than one" if x < 1 else None
            }            
        )

        self.limit = ModelField(
            field_type=int,
            optional= True,
            eval={
                "_bigger": lambda x: "The limit value must be bigger than zero" if x < 0 else None
            }            
        )

class RegisterFeedback(BaseParamsSchema):
    title : ModelField
    body : ModelField
    job_title : ModelField
    score : ModelField
    salary : ModelField
    type : ModelField
    company_id: ModelField
    details : ModelField

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.title = ModelField(
            field_type=str,
            optional= False,
            eval={
                "_bigger": lambda x: "The length of job title must be bigger than 4" if len(x) < 4 else None,
                "_smaller": lambda x: "The length of job title can't be bigger than 32" if len(x) > 32 else None,
            }            
        )
        self.body = ModelField(
            field_type=str,
            optional= False,
            eval={
                "_bigger": lambda x: "The length of feedback must be bigger than 20" if len(x) < 20 else None,
                "_smaller": lambda x: "The length of feedback can't be bigger than 2000" if len(x) > 2000 else None,
            }                  
        )
        self.job_title = ModelField(
            field_type=str,
            optional= False,
            eval={
                "_bigger": lambda x: "The length of job title must be bigger than 4" if len(x) < 4 else None,
                "_smaller": lambda x: "The length of job title can't be bigger than 32" if len(x) > 32 else None,
            }            
        )
        self.score = ModelField(
            field_type =  int,
            optional =  False,
            eval =  {
                "_between": lambda x: "The score must be btween 0 and 10" if x < 0 or x > 10 else None
            }
        )
        self.salary = ModelField(
            field_type=float,
            optional= False,
            eval={
                "_order": lambda x: "The salary must be btween 1 and 100 million tomans" if x < 1 or x > 100 else None,
            },
            preconverter= lambda x: parse_int_float(round(x,2), float)            
        )
        self.type = ModelField(
            field_type=FeedbackType,
            optional= False,
            eval={
                "_in": lambda x: Validators.is_in(x,list(FeedbackType.__members__.values()))
            },
            preconverter= convert_to_feedback_type            
        )
        self.company_id = ModelField(
            field_type=int,
            optional= False,
            eval={
                "_has_id": lambda x: Validators.sql_model_id(x, Company)
            }
        )

        self.details = ModelField(
            field_type=dict,
            optional= True, # TODO We later convert this to True
            eval={
                "_keys_in": lambda x: Validators.is_in(x.items().keys(),['some_key'])
            }
        )


class RegisterReview(RegisterFeedback):
    start_ts : ModelField
    end_ts : ModelField

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # message = "User has already reviewed this company"
        # user_reviewed = lambda x: Validators.is_unique(x, main_column=Review.company_id, model=Review, filters= {Review.user_id: self.inputs['user_id']})
        # self.company_id.eval["_user_reviewed"] = lambda x: message if user_reviewed(x) is not None else None
        self.type.ignore = True
        date_fmt = "%d-%m-%Y"
        self.start_ts = ModelField(
            field_type=datetime,
            optional= False,
            eval={
                "_before_now": lambda x: Validators.date_compare(x,format= date_fmt, date=None, order='before')
            },
            preconverter= lambda x: convert_to_datetime(x, date_fmt)
        )

        self.end_ts = ModelField(
            field_type=datetime,
            optional= True, # If false is given, thye are still employed
            eval={
                "_before_now": lambda x: Validators.date_compare(x,format= date_fmt, date=None, order='before'),
                "_after_start": lambda x: Validators.date_compare(x,format= date_fmt, date=self.inputs['start_ts'], order='after')
            },
            preconverter= lambda x: convert_to_datetime(x, date_fmt)
        )

class EditReview(RegisterReview):
    id: ModelField

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        for _, attr in self.get_fields():
            attr.optional = True

        if "start_ts" not in self.inputs and "end_ts" in self.inputs:
            del self.end_ts.eval["_after_start"]

        self.company_id.ignore = True

        self.id = ModelField(
            field_type=int,
            optional=False,
            eval= {
                "_has_id": lambda x: Validators.sql_model_id(x, Review)
            }
        )
    def inputs_check(self):
        if len(self.inputs) < 2 or "id" not in self.inputs:
            raise ValidationException(message="Payload must contain the field id and at least one other field to edit")    

class RegisterInterview(RegisterFeedback):
    int_ts : ModelField
    expected_salary : ModelField
    result : ModelField

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        def convert_to_interview_result(result:str):
            try:
                return InterviewResult[result]
            except:
                return None

        # message = "User has already registered an interview for this company"
        # user_reviewed = lambda x: Validators.is_unique(x, main_column=Interview.company_id, model=Interview, filters= {Interview.user_id: self.inputs['user_id']})
        # self.company_id.eval["_user_interviewed"] = lambda x: message if user_reviewed(x) is not None else None
        self.type.ignore = True
        date_fmt = "%d-%m-%Y"
        self.int_ts = ModelField(
            field_type=datetime,
            optional= False,
            eval={
                "_before_now": lambda x: Validators.date_compare(x,format= date_fmt, date=None, order='before')
            },
            preconverter= lambda x: convert_to_datetime(x, date_fmt)
        )

        self.expected_salary = self.salary # The expected_salary validator is the same as salary

        self.result = ModelField(
            field_type=InterviewResult,
            optional= False,
            eval={
                "_in": lambda x: Validators.is_in(x,list(InterviewResult.__members__.values()))
            },
            preconverter= convert_to_interview_result   
        )

class EditInterView(RegisterInterview):
    id: ModelField

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        for _, attr in self.get_fields():
            attr.optional = True

        self.company_id.ignore = True

        self.id = ModelField(
            field_type=int,
            optional=False,
            eval= {
                "_has_id": lambda x: Validators.sql_model_id(x, Interview)
            }
        )
    def inputs_check(self):
        if len(self.inputs) < 2 or "id" not in self.inputs:
            raise ValidationException(message="Payload must contain the field id and at least one other field to edit")