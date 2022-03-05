import re
from urllib import response
from flask import request, jsonify
from flask_jwt_extended import set_access_cookies, unset_access_cookies
from typing import Callable, Literal, Optional, Type
from functools import wraps

from .exceptions import ResponseException
from .validation import BaseParamsSchema



def get_json_params() -> dict:
    if request.method != 'POST':
        return {}
    params = request.json
    if params is None:
        return {}
    if type(params) != dict:
        raise TypeError
    else:
        return params #type: ignore

def modify_access_cookies(response, cookie_state: Literal['set','unset'], body:Optional[dict] = None):
    if cookie_state == 'set' and body is not None:
        if 'token' not in body:
            raise Exception("Missing 'token' key in 'body'")
        set_access_cookies(response[0], body['token'])
    elif cookie_state == 'unset':
        unset_access_cookies(response[0])
    return response

def validate_and_json_response(validator_cls:Optional[Type[BaseParamsSchema]], 
access_cookie:Optional[Literal['set','unset']] = None, get_params: bool = True):
    def decorator(func:Callable) -> Callable:
        @wraps(func) # we need 'wraps' to avoid the error: 'View function mapping is overwriting an existing endpoint function...'
        def val_func(**kwargs):
            if get_params:
                kwargs = {**kwargs, **get_json_params()}
            body = None
            try: 
                sanitized = validator_cls(**kwargs).validate() if validator_cls is not None else {}
                body = func(**sanitized)
                payload = {'msg':'OK','body':body}
                code = 200
            except ResponseException as e:
                payload = {
                    'msg': e.message,
                    'body': e.to_dict()
                }
                code = e.code
            except Exception as e:
                payload = {
                    'msg': 'internal error'
                }
                code = 500
            response = jsonify(payload), code
            if access_cookie is not None:
                return modify_access_cookies(response=response, cookie_state=access_cookie, body=body)
            return response
        return val_func
    return decorator