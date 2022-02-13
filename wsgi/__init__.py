from os.path import dirname
from flask import Flask
from typing import Literal, Optional, Callable, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from pathlib import Path
from redis import Redis
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from werkzeug.wsgi import get_path_info

from conf import ProductionConfig, TestConfig, DevConfig
from base_conf import BaseConfig, ProtoConfig, MAIN_ENV
from models.main_models import Base

path = dirname(__file__)


class FlaskApp(Flask):
    __app: Optional[Flask] = None
    __redis: Optional[Redis] = None
    env:Literal['production','dev','test'] = MAIN_ENV
    runtime_config: ProtoConfig
    __psql_engine = None
    __psql_session: Optional[Session] = None
    __jwt: Optional[JWTManager] = None


    def __call__(self, environ: dict, start_response: Callable) -> Any:
        print(get_path_info(environ))
        return super().__call__(environ, start_response)
    

    @classmethod
    def config(cls, **kwargs):
        """A convenient method to preconfiguren / override default flask app settings before instantiation"""
        env = kwargs.get("env")
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

        cls.runtime_config = cls.__config__init()
        cls.__app = cls(cls.runtime_config.APP_NAME, instance_relative_config=True)
        cls.__app.config.from_object(cls.runtime_config)
        CORS(cls.__app)
        cls.__create_dirs()
        cls.__redis = Redis(host=cls.runtime_config.REDIS_HOST, port=cls.runtime_config.REDIS_PORT)
        cls.__psql_engine = create_engine(cls.runtime_config.SQLALCHEMY_DATABASE_URI)
        cls.__jwt = cls.__jwt_auth_init()
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
    def register_routes(cls):
        from api.user import user_blueprint
        cls.instance()
        if cls.__app is None:
            raise NotImplementedError
        cls.__app.register_blueprint(user_blueprint)
        return cls

    @classmethod
    def db_session(cls):
        cls.instance()
        if cls.__psql_session is None:
            cls.__psql_session = Session(cls.__psql_engine)
        return cls.__psql_session

    # TODO Replace with proper Flask app teardown method
    @classmethod
    def terminate(cls):
        if cls.__psql_session is not None:
            cls.__psql_session.close_all()

    @classmethod
    def create_tables(cls):
        cls.instance()
        if cls.__psql_engine is None:
            raise NotImplementedError
        Base.metadata.create_all(cls.__psql_engine)

    @classmethod
    def drop_tables(cls):
        cls.instance()
        if cls.__psql_engine is None:
            raise NotImplementedError
        Base.metadata.drop_all(cls.__psql_engine)
    @classmethod
    def __jwt_auth_init(cls):
        if cls.__app is None:
            raise NotImplementedError
        return JWTManager(cls.__app)

    @classmethod
    def __config__init(cls):
        config: ProtoConfig
        if cls.env == 'test':
            config = TestConfig()
        elif cls.env == 'dev':
            config = DevConfig()
        elif cls.env == 'production':
            config = ProductionConfig()
        else:
            raise ValueError("'env' value must be either ['production','dev','test']")
        return config

    @classmethod
    def get_jwt(cls) -> JWTManager:
        cls.instance()
        if cls.__jwt is None:
            raise NotImplementedError
        return cls.__jwt
        


def create_app(testing=True):
    """This is the gateway function to start server it is only used by gunicorn, flask run or flask shell"""
    return FlaskApp.config(testing=testing).register_routes().instance()
    