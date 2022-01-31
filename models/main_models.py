from enum import Enum as EnumClass
from sqlalchemy import String, Integer, Enum, Column, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, BOOLEAN, TEXT
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from .base_model import BaseMixin, Base

# from sqlalchemy_json import mutable_json_type --> if you ever wanted to modify nested json keys
class UserType(EnumClass):
    admin = 'admin'
    manager = 'manager'
    employee = 'employee'

class FeedbackType(EnumClass):
    review = 'review'
    interview = 'interview'


class User(Base, BaseMixin):
    # __tablename__ = 'users'
    dict_ignore = ['id','password','created_at','updated_at','remember_token']

    id = Column(Integer, primary_key=True)
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
    

class Company(Base, BaseMixin):
    # __tablename__ = 'companies'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, unique=True)
    en_name = Column(String(80), unique=True, nullable=False)
    fa_name = Column(String(80), unique=True, nullable=False)
    email = Column(String(80), nullable=False, unique=True)
    phone = Column(String(15), nullable=False, unique=True)
    city = Column(String(15), nullable=False, default='Tehran')
    score = Column(Integer, nullable=False, default=5)
    info = Column(MutableDict.as_mutable(JSONB), nullable=True)

    user = relationship(User, back_populates="company")
    feedbacks = relationship("Feedback", back_populates="company")


class Feedback(Base, BaseMixin):
    # __tablename__ = 'feedbacks'

    id = Column(Integer, primary_key=True)
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
    # __tablename__ = 'reviews'
    
    id = Column(Integer, ForeignKey('feedbacks.id'),  primary_key=True)
    start_ts = Column(TIMESTAMP, nullable=True) # job start timestamp
    end_ts = Column(TIMESTAMP, nullable=True) # job end timestamp

    __mapper_args__ = {
        'polymorphic_identity':'review',
    }

class Interview(Feedback):
    # __tablename__ = 'interviews'

    id = Column(Integer, ForeignKey('feedbacks.id'),  primary_key=True)
    int_ts = Column(TIMESTAMP, nullable=False) # interview date timestamp
    expected_salary = Column(Integer, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity':'interview',
    }


class CompanyResponse(Base, BaseMixin):
    # __tablename__ = 'company_responses'

    id = Column(Integer, primary_key=True)
    body = Column(TEXT, nullable=False)
    type = Column(Enum(FeedbackType), nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False) # response date timestamp
    feedback_id = Column(Integer, ForeignKey('feedbacks.id'), nullable=False)
    details = Column(MutableDict.as_mutable(JSONB), nullable=True)

    feedback = relationship(Feedback, back_populates="response")


# class Price(Model):
#     __tablename__ = 'prices'

#     date: str
#     has_updated_at = False
#     dict_ignore = ["id", "created_at", "timestamp"]

#     id = Column(INTEGER, primary_key=True)
#     # Mongo Db Id of the price
#     meta_info_ref_id = Column(String, nullable=False)
#     timestamp = Column(TIMESTAMP, nullable=False)
#     open = Column(Float, nullable=True)
#     high = Column(Float, nullable=True)
#     low = Column(Float, nullable=True)
#     close = Column(Float, nullable=False)
#     info = Column(MutableDict.as_mutable(JSONB), nullable=False)
#     misc = Column(MutableDict.as_mutable(JSONB), nullable=True)

#     def __repr__(self):
#         return f"<Price (id= {self.id})>"

#     def to_dict(self):
#         self.date = self.timestamp.strftime("%d-%m-%y")
#         return super().to_dict()

