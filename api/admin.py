from flask import Blueprint, jsonify, request
from jwt import ExpiredSignatureError
from flask_jwt_extended import set_access_cookies, unset_jwt_cookies

from controllers.user import authenticate_user, get_user_info, create_user, del_user, update_user
from util.exceptions import ValidationException
from util.validation import CreateUser, EditUser
from .user import login, logout


admin_blueprint = Blueprint('amin', __name__, url_prefix='/admin')

@admin_blueprint.route('/login', methods=['POST'])
def admin_login():
    return login()


@admin_blueprint.route('/logout', methods=['GET'])
def admin_logout():
    return logout()

