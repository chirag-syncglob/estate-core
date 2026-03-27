from __future__ import annotations

from http import HTTPStatus
from typing import Any, Mapping


class AppException(Exception):
    status_code = int(HTTPStatus.INTERNAL_SERVER_ERROR)
    code = "internal_server_error"
    default_message = "An unexpected error occurred."

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: Any | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        self.message = message or self.default_message
        self.code = code or self.code
        self.status_code = status_code or self.status_code
        self.details = details
        self.headers = dict(headers or {})
        super().__init__(self.message)


class BadRequestException(AppException):
    status_code = int(HTTPStatus.BAD_REQUEST)
    code = "bad_request"
    default_message = "The request is invalid."


class AuthenticationException(AppException):
    status_code = int(HTTPStatus.UNAUTHORIZED)
    code = "authentication_failed"
    default_message = "Authentication failed."


class AuthorizationException(AppException):
    status_code = int(HTTPStatus.FORBIDDEN)
    code = "forbidden"
    default_message = "You are not allowed to perform this action."


class NotFoundException(AppException):
    status_code = int(HTTPStatus.NOT_FOUND)
    code = "not_found"
    default_message = "The requested resource was not found."


class ConflictException(AppException):
    status_code = int(HTTPStatus.CONFLICT)
    code = "resource_conflict"
    default_message = "The requested operation conflicts with the current state."


class DatabaseException(AppException):
    status_code = int(HTTPStatus.INTERNAL_SERVER_ERROR)
    code = "database_error"
    default_message = "A database error occurred."
