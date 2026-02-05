import aiosmtplib
import secrets
from email.message import EmailMessage
from typing import Optional
from app.core.config import Settings


settings = Settings()


async def send_verification_email(to_email: str, verification_code: str, username: str) -> bool:
    try:
        message = EmailMessage()
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        message["To"] = to_email
        message["Subject"] = "Код подтверждения регистрации - FishMap"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1a3a52; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border: 1px solid #ddd; border-radius: 0 0 5px 5px; }}
                .code {{ background-color: #00b4d8; color: white; font-size: 32px; font-weight: bold; padding: 15px; text-align: center; border-radius: 5px; margin: 20px 0; letter-spacing: 5px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>FishMap</h2>
                </div>
                <div class="content">
                    <p>Здравствуйте, {username}!</p>
                    <p>Благодарим вас за регистрацию на платформе FishMap.</p>
                    <p>Ваш код подтверждения email:</p>
                    <div class="code">{verification_code}</div>
                    <p><strong>Срок действия кода: {settings.EMAIL_CODE_EXPIRE_MINUTES} минут</strong></p>
                    <p>Если вы не регистрировались на нашем сайте, проигнорируйте это письмо.</p>
                </div>
                <div class="footer">
                    <p>&copy; 2024 FishMap. Все права защищены.</p>
                </div>
            </div>
        </body>
        </html>
        """

        message.set_content(f"""
Здравствуйте, {username}!

Благодарим вас за регистрацию на платформе FishMap.

Ваш код подтверждения email: {verification_code}

Срок действия кода: {settings.EMAIL_CODE_EXPIRE_MINUTES} минут

Если вы не регистрировались на нашем сайте, проигнорируйте это письмо.

© 2024 FishMap. Все права защищены.
        """)

        message.set_content(html_content, subtype="html")

        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=True,
            timeout=30
        )

        return True

    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def generate_verification_code() -> str:
    return "".join([str(secrets.randbelow(10)) for _ in range(settings.EMAIL_CODE_LENGTH)])
