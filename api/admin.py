from flask import Blueprint

from controllers.user import login
from controllers.company import create_company, update_company, del_company, get_company_info
from util.validation import CreateCompany, EditCompany, GetCompany
from util.api_process import validate_and_json_response
from util.validation import Login


admin_blueprint = Blueprint('admin', __name__, url_prefix='/admin')

@admin_blueprint.route('/login', methods=['POST'])
@validate_and_json_response(validator_cls=Login, access_cookie='set')
def admin_login(email:str, password:str):
    return login(email=email, password=password)


@admin_blueprint.route('/logout', methods=['GET'])
@validate_and_json_response(validator_cls=None, access_cookie='unset')
def admin_logout():
    return {}

@admin_blueprint.route('/company/create', methods=['POST'])
@validate_and_json_response(validator_cls=CreateCompany)
def add_company(**sanitized):
    return create_company(is_verified=True,**sanitized)


@admin_blueprint.route('/company/<int:company_id>/edit', methods=['POST'])
@validate_and_json_response(validator_cls=EditCompany)
def edit_company(**sanitized):
    return update_company(**sanitized)


@admin_blueprint.route('/company/<int:company_id>/get', methods=['GET'])
@validate_and_json_response(validator_cls=GetCompany)
def get_company(company_id:int):
    return get_company_info(company_id=company_id)

@admin_blueprint.route('/company/<int:company_id>/get', methods=['GET'])
@validate_and_json_response(validator_cls=GetCompany)
def del_company(company_id:int):
    return del_company(company_id=company_id)