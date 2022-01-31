from flask import Blueprint, jsonify, request
from jwt import ExpiredSignatureError
from flask_jwt_extended import set_access_cookies, unset_jwt_cookies
from controllers.user import authenticate_user, get_user_info


user_blueprint = Blueprint('user', __name__, url_prefix='/user')

@user_blueprint.route('/login', methods=['POST'])
def login():
    if request.json is None:
        raise NotImplementedError
    user_name = request.json.get('user_name',None)
    password = request.json.get('password', None)
    if user_name is None or password is None:
        return jsonify({"msg":"Empty user or password"}), 400
    try:
        token = authenticate_user(user_name=user_name, password=password)
        response = jsonify({"msg": "Login successful"})
        set_access_cookies(response, token)
        return response
    except ValueError as e:
        return jsonify({"msg":"User or password is incorrect"}), 400

@user_blueprint.route('/logout', methods=['GET'])
def logout():
    response = jsonify({"msg": "logout successful"})
    unset_jwt_cookies(response)
    return response
   

@user_blueprint.route('/add', methods=['POST'])
def add_user():
    pass

@user_blueprint.route('/edit', methods=['POST'])
def edit_user():
    pass

@user_blueprint.route('/get', methods=['GET'])
def get_user():
    try:
        return jsonify(get_user_info())
    except ExpiredSignatureError as e:
        return jsonify({
            "msg": "session expired"
        }), 400

@user_blueprint.route('/del', methods=['GET'])
def delete_user():
    pass