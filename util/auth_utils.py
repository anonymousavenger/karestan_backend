from models.main_models import User
from flask_jwt_extended import create_access_token

from wsgi import FlaskApp

jwt = FlaskApp.get_jwt()


# Register a callback function that takes whatever object is passed in as the
# identity when creating JWTs and converts it to a JSON serializable format.
@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.id


# Register a callback function that loads a user from your database whenever
# a protected route is accessed. This should return any python object on a
# successful lookup, or None if the lookup failed for any reason (for example
# if the user has been deleted from the database).
@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return q.filter_by(id=identity).one_or_none()

def create_auth_token(identity:User):
    return create_access_token(identity=identity)