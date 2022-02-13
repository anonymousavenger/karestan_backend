from email import message
from flask import jsonify

class ResponseException(BaseException):
    code: int
    message: str
    error: str

    def __init__(self, code, message, error) -> None:
        self.error = error
        self.code = code
        self.message = message
        super().__init__(error)

    def to_json_response(self, payload:dict=None):
        if payload is None:
            payload = {
            "msg": self.message,
            "body": {
                "type": self.error,
            }
        }
        return jsonify(payload), self.code



class ValidationException(ResponseException):
    bag = None

    def __init__(self, bag: dict, message=None, code=422, error="Validation error"):
        # Call the base class constructor with the parameters it needs
        self.message = message if message else "Please check the 'errors' for the list of validation errors"
        self.error = error
        self.bag = bag
        self.code = code
        super().__init__(code=code, message=message, error=error)


    def to_json_response(self, payload: dict = None):
        payload = {
            "msg": self.message,
            "body": {
                "type": self.error,
                "errors": self.bag
            }
        }
        return super().to_json_response(payload)


class MiddlewareException(ResponseException):
    def __init__(self, code=404, message="Not authorized", error="Middleware error") -> None:
        super().__init__(code, message, error)

