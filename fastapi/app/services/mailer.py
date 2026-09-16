import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi_mail import FastMail, ConnectionConfig, MessageSchema

load_dotenv(Path(__file__).resolve().parent.parent / '.env')

class Mailer():
    config = ConnectionConfig(
        MAIL_SERVER=os.getenv('SMTP_HOST'),
        MAIL_PORT=int(os.getenv('SMTP_PORT')),
        MAIL_USERNAME=os.getenv('SMTP_USER'),
        MAIL_PASSWORD=os.getenv('SMTP_PASS'),
        MAIL_SSL_TLS=False,
        MAIL_STARTTLS=False,
        MAIL_FROM='admin@admin.be',
        TEMPLATE_FOLDER = Path(__file__).parent.parent / 'templates'
    )
        
    async def send_message(self, subject: str, dest: list[str], template_body: dict, template_name: str):
        message = MessageSchema(
            subject=subject,
            from_email='admin@admin.be',
            recipients=dest,
            template_body=template_body,
            # body=f'L\'utilisateur {dto.name} ({dto.email}): Ce mail contenait: {dto.content}',
            subtype='html'
        )
        mailer = FastMail(Mailer.config)
        return await mailer.send_message(message, template_name=template_name)