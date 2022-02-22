import json
from datetime import datetime, timedelta
from wsgi import FlaskApp
from argon2 import PasswordHasher
from random import randint, randrange
from factory import Factory, Sequence, LazyAttribute
from faker import Faker

from .db_operations import add_to_db
from models.main_models import FeedbackType, Interview, InterviewResult, User, Company, Review, UserType, Province, City

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
    website = LazyAttribute(lambda _: fake_en.unique.domain_name())
    email = LazyAttribute(lambda o: f"contact@{o.website}")
    national_id = Sequence(lambda n: str(10000000000+n))
    phone = Sequence(lambda n: str(11111111+n))
    city_id = LazyAttribute(lambda _: randint(1,1321))

def random_item(data:list):
    return data[randint(0, len(data)-1)]
class ReviewFactory(Factory):

    class Meta:
        model = Review

    title = LazyAttribute(lambda _: random_item(titles))
    body = LazyAttribute(lambda _: random_item(bodies))
    job_title = LazyAttribute(lambda _: random_item(jobs))
    score = LazyAttribute(lambda _: randint(1,10))
    salary = LazyAttribute(lambda _: str(randrange(1000000,12000000,1000000)))
    start_ts = LazyAttribute(lambda _: datetime.now() - timedelta(days=randint(0,1000)))
    end_ts = LazyAttribute(lambda o: o.start_ts + timedelta(days=randint(0,1000)))
    user_id = None
    company_id = None


class InterviewFactory(Factory):

    class Meta:
        model = Interview

    title = LazyAttribute(lambda _: random_item(titles))
    body = LazyAttribute(lambda _: random_item(bodies))
    job_title = LazyAttribute(lambda _: random_item(jobs))
    score = LazyAttribute(lambda _: randint(1,10))
    salary = LazyAttribute(lambda _: str(randrange(1000000,12000000,1000000)))
    expected_salary = LazyAttribute(lambda _: str(randrange(1000000,12000000,1000000)))
    int_ts = LazyAttribute(lambda _: datetime.now() - timedelta(days=randint(0,1000)))
    result = LazyAttribute(lambda _: random_item(list(InterviewResult.__members__.values())))
    user_id = None
    company_id = None

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


def assign_feedback(type:FeedbackType,user_id:int):
    user_company_reviews
    company_id = randint(1, number)
    j = 1
    while user_id in user_company_reviews[company_id][type]:
        j +=1
        if j > number:
            raise
        company_id = randint(2, number+3)
    user_company_reviews[company_id][type].append(user_id)
    if type == FeedbackType.interview:
        return InterviewFactory(company_id=company_id, user_id=user_id)
    else:
        return ReviewFactory(company_id=company_id, user_id=user_id)        
    
    
def run():
    user_company_reviews
    create_provinces()
    create_cities()
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
        for j in range(4):
            feedback_type = random_item(list(FeedbackType.__members__.values()))
            try:
                feedback_models.append(assign_feedback(feedback_type,i+1))
            except:
                continue
    
    add_to_db(session=session, models=feedback_models)

    



    