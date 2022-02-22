from crypt import methods
from flask import Blueprint
from models.main_models import FeedbackType

# from controllers.company import create_company, update_company, del_company, get_company_info
from util.validation import RegisterReview, RegisterInterview
from util.api_process import validate_and_json_response
from controllers.feedback import register_feedback

feedback_blueprint = Blueprint('feedback', __name__, url_prefix='/admin')


@feedback_blueprint.route('/feedback/review/add', methods=['POST'])
@validate_and_json_response(validator_cls=RegisterReview)
def register_review(**sanitized):
    return register_feedback(type=FeedbackType.review, **sanitized)


@feedback_blueprint.route('/feedback/interview/add', methods=['POST'])
@validate_and_json_response(validator_cls=RegisterInterview)
def register_interview(**sanitized):
    return register_feedback(type=FeedbackType.interview, **sanitized)