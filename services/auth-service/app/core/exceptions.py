from fastapi import HTTPException, status


class EmailServiceUnavailableError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "EMAIL_SERVICE_UNAVAILABLE",
                    "message": "Сервис верификации временно недоступен. Попробуйте позже."
                }
            }
        )
