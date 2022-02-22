from flask import Blueprint
from controllers.user import get_user_info, create_user, del_user, update_user, login

from util.validation import CreateUser, EditUser, Login
from util.api_process import validate_and_json_response

user_blueprint = Blueprint('user', __name__, url_prefix='/user')

@user_blueprint.route('/login', methods=['POST'])
@validate_and_json_response(validator_cls=Login, access_cookie='set')
def login_user(email, password):
    return login(email=email, password=password)

@user_blueprint.route('/logout', methods=['GET'])
@validate_and_json_response(validator_cls=None, access_cookie='unset')
def user_logout():
    return {}
   
@user_blueprint.route('/add', methods=['POST'])
@validate_and_json_response(validator_cls=CreateUser, access_cookie='set')
def add_user(**sanitized):
    return create_user(**sanitized)

@user_blueprint.route('/edit', methods=['POST'])
@validate_and_json_response(validator_cls=EditUser)
def edit_user(**sanitized):
    return update_user(**sanitized)
    

@user_blueprint.route('/get', methods=['GET'])
@validate_and_json_response(validator_cls=None)
def get_user():
    return get_user_info()

@user_blueprint.route('/del', methods=['GET'])
def delete_user():
    del_user()
    return user_logout()