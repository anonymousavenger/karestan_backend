from abc import ABCMeta, abstractmethod
from datetime import timedelta
from enum import Enum
from os.path import dirname
from threading import main_thread

from dataclasses import dataclass
from typing import Literal, Protocol, Type


MAIN_ENV: Literal['production','dev','test'] = 'test'



class BaseConfig(metaclass=ABCMeta):
    APP_NAME = 'karestan_backend'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_URI = f'redis://{REDIS_HOST}:{REDIS_PORT}'
    
    LOG_DIR = "logs"

    # The following is called for the celery config
    broker_url = REDIS_URI
    result_serializer = 'pickle'
    task_serializer = 'pickle'
    accept_content = ['json', 'pickle']


    

# Since python 3.8, classes that act as interface can be inherited from protocols
class ProtoConfig(Protocol):
    APP_SECRET_KEY: str
    ENV: str
    SQLALCHEMY_DATABASE_URI: str
    JWT_SECRET_KEY: str
    JWT_ACCESS_TOKEN_EXPIRES: timedelta
    # MONGO_CLIENT_URI: str
    # MONGO_DB_NAME: str


# Copy These into cong.py
# class DevConfig(BaseConfig):
#     SQLALCHEMY_DATABASE_URI = 'postgresql://user:123456@localhost/crawler'
#     ENV = 'development'
#     APP_SECRET_KEY = 'dev'
#     MONGO_CLIENT_URI = "mongodb://localhost:27017"
#     MONGO_DB_NAME = "crawler"


# class TestConfig(BaseConfig):
#     SQLALCHEMY_DATABASE_URI = 'postgresql://user:123456@localhost/crawler_test'
#     ENV = 'development'
#     APP_SECRET_KEY = 'dev'
#     MONGO_CLIENT_URI = "mongodb://localhost:27017"
#     MONGO_DB_NAME = "crawler_test"

# class ProductionConfig(BaseConfig):
#     SQLALCHEMY_DATABASE_URI = 'postgresql://user:123456@localhost/crawler'
#     ENV = 'production'
#     APP_SECRET_KEY = 'secret'
#     MONGO_CLIENT_URI = "mongodb://localhost:27017"
#     MONGO_DB_NAME = "crawler"