import logging

# A placeholder for Celery configuration and email sending logic.
# In a real environment, we use Celery to send emails async without blocking the API.

logger = logging.getLogger("careeros")


def send_verification_email(email: str, token: str):
    """
    Dummy asynchronous function to simulate sending a verification email.
    In production, this would be a @celery.task.
    """
    verification_link = f"https://careeros.com/verify?token={token}"
    logger.info(f"Sending verification email to {email}: {verification_link}")


def send_password_reset_email(email: str, token: str):
    """
    Dummy asynchronous function to simulate sending a password reset email.
    In production, this would be a @celery.task.
    """
    reset_link = f"https://careeros.com/reset-password?token={token}"
    logger.info(f"Sending password reset email to {email}: {reset_link}")
