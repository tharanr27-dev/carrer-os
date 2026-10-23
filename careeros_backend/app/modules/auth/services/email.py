import logging

# NOT IMPLEMENTED: no email provider is configured and nothing in the application calls these functions.
# They only write a log line. Password reset and email verification are therefore unavailable (the UI says so).

logger = logging.getLogger("careeros")


def send_verification_email(email: str, token: str):
    """
    Does NOT send email. Logs only (see module note).
    """
    verification_link = f"https://careeros.com/verify?token={token}"
    logger.info(f"Sending verification email to {email}: {verification_link}")


def send_password_reset_email(email: str, token: str):
    """
    Does NOT send email. Logs only (see module note).
    """
    reset_link = f"https://careeros.com/reset-password?token={token}"
    logger.info(f"Sending password reset email to {email}: {reset_link}")
