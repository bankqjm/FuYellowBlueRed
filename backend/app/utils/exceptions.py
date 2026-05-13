from fastapi import HTTPException, status


class BizException(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class UnauthorizedException(HTTPException):
    def __init__(self, message: str = "未授权"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": 401, "message": message},
        )


class ForbiddenException(HTTPException):
    def __init__(self, message: str = "权限不足"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": 403, "message": message},
        )


class NotFoundException(HTTPException):
    def __init__(self, message: str = "资源不存在"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": 404, "message": message},
        )


class BadRequestException(HTTPException):
    def __init__(self, message: str = "请求参数错误"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": 400, "message": message},
        )
