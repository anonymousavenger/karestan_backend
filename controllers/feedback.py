from models.main_models import FeedbackStatus, FeedbackType
from .auth import get_current_user, db_session
from models.main_models import Review, Interview
from util.exceptions import ResponseException
from util.db_operations import add_to_db

def register_feedback(type:FeedbackType, **kwargs):
    user = get_current_user()
    if type == FeedbackType.review:
        feeback_model = Review
        m_str = 'a review'
    elif type == FeedbackType.interview:
        feeback_model = Interview
        m_str = 'an interview'
    else:
        raise ValueError("'type' must be either interview or review of FeedbackType.")
    q = db_session.query(feeback_model)
    c= q.filter(feeback_model.company_id == kwargs.get('company_id')).filter(feeback_model.user_id == user.id)\
    .filter(feeback_model.status._in([FeedbackStatus.waiting, FeedbackStatus.show])).count()
    if c > 0:
        raise ResponseException(code=400, message=f"User has already added {m_str} for this company")
    feedback = feeback_model(type=type, user_id=user.id)
    for col, value in kwargs.items():
        setattr(feedback,col,value)
    add_to_db(db_session, feedback)
    feedback.id
    return feedback.to_dict()
