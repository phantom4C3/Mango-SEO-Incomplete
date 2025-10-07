# ai_blog_writer\app\core\exceptions.py
from fastapi import HTTPException, status


class FormatterError(HTTPException):
    """Exception raised during content formatting or article processing."""

    def __init__(self, detail: str, operation: str = "Unknown"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "FormatterError",
                "operation": operation,
                "message": detail,
            },
        )


class PipelineError(HTTPException):
    """Exception raised during pipeline execution."""

    def __init__(self, detail: str, operation: str = "Unknown"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "PipelineError",
                "operation": operation,
                "message": detail,
            },
        )


class IntegrationError(HTTPException):
    """Exception raised for third-party integration failures."""

    def __init__(self, detail: str, service_name: str = "Unknown"):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "IntegrationError",
                "service": service_name,
                "message": detail,
            },
        )



