from os.path import dirname
from flask import Flask, g, current_app
from typing import Literal, Optional
from flask_sqlalchemy import SQLAlchemy
from pathlib import Path
from redis import Redis

from conf import ProductionConfig, TestConfig, DevConfig
from base_conf import BaseConfig, ProtoConfig, MAIN_ENV
from .base_model import BaseModel as Base
from flask_cors import CORS

path = dirname(__file__)


class FlaskApp:
    __app: Optional[Flask] = None
    __redis: Optional[Redis] = None
    __has_celery:bool = True
    env:Literal['production','dev','test'] = MAIN_ENV
    runtime_config: ProtoConfig

    @classmethod
    def config(cls, **kwargs):
        """A convenient method to preconfiguren / override default flask app settings before instantiation"""
        has_celery = kwargs.get("has_celey")
        env = kwargs.get("env")
        if has_celery is not None:
            if isinstance(has_celery, bool):
                cls.__has_celery = has_celery
            else:
                raise TypeError("Error in FlaskApp config: 'has_celery' must be bool")
        if env is not None:
            if env in ['production','dev','test']:
                cls.env = env
            else:
                raise ValueError("Error in FlaskApp config: 'env' value must be either ['production','dev','test']")
        
        return cls

    @staticmethod
    def __create_dirs():
        Path(BaseConfig.LOG_DIR).mkdir(exist_ok=True)

    @classmethod
    def instance(cls):
        if cls.__app:
            return cls.__app
        config: ProtoConfig
        if cls.env == 'test':
            config = TestConfig()
        elif cls.env == 'dev':
            config = DevConfig()
        elif cls.env == 'production':
            config = ProductionConfig()
        else:
            raise ValueError("'env' value must be either ['production','dev','test']")
        cls.runtime_config = config

        cls.__app = Flask(cls.runtime_config.APP_NAME, instance_relative_config=True)
        cls.__app.config.from_object(cls.runtime_config)
        CORS(cls.__app)
        cls.__create_dirs()
        cls.__redis = Redis(host=cls.runtime_config.REDIS_HOST, port=cls.runtime_config.REDIS_PORT)
        return cls.__app

    @classmethod
    def context(cls):
        return cls.instance().app_context()

    @classmethod
    def get_redis(cls):
        cls.instance()
        if cls.__redis is None:
            raise
        return cls.__redis

    @classmethod
    def psql_db(cls) -> SQLAlchemy:
        cls.instance()
        with cls.__app.app_context(): # type: ignore
            if 'db' not in g:
                g.db = SQLAlchemy(current_app, model_class=Base)
            return g.db

    @classmethod
    def register_routes(cls):
        cls.instance()
        from api.main_routes import api
        if cls.__app is None:
            raise NotImplementedError
        cls.__app.register_blueprint(api)
        return cls

    # TODO Replace with proper Flask app teardown method
    @staticmethod
    def terminate():
        db: Optional[SQLAlchemy] = g.pop('db', None)
        if db is not None:
            db.close_all_sessions() # type: ignore

def create_app(testing=False, has_celery=True):
    """This is the gateway function to start server it is only used by gunicorn, flask run or flask shell"""
    return FlaskApp.config(testing=testing, has_celery=has_celery).register_routes().instance()
    