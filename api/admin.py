from flask import Blueprint, jsonify, request
from flask_jwt_extended import set_access_cookies, unset_jwt_cookies

from controllers.company import create_company, update_company, del_company, get_company_info
from util.exceptions import ValidationException
from util.validation import CreateCompany, EditCompany, GetCompany
from .user import login, logout, get_json_params


admin_blueprint = Blueprint('amin', __name__, url_prefix='/admin')

@admin_blueprint.route('/login', methods=['POST'])
def admin_login():
    return login()


@admin_blueprint.route('/logout', methods=['GET'])
def admin_logout():
    return logout()

@admin_blueprint.route('/company/create', methods=['POST'])
def add_company():
    params = get_json_params()
    try:
        sanitized = CreateCompany(**params).validate()
    except ValidationException as e:
        return e.to_json_response()
    data = create_company(is_verified=True,**sanitized)
    return jsonify({"msg":"OK", "body": data})

@admin_blueprint.route('/company/<int:company_id>/edit', methods=['POST'])
def edit_company(company_id:int):
    params = get_json_params()
    try:
        sanitized = EditCompany(company_id = company_id,**params).validate()
    except ValidationException as e:
        return e.to_json_response()
    data = update_company(**sanitized)
    return jsonify({"msg":"OK", "body": data})

@admin_blueprint.route('/company/<int:company_id>/get', methods=['GET'])
def get_company(company_id:int):
    try:
        GetCompany(company_id = company_id).validate()
    except ValidationException as e:
        return e.to_json_response()
    data = get_company_info(company_id=company_id)
    return jsonify({"msg":"OK", "body": data})

@admin_blueprint.route('/company/<int:company_id>/get', methods=['GET'])
def del_company(company_id:int):
    try:
        GetCompany(company_id = company_id).validate()
    except ValidationException as e:
        return e.to_json_response()
    data = del_company(company_id=company_id)
    return jsonify({"msg":"OK", "body": data})