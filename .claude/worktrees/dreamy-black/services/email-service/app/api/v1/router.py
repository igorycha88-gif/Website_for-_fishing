from fastapi import APIRouter, HTTPException
from app.schemas.email import EmailTypeSendRequest, EmailSendResponse, GenerateCodeResponse
from app.core.email import send_verification_email, send_password_reset_email, generate_verification_code

router = APIRouter()


@router.post("/send", response_model=EmailSendResponse)
async def send_email(request: EmailTypeSendRequest):
    if request.email_type == "verification":
        success = await send_verification_email(
            to_email=request.to_email,
            verification_code=request.verification_code,
            username=request.username
        )
        message = "Verification email sent successfully"
    elif request.email_type == "password_reset":
        success = await send_password_reset_email(
            to_email=request.to_email,
            verification_code=request.verification_code,
            username=request.username
        )
        message = "Password reset email sent successfully"
    else:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_EMAIL_TYPE",
                "message": "Invalid email type",
                "details": {"email_type": request.email_type}
            }
        )

    if success:
        return EmailSendResponse(
            success=True,
            message=message
        )
    else:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "EMAIL_SEND_FAILED",
                "message": "Failed to send email",
                "details": {}
            }
        )


@router.post("/generate-code", response_model=GenerateCodeResponse)
async def generate_code():
    code = generate_verification_code()
    return GenerateCodeResponse(code=code)
