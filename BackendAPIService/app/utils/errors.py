from flask import jsonify
from werkzeug.exceptions import HTTPException


class APIError(HTTPException):
    """Base API error with structured JSON response."""
    code = 400
    description = "Bad Request"

    def __init__(self, message=None, code=None, details=None):
        super().__init__(description=message or self.description)
        if code is not None:
            self.code = code
        self.message = message or self.description
        self.details = details

    # PUBLIC_INTERFACE
    def to_response(self):
        """Return a Flask response object with standardized JSON error shape."""
        payload = {"code": self.code, "message": self.message}
        if self.details is not None:
            payload["details"] = self.details
        response = jsonify(payload)
        response.status_code = self.code
        return response


class BadRequest(APIError):
    code = 400
    description = "Invalid request"


class NotFound(APIError):
    code = 404
    description = "Resource not found"


class InternalServerError(APIError):
    code = 500
    description = "Internal server error"
