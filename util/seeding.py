from models.main_models import User, Company, Feedback, Review, Interview, CompanyResponse, UserType
from datetime import datetime, timedelta
from wsgi import FlaskApp


session = FlaskApp.db_session()
def run():
    employer =  User(name="jobguy",password="12345678",type=UserType.employee,email="me@jobguy.com")
    manager = User(name="badman",password="12345678",type=UserType.manager,email="manager@choscorp.ir", is_verified=True)
    company = Company(en_name="Chos Corp",fa_name="بهینه سازان چس اندیش",email="hi@choscorp.ir", phone="33445566", 
    city="Tehran")
    session.add_all([manager, employer])
    session.commit()
    manager.company = company
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
    session.add(manager)
    session.commit()



    