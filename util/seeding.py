import json
from datetime import datetime, timedelta
from wsgi import FlaskApp
from argon2 import PasswordHasher
from random import randint, choice
from factory import Factory, Sequence, LazyAttribute
from faker import Faker

from .db_operations import add_to_db
from models.main_models import FeedbackStatus, FeedbackType, Interview, InterviewResult, User, Company, \
Review, UserType, Province, City, Industry
from .validation import create_dir_name

session = FlaskApp.db_session()
ph = PasswordHasher()
fake_fa = Faker(locale='fa_IR')
fake_en = Faker()
number = 90
user_company_reviews = {}
titles = ['فاجعه بود','کثافت بود','عالی بود','یعنی لعنت بهتون','معمولی','توهین به شعورم بود','نرفتم','رد شدم']
bodies = [
    'تو مصاحبه طرف آشغال ریخت و از من خواست که تمیزش کنم. واقعا عملی و خوب بود فقط بو میداد',
    'یعنی لعنت به شرکتی که مدیرش تو باشی. روده فروشی کلاسش از تو بیشتره',
    'هیچوقت فکر نمیکردم که به چنین شرکت با کلاسی دعوت بشم',
    'کار کردن در این شرکت از بیگاری بدتره',
    'طویله خونه جلوی این شرکت هیچی نداره. مدیرش از شما سو استفاده میکنه',
    'اگر خیال کردید اینجا حقوق خوبی به شما میدن... خیال درستی کردید. فقط خیاله',
    'هرگز نمیشد باورم این برف پیری بر سرم. برم توی شرکتی که خاک بریزن بر سرم',
    'اگر دنبال جایی هستید که در عین جوانی و ناکامی بتونید کام عمیقی بگیرید این شرکت رو به شما حتما پیشنهاد میدم',
]
jobs = [
    'مدیر بیکار',
    'متصدی امور آبدارخانه',
    'توالتچی',
    'مسئول تدارکات',
    'منشی',
    'دکتر',
    'مهندس برق',
    'سگ گردان مدیر',
    'معاون سیستم فاضلاب'
]
    
class EmployeeFactory(Factory):
    class Meta:
        model= User

    name = LazyAttribute(lambda _: fake_fa.unique.name())
    email = LazyAttribute(lambda _: fake_en.unique.email())
    password = ph.hash("12345678")
    type = UserType.employee
    is_verified = LazyAttribute(lambda _:fake_en.boolean())

class CompanyFactory(Factory):

    class Meta:
        model= Company

    fa_name = LazyAttribute(lambda _: fake_fa.unique.company())
    en_name = LazyAttribute(lambda _: fake_en.unique.company())
    dirname = LazyAttribute(lambda o: create_dir_name(o.en_name))
    website = LazyAttribute(lambda _: fake_en.unique.domain_name())
    email = LazyAttribute(lambda o: f"contact@{o.website}")
    national_id = Sequence(lambda n: str(10000000000+n))
    phone = Sequence(lambda n: str(11111111+n))
    city_id = LazyAttribute(lambda _: randint(1,1320))
    industry_id = LazyAttribute(lambda _: randint(1,30))

class ReviewFactory(Factory):

    class Meta:
        model = Review

    title = LazyAttribute(lambda _: choice(titles))
    body = LazyAttribute(lambda _: choice(bodies))
    job_title = LazyAttribute(lambda _: choice(jobs))
    score = LazyAttribute(lambda _: randint(1,10))
    salary = LazyAttribute(lambda _: round(randint(1000000,9900000)/1000000,2))
    start_ts = LazyAttribute(lambda _: datetime.now() - timedelta(days=randint(0,1000)))
    status = LazyAttribute(lambda _: choice(list(FeedbackStatus.__members__.values())))
    end_ts = LazyAttribute(lambda o: o.start_ts + timedelta(days=randint(0,1000)))
    user_id = None
    company_id = None


class InterviewFactory(Factory):

    class Meta:
        model = Interview

    title = LazyAttribute(lambda _: choice(titles))
    body = LazyAttribute(lambda _: choice(bodies))
    job_title = LazyAttribute(lambda _: choice(jobs))
    score = LazyAttribute(lambda _: randint(1,10))
    salary = LazyAttribute(lambda _: round(randint(1000000,9900000)/1000000,2))
    expected_salary = LazyAttribute(lambda _: round(randint(1000000,9900000)/1000000,2))
    int_ts = LazyAttribute(lambda _: datetime.now() - timedelta(days=randint(0,1000)))
    status = LazyAttribute(lambda _: choice(list(FeedbackStatus.__members__.values())))
    result = LazyAttribute(lambda _: choice(list(InterviewResult.__members__.values())))
    user_id = None
    company_id = None

def create_constant_tables():
    mapper = {
        "provinces": Province,
        "cities": City,
        "industries": Industry
    }

    for file_name, model in mapper.items():
        with open(f"resources/{file_name}.json","r") as f:
            model_params  = json.load(f)
        models = []
        for item in model_params:
            models.append(model(**item))
        add_to_db(session=session, models=models)


def assign_feedback(type:FeedbackType,user_id:int):
    company_id = randint(1, number)
    j = 1
    while user_id in user_company_reviews[company_id][type]:
        j +=1
        if j > number:
            raise
        company_id = randint(2, number+3)
    if type == FeedbackType.interview:
        model = InterviewFactory(company_id=company_id, user_id=user_id)
    else:
        model = ReviewFactory(company_id=company_id, user_id=user_id)
    # We only index uniqueness for the feedbacks that have the satatus of 'show' or 'waiting'
    if model.status in  [FeedbackStatus.show, FeedbackStatus.waiting]: 
        user_company_reviews[company_id][type].append(user_id)
    return model     
    
    
def run():
    create_constant_tables()
    employee =  User(name="jobguy",password=ph.hash("12345678"),type=UserType.employee,email="me@jobguy.com")
    manager = User(name="badman",password=ph.hash("12345678"),type=UserType.manager,email="manager@choscorp.ir", is_verified=True)
    admin = User(name="admin",password=ph.hash("12345678"),type=UserType.admin,email="admin@karestan.ir", is_verified=True)
    models = [manager, employee, admin]
    for i in range(number):
        models += [EmployeeFactory(), CompanyFactory()]
        user_company_reviews[i+1] = {
            FeedbackType.interview: [],
            FeedbackType.review: []
        }
    add_to_db(session=session, models=models) # type: ignore

    feedback_models = []
    for i in range(2, number + 3):
        for j in range(400):
            feedback_type = choice(list(FeedbackType.__members__.values()))
            try:
                feedback_models.append(assign_feedback(feedback_type,i+1))
            except:
                continue
    
    add_to_db(session=session, models=feedback_models)

    



    