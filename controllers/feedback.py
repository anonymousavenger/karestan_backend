from datetime import datetime, timedelta
from typing import Optional
from models.main_models import Feedback, FeedbackStatus, FeedbackType
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
    .filter(feeback_model.status.in_([FeedbackStatus.waiting, FeedbackStatus.show])).count()
    if c > 0:
        raise ResponseException(code=400, message=f"User has already added {m_str} for this company that has 'waiting' or 'shown' status")
    feedback = feeback_model(type=type, user_id=user.id)
    for col, value in kwargs.items():
        setattr(feedback,col,value)
    add_to_db(db_session, feedback)
    feedback.id
    return feedback.to_dict()

def edit_feedback(type:FeedbackType, id:int, **kwargs):
    user = get_current_user()
    if type == FeedbackType.review:
        feeback_model = Review
        m_str = 'a review'
    elif type == FeedbackType.interview:
        feeback_model = Interview
        m_str = 'an interview'
    else:
        raise ValueError("'type' must be either interview or review of FeedbackType.")
    feedback: Optional[Feedback] = db_session.query(feeback_model).get(id)

    if feedback is None:
        raise Exception("Returned None feedback query")
    elif feedback.user_id != user.id:
        raise ResponseException(code=400, message="User is not authorized to edit this feedback")
    if feedback.created_at is not None and feedback.created_at < datetime.now() - timedelta(days=1):
        raise ResponseException(code=400, message="Feedback edit time window is expired")
    for key, value in kwargs.items():
        setattr(feedback, key, value)
    add_to_db(db_session, feedback)
    feedback.id
    return feedback.to_dict()

