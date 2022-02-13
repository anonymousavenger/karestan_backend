from sqlalchemy import String, Integer, Enum, Column, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, BOOLEAN, TEXT
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from .base_model import BaseMixin, Base
from util import BaseEnum

# from sqlalchemy_json import mutable_json_type --> if you ever wanted to modify nested json keys
class UserType(BaseEnum):
    admin = 'admin'
    manager = 'manager'
    employee = 'employee'

class FeedbackType(BaseEnum):
    review = 'review'
    interview = 'inteprview'

class User(Base, BaseMixin):
    # __tablename__ = 'users'
    dict_ignore = ['id','password','created_at','updated_at','remember_token']

    name = Column(String(80), unique=True, nullable=False)
    password = Column(String(120), nullable=False)
    remember_token = Column(String(120), nullable=True)
    email = Column(String(120), nullable=False, unique=True)
    is_verified = Column(BOOLEAN, nullable=False, default=False)
    type = Column(Enum(UserType), default=UserType.employee)

    company = relationship("Company", back_populates="user", uselist=False)
    feedbacks = relationship("Feedback", back_populates="user")

    def __repr__(self):
        return "<User (name= '%s')>" % self.name

class Province(Base, BaseMixin):
    col_ignore = ['created_at','updated_at']

    fa_name = Column(String(80), unique=True, nullable=False)
    en_name = Column(String(80), unique=True, nullable=True)

    cities = relationship("City", back_populates="province")

class City(Base, BaseMixin):
    col_ignore = ['created_at','updated_at']

    fa_name = Column(String(80), unique=False, nullable=False)
    en_name = Column(String(80), unique=False, nullable=True)
    province_id = Column(Integer, ForeignKey('provinces.id'), nullable=False)

    province = relationship(Province, back_populates="cities")
    companies = relationship("Company", back_populates="city")

class Company(Base, BaseMixin):

    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, unique=True)
    en_name = Column(String(80), unique=True, nullable=False)
    fa_name = Column(String(80), unique=True, nullable=False)
    national_id = Column(String(11), unique=True, nullable=False) 
    email = Column(String(80), nullable=False, unique=True)
    website = Column(String(80), nullable=False, unique=True)
    phone = Column(String(15), nullable=False, unique=True)
    city_id = Column(Integer, ForeignKey('cities.id'), nullable=False)
    score = Column(Integer, nullable=True)
    info = Column(MutableDict.as_mutable(JSONB), nullable=True)
    is_verified = Column(BOOLEAN, nullable=False, default=False)

    user = relationship(User, back_populates="company")
    feedbacks = relationship("Feedback", back_populates="company")
    city = relationship(City, back_populates="companies")

class Feedback(Base, BaseMixin):

    title = Column(String(80), unique=False, nullable=False)
    body = Column(TEXT, nullable=False)
    job_title = Column(String(80), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    score = Column(Integer, nullable=False, default=5)
    salary = Column(Integer, nullable=True)
    type = Column(String(10), nullable=False)
    details = Column(MutableDict.as_mutable(JSONB), nullable=True)

    user = relationship(User, back_populates="feedbacks")
    company = relationship(Company, back_populates="feedbacks")
    response = relationship("CompanyResponse", back_populates="feedback", uselist=False)

    __mapper_args__ = {
        'polymorphic_identity':'feedbacks',
        'polymorphic_on':type
    }

class Review(Feedback):
    col_ignore = ['id']
    
    id = Column(Integer, ForeignKey('feedbacks.id'),  primary_key=True) # type: ignore # declaredattr assign error
    start_ts = Column(TIMESTAMP, nullable=True) # job start timestamp
    end_ts = Column(TIMESTAMP, nullable=True) # job end timestamp

    __mapper_args__ = {
        'polymorphic_identity':'review',
    }

class Interview(Feedback):
    col_ignore = ['id']

    id = Column(Integer, ForeignKey('feedbacks.id'),  primary_key=True) # type: ignore # declaredattr assign error
    int_ts = Column(TIMESTAMP, nullable=False) # interview date timestamp
    expected_salary = Column(Integer, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity':'interview',
    }

class CompanyResponse(Base, BaseMixin):

    body = Column(TEXT, nullable=False)
    type = Column(Enum(FeedbackType), nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False) # response date timestamp
    feedback_id = Column(Integer, ForeignKey('feedbacks.id'), nullable=False)
    details = Column(MutableDict.as_mutable(JSONB), nullable=True)

    feedback = relationship(Feedback, back_populates="response")
