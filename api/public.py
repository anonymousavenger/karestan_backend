from typing import Literal, Optional
from flask import Blueprint, jsonify, request

from controllers.company import get_company_info, get_company_feedback_info
from models.main_models import FeedbackType
from util.validation import GetCompany, GetFeedbacks
from util.api_process import validate_and_json_response


public_blueprint = Blueprint('public', __name__, url_prefix='/')

# Important! Order at which decorators must be used:
# Route decorator -> outermost
# json_response
# Validation decorator -> innermoset

@public_blueprint.route('/companies/query', methods=['GET'])
def query_companies():
    print(request.args.to_dict())
    return jsonify({'msg':'ok'})


@public_blueprint.route('/companies/<int:company_id>', methods=['GET'])
@validate_and_json_response(validator_cls=GetCompany)
def get_company(company_id:int):
    return get_company_info(company_id=company_id)

@validate_and_json_response(validator_cls=GetFeedbacks)
def get_feedbacks(company_id:int, feedback_type:Optional[FeedbackType], sequence: Optional[int] = None):
    return get_company_feedback_info(company_id=company_id, feedback_type=feedback_type, offset=sequence)

@public_blueprint.route('/companies/<int:company_id>/<string:feedback_type>', methods=['GET'])
def get_company_feedback(company_id:int, feedback_type:Literal['interviews','reviews']):
    return get_feedbacks(company_id=company_id, feedback_type=feedback_type)


@public_blueprint.route('/companies/<int:company_id>/<string:feedback_type>/<int:sequence>', methods=['GET'])
def get_single_company_feedback(company_id:int, feedback_type:Literal['interviews','reviews'], sequence:int):
    return get_feedbacks(company_id=company_id, feedback_type=feedback_type, sequence=sequence)
