from fastapi import HTTPException


class BaseAPIException(HTTPException):
    def __init__(self, message: str = None, detail: str = None):
        self.error_code = self.__class__.__name__.replace("Exception", "").upper()
        self.message = message or detail or self.__class__.__doc__ or "An error occurred"
        super().__init__(
            status_code=self.status_code,
            detail={
                "code": self.status_code,
                "error_code": self.error_code,
                "message": self.message,
            }
        )


class NotFoundException(BaseAPIException):
    status_code = 404
    detail = "Resource not found"


class UnauthorizedException(BaseAPIException):
    status_code = 401
    detail = "Unauthorized access"


class ForbiddenException(BaseAPIException):
    status_code = 403
    detail = "Access forbidden"


class ValidationException(BaseAPIException):
    status_code = 422
    detail = "Validation error"


class BusinessException(BaseAPIException):
    status_code = 400
    detail = "Business logic error"


class BadRequestException(BusinessException):
    detail = "Invalid request"


class ConflictException(BaseAPIException):
    status_code = 409
    detail = "Resource conflict"


class InternalServerException(BaseAPIException):
    status_code = 500
    detail = "Internal server error"
