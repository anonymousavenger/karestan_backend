# To avoid confusion, all methods that REQUIRE jwt authentication are defined here
# DONOT use this module directly in the routes!
# TODO See if you can trun this module to a middleware

from flask_jwt_extended import jwt_required, current_user, create_access_token
from typing import Optional
from models.main_models import User
from wsgi import FlaskApp

db_session = FlaskApp.db_session()
jwt = FlaskApp.get_jwt()
q = db_session.query(User)


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
    return q.get(identity)


# This method get user by callbacks from jwt operations (see above functinos decorated with @jwt)
# also see: https://flask-jwt-extended.readthedocs.io/en/stable/automatic_user_loading
@jwt_required()
def get_current_user() -> User:
    """Gets current user object automatically using 'current_user' functionality of flask_jwt_extended
    """
    user: User = current_user # type: ignore # ignoring access error to current_user
    return user

def generate_auth_token(identity:User):
    return create_access_token(identity=identity)