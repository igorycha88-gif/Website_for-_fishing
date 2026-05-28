import aiosmtplib
import secrets
from email.message import EmailMessage
from app.core.config import Settings


settings = Settings()


def _create_verification_email_html(verification_code: str, username: str) -> str:
    return f"""
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


def _create_verification_email_text(verification_code: str, username: str) -> str:
    return f"""
Здравствуйте, {username}!

Благодарим вас за регистрацию на платформе FishMap.

Ваш код подтверждения email: {verification_code}

Срок действия кода: {settings.EMAIL_CODE_EXPIRE_MINUTES} минут

Если вы не регистрировались на нашем сайте, проигнорируйте это письмо.

© 2024 FishMap. Все права защищены.
    """


def _create_password_reset_email_html(verification_code: str, username: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #ff6b6b; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
            .content {{ background-color: #f9f9f9; padding: 30px; border: 1px solid #ddd; border-radius: 0 0 5px 5px; }}
            .code {{ background-color: #2ecc71; color: white; font-size: 32px; font-weight: bold; padding: 15px; text-align: center; border-radius: 5px; margin: 20px 0; letter-spacing: 5px; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            .warning {{ background-color: #fff3cd; color: #856404; padding: 15px; border-radius: 5px; margin: 20px 0; border: 1px solid #ffeeba; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>FishMap</h2>
            </div>
            <div class="content">
                <p>Здравствуйте, {username}!</p>
                <p>Поступил запрос на сброс пароля вашего аккаунта на платформе FishMap.</p>
                <p>Ваш код для сброса пароля:</p>
                <div class="code">{verification_code}</div>
                <p><strong>Срок действия кода: {settings.EMAIL_CODE_EXPIRE_MINUTES} минут</strong></p>
                <div class="warning">
                    <p><strong>Внимание!</strong> Если вы не запрашивали сброс пароля, немедленно проигнорируйте это письмо и измените свой пароль для безопасности.</p>
                </div>
            </div>
            <div class="footer">
                <p>&copy; 2024 FishMap. Все права защищены.</p>
            </div>
        </div>
    </body>
    </html>
    """


def _create_password_reset_email_text(verification_code: str, username: str) -> str:
    return f"""
Здравствуйте, {username}!

Поступил запрос на сброс пароля вашего аккаунта на платформе FishMap.

Ваш код для сброса пароля: {verification_code}

Срок действия кода: {settings.EMAIL_CODE_EXPIRE_MINUTES} минут

ВНИМАНИЕ! Если вы не запрашивали сброс пароля, немедленно проигнорируйте это письмо и измените свой пароль для безопасности.

© 2024 FishMap. Все права защищены.
    """


async def _send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str
) -> bool:
    try:
        print(f"Sending email to: {to_email}")
        print(f"SMTP: {settings.SMTP_HOST}:{settings.SMTP_PORT}")
        print(f"From: {settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>")

        message = EmailMessage()
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        message["To"] = to_email
        message["Subject"] = subject

        message.set_content(text_content)
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

        print(f"Email successfully sent to {to_email}")
        return True

    except Exception as e:
        print(f"Error sending email to {to_email}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def send_verification_email(to_email: str, verification_code: str, username: str) -> bool:
    subject = "Код подтверждения регистрации - FishMap"
    html_content = _create_verification_email_html(verification_code, username)
    text_content = _create_verification_email_text(verification_code, username)
    return await _send_email(to_email, subject, html_content, text_content)


async def send_password_reset_email(to_email: str, verification_code: str, username: str) -> bool:
    subject = "Код для сброса пароля - FishMap"
    html_content = _create_password_reset_email_html(verification_code, username)
    text_content = _create_password_reset_email_text(verification_code, username)
    return await _send_email(to_email, subject, html_content, text_content)


def generate_verification_code() -> str:
    return "".join([str(secrets.randbelow(10)) for _ in range(settings.EMAIL_CODE_LENGTH)])
