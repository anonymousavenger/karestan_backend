from enum import Enum
from typing import Union, List


from sqlalchemy.dialects.postgresql import JSONB, BOOLEAN, TEXT
from sqlalchemy.ext.mutable import MutableDict
from wsgi import FlaskApp

db = FlaskApp.psql_db()


# from sqlalchemy_json import mutable_json_type --> if you ever wanted to modify nested json keys
class UserType(Enum):
    admin = 'admin'
    manager = 'manager'
    employer = 'employer'

class FeedbackType(Enum):
    review = 'review'
    interview = 'interview'


class User(db.Model):
    __tablename__ = 'users'

    name = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    remember_token = db.Column(db.String(120), nullable=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    is_verified = db.Column(BOOLEAN, nullable=False, default=True)
    type = db.Column(db.Enum(UserType), default=UserType.employer)

    company = db.RelationshipProperty("Company", back_populates="user", uselist=False)
    # feedbacks = db.RelationshipProperty("Feedback", back_populates="user", lazy="dynamic")

    def __repr__(self):
        return "<User (name= '%s')>" % self.name
    

class Company(db.Model):
    __tablename__ = 'companies'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, unique=True)
    en_name = db.Column(db.String(80), unique=True, nullable=False)
    fa_name = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(80), nullable=False, unique=True)
    phone = db.Column(db.String(15), nullable=False, unique=True)
    city = db.Column(db.String(15), nullable=False, default='Tehran')
    score = db.Column(db.Integer, nullable=False, default=5)
    info = db.Column(MutableDict.as_mutable(JSONB), nullable=True)

    user = db.RelationshipProperty(User, back_populates="company")
    feedbacks = db.RelationshipProperty("Feedback", back_populates="company")


class Feedback(db.Model):
    __tablename__ = 'feedbacks'

    title = db.Column(db.String(80), unique=False, nullable=False)
    body = db.Column(TEXT, nullable=False)
    job_title = db.Column(db.String(80), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False, default=5)
    salary = db.Column(db.Integer, nullable=True)
    type = db.Column(db.String(10), nullable=False)
    details = db.Column(MutableDict.as_mutable(JSONB), nullable=True)

    # user = db.RelationshipProperty(User, back_populates="feedbacks", lazy="dynamic")
    company = db.RelationshipProperty(Company, back_populates="feedbacks")
    response = db.RelationshipProperty("CompanyResponse", back_populates="feedback", uselist=False)

    __mapper_args__ = {
        'polymorphic_identity':'feedbacks',
        'polymorphic_on':type
    }


class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, db.ForeignKey('feedbacks.id'),  primary_key=True)
    start_ts = db.Column(db.TIMESTAMP, nullable=True) # job start timestamp
    end_ts = db.Column(db.TIMESTAMP, nullable=True) # job end timestamp

    __mapper_args__ = {
        'polymorphic_identity':'review',
    }

class Interview(db.Model):
    __tablename__ = 'interviews'

    id = db.Column(db.Integer, db.ForeignKey('feedbacks.id'),  primary_key=True)
    int_ts = db.Column(db.TIMESTAMP, nullable=False) # interview date timestamp
    expected_salary = db.Column(db.Integer, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity':'interview',
    }


class CompanyResponse(db.Model):
    __tablename__ = 'company_responses'

    body = db.Column(TEXT, nullable=False)
    type = db.Column(db.Enum(FeedbackType), nullable=False)
    timestamp = db.Column(db.TIMESTAMP, nullable=False) # response date timestamp
    feedback_id = db.Column(db.Integer, db.ForeignKey('feedbacks.id'), nullable=False)
    details = db.Column(MutableDict.as_mutable(JSONB), nullable=True)

    feedback = db.RelationshipProperty(Feedback, back_populates="response")


# class Price(db.Model):
#     __tablename__ = 'prices'

#     date: str
#     has_updated_at = False
#     dict_ignore = ["id", "created_at", "timestamp"]

#     id = db.Column(db.INTEGER, primary_key=True)
#     # Mongo Db Id of the price
#     meta_info_ref_id = db.Column(db.String, nullable=False)
#     timestamp = db.Column(db.TIMESTAMP, nullable=False)
#     open = db.Column(db.Float, nullable=True)
#     high = db.Column(db.Float, nullable=True)
#     low = db.Column(db.Float, nullable=True)
#     close = db.Column(db.Float, nullable=False)
#     info = db.Column(MutableDict.as_mutable(JSONB), nullable=False)
#     misc = db.Column(MutableDict.as_mutable(JSONB), nullable=True)

#     def __repr__(self):
#         return f"<Price (id= {self.id})>"

#     def to_dict(self):
#         self.date = self.timestamp.strftime("%d-%m-%y")
#         return super().to_dict()

