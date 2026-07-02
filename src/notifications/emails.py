"""
Implementation of a mail sender using aiosmtplib and Jinja2.
"""
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import aiosmtplib
from jinja2 import Environment, FileSystemLoader

from src.config.settings import settings
from src.security.exceptions import BaseEmailError
from src.notifications.interfaces import EmailSenderInterface


class EmailSender(EmailSenderInterface):
    """
    An asynchronous email sender that uses the Jinja2 templating engine.
    """

    def __init__(self) -> None:
        self._hostname = settings.SMTP_HOST
        self._port = settings.SMTP_PORT
        self._email = settings.MAIL_FROM
        self._password = settings.SMTP_PASSWORD
        self._use_tls = settings.SMTP_USE_TLS

        self._activation_email_template = "activation.html"
        self._activation_complete_template = "activation_complete.html"
        self._password_reset_template = "password_reset.html"
        self._password_complete_template = "password_complete.html"
        self._comment_reply_template = "comment_reply.html"
        self._comment_like_template = "comment_like.html"

        # Specify the folder containing the templates
        self._env = Environment(
            loader=FileSystemLoader("src/notifications/templates/")
        )

    async def _send_email(
            self,
            recipient: str,
            subject: str,
            html_content: str
    ) -> None:
        """
        Asynchronously send an email with the given subject and HTML content.

        Args:
            recipient (str): The recipient's email address.
            subject (str): The subject of the email.
            html_content (str): The HTML content of the email.

        Raises:
            BaseEmailError: If sending the email fails.
        """
        message = MIMEMultipart()
        message["From"] = self._email
        message["To"] = recipient
        message["Subject"] = subject
        message.attach(MIMEText(html_content, "html"))

        try:
            smtp = aiosmtplib.SMTP(
                hostname=self._hostname,
                port=self._port,
                start_tls=self._use_tls
            )
            await smtp.connect()
            if self._use_tls:
                await smtp.starttls()
            # Log in only if you have a password
            if self._password:
                await smtp.login(self._email, self._password)

            await smtp.sendmail(
                self._email,
                [recipient],
                message.as_string()
            )
            await smtp.quit()
        except aiosmtplib.SMTPException as error:
            logging.error(f"Failed to send email to {recipient}: {error}")
            raise BaseEmailError(f"Failed to send email to: {error}")

    async def send_activation_email(
            self,
            email: str,
            activation_link: str
    ) -> None:
        """
        Send an account activation email asynchronously.

        Args:
            email (str): The recipient's email address.
            activation_link (str): The activation link to be included in the email.
        """
        template = self._env.get_template(self._activation_email_template)
        html_content = template.render(
            email=email,
            activation_link=activation_link
        )
        await self._send_email(
            email,
            "Account Activation",
            html_content
        )

    async def send_activation_complete_email(
            self,
            email: str,
            login_link: str
    ) -> None:
        """
        Send an account activation completion email asynchronously.

        Args:
            email (str): The recipient's email address.
            login_link (str): The login link to be included in the email.
        """
        template = self._env.get_template(self._activation_complete_template)
        html_content = template.render(
            email=email,
            login_link=login_link
        )
        await self._send_email(
            email,
            "Account Activated Successfully",
            html_content
        )

    async def send_password_reset_email(
            self,
            email: str,
            reset_link: str
    ) -> None:
        """
        Send a password reset request email asynchronously.

        Args:
            email (str): The recipient's email address.
            reset_link (str): The reset link to be included in the email.
        """
        template = self._env.get_template(self._password_reset_template)
        html_content = template.render(
            email=email,
            reset_link=reset_link
        )
        await self._send_email(
            email,
            "Password Reset Request",
            html_content
        )

    async def send_password_reset_complete_email(
            self,
            email: str,
            login_link: str
    ) -> None:
        """
        Send a password reset completion email asynchronously.

        Args:
            email (str): The recipient's email address.
            login_link (str): The login link to be included in the email.
        """
        template = self._env.get_template(self._password_complete_template)
        html_content = template.render(
            email=email,
            login_link=login_link
        )
        await self._send_email(
            email,
            "Your Password Has Been Successfully Reset",
            html_content
        )

    async def send_comment_reply_email(
            self,
            email: str,
            movie_title: str,
            replier_name: str,
            comment_content: str
    ) -> None:
        """
        Sends an email notification to the recipient
        when they receive a reply to their comment.

        Args:
            email (str): The email address of the recipient.
            movie_title (str): The title of the movie.
            replier_name (str): The name of the user who replied.
            comment_content (str): The content of the comment.
        """
        template = self._env.get_template(self._comment_reply_template)
        html_content = template.render(
            movie_title=movie_title,
            replier_name=replier_name,
            comment_content=comment_content
        )
        await self._send_email(
            email,
            f"You have received a reply "
            f"to your comment on {movie_title}",
            html_content
        )

    async def send_comment_like_email(
            self,
            email: str,
            movie_title: str,
            comment_preview: str
    ) -> None:
        """
        Sends an email notification to the recipient
        when they receive a like to their comment.

        Args:
            email (str): The email address of the recipient.
            movie_title (str): The title of the movie.
            comment_preview (str): The preview of the comment.
        """
        template = self._env.get_template(self._comment_like_template)
        html_content = template.render(
            movie_title=movie_title,
            comment_preview=comment_preview
        )
        await self._send_email(
            email,
            f"You have received a like "
            f"to your comment on {movie_title}",
            html_content
        )


# --------------------------------------------------
# FastAPI dependencies for the notifications module.
# --------------------------------------------------


def get_email_sender() -> EmailSenderInterface:
    """
    Returns an instance of EmailSender for using in routes.
    """
    return EmailSender()
