from typing import Literal
from flask import Blueprint
from werkzeug.exceptions import NotFound

from models.main_models import FeedbackType
from util.validation import EditInterView, EditReview, RegisterReview, RegisterInterview
from util.api_process import validate_and_json_response
from controllers.feedback import edit_feedback, register_feedback

feedback_blueprint = Blueprint('feedback', __name__, url_prefix='/feedback')

mapper = {
    FeedbackType.review.name: {
        'add': [RegisterReview, lambda **x: register_feedback(FeedbackType.review, **x)],
        'edit': [EditReview, lambda **x: edit_feedback(FeedbackType.review, **x)]
    },
    FeedbackType.interview.name: {
        'add': [RegisterInterview, lambda **x: register_feedback(FeedbackType.interview, **x)],
        'edit': [EditInterView, lambda **x: edit_feedback(FeedbackType.interview, **x)]
    },
}

@feedback_blueprint.route('/<string:feedback_type>/<string:operation>', methods=['POST'])
def register_review(feedback_type: str, operation: Literal['add','edit']):
    if feedback_type not in FeedbackType.names() or operation not in ['add', 'edit']:
        raise NotFound
    try:
        package = mapper[feedback_type][operation]
        [validator_cls, controller_func] = package
    except:
        raise
    func = validate_and_json_response(validator_cls=validator_cls)(controller_func)
    return func()