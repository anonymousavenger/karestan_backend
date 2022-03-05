from typing import Optional

class InternalException(BaseException):
    error = None
    def __init__(self, error = None) -> None:
        self.error = error
        super().__init__(error)

class ResponseException(BaseException):
    code: int
    message: str
    error: Optional[str]

    def __init__(self, code, message, error = None) -> None:
        self.error = error
        self.code = code
        self.message = message
        super().__init__(error)

    def to_dict(self, payload:Optional[dict]=None) -> dict:
        if payload is None:
            payload = {
                "type": self.error,
            }
        return payload



class ValidationException(ResponseException):
    error_bag: Optional[dict]

    def __init__(self, error_bag:Optional[dict] = None, message="Please check the 'errors' for the list of validation errors", code=422, error="Validation error"):
        # Call the base class constructor with the parameters it needs
        self.message = message
        self.error = error
        self.code = code
        self.error_bag = error_bag
        super().__init__(code=code, message=message, error=error)

    # @property
    # def schema_instance(self):
    #     from .validation import BaseParamsSchema
    #     if self.__sch_i is not None and issubclass(self.__sch_i.__class__,BaseParamsSchema):
    #         sss: BaseParamsSchema  = self.__sch_i
    #         return sss
    #     else:
    #         return None

    # @schema_instance.setter
    # def schema_instance(self, schema_instance):
    #     from .validation import BaseParamsSchema
    #     if issubclass(schema_instance.__class__,BaseParamsSchema):
    #         self.__sch_i = schema_instance
    #     else:
    #         raise ValueError

    def to_dict(self, payload: Optional[dict] = None):
        payload = {
                "type": self.error,
                "errors": self.error_bag
            }
        return super().to_dict(payload)



class MiddlewareException(ResponseException):
    def __init__(self, code=400, message="", error="Middleware error") -> None:
        super().__init__(code, message, error)

class NotAuthorized(MiddlewareException):
    def __init__(self, message="Not Authorized") -> None:
        super().__init__(message=message)

