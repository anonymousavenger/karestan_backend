import json
from datetime import datetime, timedelta
from wsgi import FlaskApp
from argon2 import PasswordHasher

from .db_operations import add_to_db
from models.main_models import User, Company, Review, UserType, Province, City


session = FlaskApp.db_session()
ph = PasswordHasher()

def create_provinces():
    with open("resources/provinces.json","r") as f:
        provinces  = json.load(f)
    models = []
    for item in provinces:
        models.append(Province(**item))
    add_to_db(session=session, models=models)


def create_cities():
    with open("resources/cities.json","r") as f:
        cities  = json.load(f)
    models = []
    for item in cities:
        models.append(City(**item))
    add_to_db(session=session, models=models)

def run():
    create_provinces()
    create_cities()
    employer =  User(name="jobguy",password=ph.hash("12345678"),type=UserType.employee,email="me@jobguy.com")
    manager = User(name="badman",password=ph.hash("12345678"),type=UserType.manager,email="manager@choscorp.ir", is_verified=True)
    admin = User(name="admin",password=ph.hash("12345678"),type=UserType.admin,email="admin@karestan.ir", is_verified=True)
    company = Company(en_name="Chos Corp",fa_name="بهینه سازان چس اندیش",email="hi@choscorp.ir", website ="choscorp.ir",
    phone="33445566", national_id="12345678901", city_id=1)
    add_to_db(session=session, models=[manager, employer, admin])
    title = "گه بگیرن در اون شرکت رو"
    body = "یعنی ریدم به شرکتی که مدیرش تو باشی. روده فروشی کلاسش از تو بیشتره"
    job_title = "ارواح عمه ت"
    score = 1
    salary = "6000000"
    start_ts = datetime.now() - timedelta(days=60)
    end_ts = datetime.now()
    review = Review(title=title, body=body, job_title=job_title, salary=salary, score=score,
    user_id=employer.id, company_id=company.id, start_ts=start_ts, end_ts=end_ts)
    company.feedbacks = [review] # type: ignore
    add_to_db(session=session, models=company)



    