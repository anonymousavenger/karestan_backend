import re
from flask_jwt_extended.exceptions import UserLookupError, WrongTokenError, NoAuthorizationError
from flask import request

from controllers.auth import get_current_user
from models.main_models import UserType

from .user import user_blueprint
from .admin import admin_blueprint
from util.exceptions import MiddlewareException, NotAuthorized

def admin_check():
    try:
        user = get_current_user()
        if user.type != UserType.admin:
            raise NotAuthorized
    except UserLookupError or WrongTokenError or NoAuthorizationError:
        raise NotAuthorized


mapper = {
        user_blueprint.url_prefix[1:]: {
            "middleware_func": None,
        },
        admin_blueprint.url_prefix[1:]: {
            "middleware_func": admin_check,
            "login": None
        }
    }

def __get_middleware_func(path:str):
        mid_dict = mapper
        p_list = re.findall(r"([^\/]+)", path)
        l = len(p_list)
        for i in range(0,l):
            mid_dict = mid_dict.get(p_list[i])
            if mid_dict is None:
                return None
            if i < l -1 and p_list[i+1] in mid_dict and type(mid_dict) == dict:
                continue
            elif "middleware_func" not in mid_dict:
                raise Exception(f"Missing the key 'middleware_func' in the middleware mapper definition for {path}")
            else:
                return mid_dict["middleware_func"]


def get_middleware():
    # path = parse.urlparse(url).path
    path = request.path
    return __get_middleware_func(path=path)








