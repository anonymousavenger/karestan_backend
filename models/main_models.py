import email
from sqlalchemy import String, Integer, Enum, Column, TIMESTAMP, ForeignKey, Index, Float
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
    interview = 'interview'

class FeedbackStatus(BaseEnum):
    waiting = 1
    show = 2
    rejected = 3
    striken = 4
    user_flagged = 5
    hidden = 6

class InterviewResult(BaseEnum):
    accepted = 1 # passed and interviewer accepted the job
    rejected = 2 # passed but interviewer rejected the job
    failed = 3 # interviever failed the interview
    cancelled = 4 # interview was cancelled
    ghosted = 5 # interview was done but the result wasn't given by the employee


class User(Base, BaseMixin):
    # __tablename__ = 'users'
    dict_ignore = ['id','password','created_at','updated_at','remember_token']

    name = Column(String(80), nullable=False)
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

class Industry(Base, BaseMixin):
    col_ignore = ["updated_at"]

    en_name = Column(String(80), unique=True, nullable=True)
    fa_name = Column(String(80), unique=True, nullable=False)
    en_description = Column(String(200), unique=False, nullable=True)
    fa_description = Column(String(200), unique=False, nullable=True)
    info = Column(MutableDict.as_mutable(JSONB), nullable=False, default= {"logo":"default","icon":"fa fa-code"})

    companies = relationship("Company", back_populates="industry")

class Company(Base, BaseMixin):

    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, unique=True)
    en_name = Column(String(80), unique=True, nullable=False)
    fa_name = Column(String(80), unique=True, nullable=False)
    dirname = Column(String(100), unique=True, nullable=False)
    brand_name = Column(String(10), unique=True, nullable=True)
    national_id = Column(String(11), unique=True, nullable=True) 
    email = Column(String(80), nullable=True, unique=True)
    website = Column(String(80), nullable=True, unique=True)
    phone = Column(String(15), nullable=True, unique=True)
    city_id = Column(Integer, ForeignKey('cities.id'), nullable=False)
    industry_id = Column(Integer, ForeignKey('industries.id'), nullable=False)
    score = Column(Integer, nullable=True)
    is_verified = Column(BOOLEAN, nullable=False, default=False)
    info = Column(MutableDict.as_mutable(JSONB), nullable=True)

    user = relationship(User, back_populates="company")
    feedbacks = relationship("Feedback", back_populates="company")
    city = relationship(City, back_populates="companies")
    industry = relationship(Industry, back_populates="companies")

class Feedback(Base, BaseMixin):

    title = Column(String(80), unique=False, nullable=False)
    body = Column(TEXT, nullable=False)
    job_title = Column(String(80), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    score = Column(Integer, nullable=False, default=5)
    salary = Column(Float, nullable=True) # Salary is in million toman
    type = Column(Enum(FeedbackType), nullable=False)
    status = Column(Enum(FeedbackStatus), nullable=False, default=FeedbackStatus.waiting)
    details = Column(MutableDict.as_mutable(JSONB), nullable=True)

    user = relationship(User, back_populates="feedbacks")
    company = relationship(Company, back_populates="feedbacks")
    response = relationship("CompanyResponse", back_populates="feedback", uselist=False)

    __mapper_args__ = {
        'polymorphic_identity':'feedbacks',
        'polymorphic_on':type
    }
    # We only index uniqueness for the feedbacks that have the satatus of 'show' or 'waiting'
    __table_args__ = (Index("unique_shown_feedback",user_id, company_id, type, status, 
    unique=True, postgresql_where=(status.in_([FeedbackStatus.show, FeedbackStatus.waiting]))),)

class Review(Feedback):
    col_ignore = ['id']
    
    id = Column(Integer, ForeignKey('feedbacks.id'),  primary_key=True) # type: ignore # declaredattr assign error
    start_ts = Column(TIMESTAMP, nullable=True) # job start timestamp
    end_ts = Column(TIMESTAMP, nullable=True) # job end timestamp

    __mapper_args__ = {
        'polymorphic_identity':FeedbackType.review,
        'polymorphic_load': 'inline'
    }

class Interview(Feedback):
    col_ignore = ['id']

    id = Column(Integer, ForeignKey('feedbacks.id'),  primary_key=True) # type: ignore # declaredattr assign error
    int_ts = Column(TIMESTAMP, nullable=False) # interview date timestamp
    expected_salary = Column(Float, nullable=True)
    result = Column(Enum(InterviewResult), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity':FeedbackType.interview,
        'polymorphic_load': 'inline'
    }

class CompanyResponse(Base, BaseMixin):

    body = Column(TEXT, nullable=False)
    type = Column(Enum(FeedbackType), nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False) # response date timestamp
    feedback_id = Column(Integer, ForeignKey('feedbacks.id'), nullable=False)
    details = Column(MutableDict.as_mutable(JSONB), nullable=True)

    feedback = relationship(Feedback, back_populates="response")
