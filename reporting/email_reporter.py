import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class EmailReporter:
    """Generates and sends daily email reports for lead generation activities."""

    def __init__(self):
        """Initialize the email reporter."""
        self.sender_email = os.getenv('EMAIL_ADDRESS')
        self.sender_password = os.getenv('EMAIL_PASSWORD')
        self.recipient_email = os.getenv('EMAIL_RECIPIENT', self.sender_email)

        if not self.sender_email or not self.sender_password:
            logger.error("Email credentials missing in environment variables")
            raise ValueError("Email credentials missing in environment variables")

    def send_report(self, report_content):
        """Send an email report."""
        try:
            msg = MIMEMultipart()
            msg["From"] = self.sender_email
            msg["To"] = self.recipient_email
            msg["Subject"] = "Daily Lead Generation Report"
            msg.attach(MIMEText(report_content, "plain"))

            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, self.recipient_email, msg.as_string())

            logger.info("Email sent successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

# Function to be imported and used by GUI
def send_summary_email(summary_content):
    """Sends a summary email with the given content."""
    reporter = EmailReporter()
    return reporter.send_report(summary_content)
