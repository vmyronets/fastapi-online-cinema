"""
This module defines an interface for email senders.
"""

from abc import ABC, abstractmethod


class EmailSenderInterface(ABC):
    """An interface for email senders."""

    @abstractmethod
    async def send_activation_email(
            self,
            email: str,
            activation_link: str
    ) -> None:
        """
        Asynchronously sends an account activation email.

        Args:
            email (str): The recipient's email address.
            activation_link (str): The activation link to include in the email.
        """
        ...

    @abstractmethod
    async def send_activation_complete_email(
            self,
            email: str,
            login_link: str
    ) -> None:
        """
        It sends a message confirming successful activation asynchronously.

        Args:
            email (str): The recipient's email address.
            login_link (str): The login link to include in the email.
        """
        ...

    @abstractmethod
    async def send_password_reset_email(
            self,
            email: str,
            reset_link: str
    ) -> None:
        """
        Asynchronously send a password reset request email.

        Args:
            email (str): The recipient's email address.
            reset_link (str): The password reset link to include in the email.
        """
        ...

    @abstractmethod
    async def send_password_reset_complete_email(
            self,
            email: str,
            login_link: str
    ) -> None:
        """
        Asynchronously send an email confirming that the password has been reset.

        Args:
            email (str): The recipient's email address.
            login_link (str): The login link to include in the email.
        """
        ...

    @abstractmethod
    async def send_comment_reply_email(
            self,
            email: str,
            movie_title: str,
            replier_name: str,
            comment_content: str
    ) -> None:
        """
        Asynchronously send an email notifying a user of a reply to their comment.

        Args:
            email (str): The recipient's email address.
            movie_title (str): The title of the movie.
            replier_name (str): The name of the user who replied.
            comment_content (str): The content of the comment that was replied to.
        """
        ...

    @abstractmethod
    async def send_comment_like_email(
            self,
            email: str,
            movie_title: str,
            comment_preview: str
    ) -> None:
        """
        Asynchronously send an email notifying a user of a like on their comment.

        Args:
            email (str): The recipient's email address.
            movie_title (str): The title of the movie.
            comment_preview (str): A preview of the comment that was liked.
        """
        ...
