from fastapi import APIRouter, HTTPException, Depends
from app.schemas.email import EmailSendRequest, EmailSendResponse, GenerateCodeResponse
from app.core.email import send_verification_email, generate_verification_code
from app.core.dependencies import verify_api_key

router = APIRouter()


@router.post("/send", response_model=EmailSendResponse)
async def send_email(
    request: EmailSendRequest,
    _: str = Depends(verify_api_key)
):
    success = await send_verification_email(
        to_email=request.to_email,
        verification_code=request.verification_code,
        username=request.username
    )

    if success:
        return EmailSendResponse(
            success=True,
            message="Email sent successfully"
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
async def generate_code(_: str = Depends(verify_api_key)):
    code = generate_verification_code()
    return GenerateCodeResponse(code=code)
