from models.main_models import User, Company, Feedback, Review, Interview, CompanyResponse, UserType
from datetime import datetime, timedelta
from wsgi import FlaskApp
from argon2 import PasswordHasher
from .db_operations import add_to_db


session = FlaskApp.db_session()
ph = PasswordHasher()

def run():
    employer =  User(name="jobguy",password=ph.hash("12345678"),type=UserType.employee,email="me@jobguy.com")
    manager = User(name="badman",password=ph.hash("12345678"),type=UserType.manager,email="manager@choscorp.ir", is_verified=True)
    company = Company(en_name="Chos Corp",fa_name="بهینه سازان چس اندیش",email="hi@choscorp.ir", phone="33445566", 
    city="Tehran")
    add_to_db(session=session, models=[manager, employer])
    title = "گه بگیرن در اون شرکت رو"
    body = "یعنی ریدم به شرکتی که مدیرش تو باشی. روده فروشی کلاسش از تو بیشتره"
    job_title = "ارواح عمه ت"
    score = 1
    salary = "6000000"
    start_ts = datetime.now() - timedelta(days=60)
    end_ts = datetime.now()
    review = Review(title=title, body=body, job_title=job_title, salary=salary, score=score,
    user_id=employer.id, company_id=company.id, start_ts=start_ts, end_ts=end_ts)
    company.feedbacks = [review]
    add_to_db(session=session, models=manager)



    