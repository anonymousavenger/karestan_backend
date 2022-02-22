from email import message
from typing import Optional
from flask import jsonify

class ResponseException(BaseException):
    code: int
    message: str
    error: Optional[str]

    def __init__(self, code, message, error = None) -> None:
        self.error = error
        self.code = code
        self.message = message
        super().__init__(error)

    def to_dict(self, payload:dict=None) -> dict:
        if payload is None:
            payload = {
                "type": self.error,
            }
        return payload



class ValidationException(ResponseException):
    bag = None

    def __init__(self, bag: dict, message="Please check the 'errors' for the list of validation errors", code=422, error="Validation error"):
        # Call the base class constructor with the parameters it needs
        self.message = message
        self.error = error
        self.bag = bag
        self.code = code
        super().__init__(code=code, message=message, error=error)


    def to_dict(self, payload: dict = None):
        payload = {
                "type": self.error,
                "errors": self.bag
            }
        return super().to_dict(payload)


class MiddlewareException(ResponseException):
    def __init__(self, code=404, message="", error="Middleware error") -> None:
        super().__init__(code, message, error)

class NotAuthorized(MiddlewareException):
    def __init__(self, message="Not Authorized") -> None:
        super().__init__(message=message)

