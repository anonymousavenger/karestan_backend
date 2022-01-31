from source import make_response
from typing import Type
from enum import Enum


class ValidationException(BaseException):
    bag = None
    code = None
    message = None

    def __init__(self, bag: dict, message=None, code=422, error="Validation error"):
        # Call the base class constructor with the parameters it needs
        super().__init__(error)
        self.message = message if message else "Please check the 'errors' for the list of validation errors"
        self.error = error
        self.bag = bag
        self.code = code

    def to_response(self, **data):
        return make_response(success=False, message=self.message, code=self.code, error=self.error, data=self.bag)

    def to_new_response(self):
        return {
            "message": self.message,
            "type": self.error,
            "errors": self.bag
        }, self.code
