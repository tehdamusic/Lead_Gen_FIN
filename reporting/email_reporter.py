import os
import smtplib
import logging
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/email_reporter.log'
)
logger = logging.getLogger('email_reporter')

# Load environment variables
load_dotenv()

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
            
        logger.info(f"Email Reporter initialized with sender: {self.sender_email}")

    def generate_daily_report(self, days_back=1, response_days=7) -> str:
        """
        Generate a daily lead generation report.
        
        Args:
            days_back: Number of days to look back for new leads
            response_days: Number of days to look back for response rate calculation
            
        Returns:
            Report text
        """
        # Calculate dates
        today = datetime.now()
        report_date = (today - timedelta(days=days_back)).strftime("%Y-%m-%d")
        response_date = (today - timedelta(days=response_days)).strftime("%Y-%m-%d")
        
        # Load data from CSVs
        linkedin_leads_count = 0
        linkedin_qualified_count = 0
        reddit_leads_count = 0
        reddit_qualified_count = 0
        messages_generated_count = 0
        
        # Check LinkedIn leads
        try:
            if os.path.exists("data/scored_linkedin_leads.csv"):
                linkedin_df = pd.read_csv("data/scored_linkedin_leads.csv")
                
                # Count total and qualified leads
                linkedin_leads_count = len(linkedin_df)
                linkedin_qualified_count = len(linkedin_df[linkedin_df['qualified'] == True])
                
                logger.info(f"Found {linkedin_leads_count} LinkedIn leads, {linkedin_qualified_count} qualified")
        except Exception as e:
            logger.error(f"Error processing LinkedIn leads: {str(e)}")
        
        # Check Reddit leads
        try:
            if os.path.exists("data/scored_reddit_leads.csv"):
                reddit_df = pd.read_csv("data/scored_reddit_leads.csv")
                
                # Count total and qualified leads
                reddit_leads_count = len(reddit_df)
                reddit_qualified_count = len(reddit_df[reddit_df['qualified'] == True])
                
                logger.info(f"Found {reddit_leads_count} Reddit leads, {reddit_qualified_count} qualified")
        except Exception as e:
            logger.error(f"Error processing Reddit leads: {str(e)}")
        
        # Check messages
        try:
            linkedin_messages_count = 0
            reddit_messages_count = 0
            
            if os.path.exists("data/linkedin_messages.csv"):
                linkedin_messages_df = pd.read_csv("data/linkedin_messages.csv")
                linkedin_messages_count = len(linkedin_messages_df)
            
            if os.path.exists("data/reddit_messages.csv"):
                reddit_messages_df = pd.read_csv("data/reddit_messages.csv")
                reddit_messages_count = len(reddit_messages_df)
                
            messages_generated_count = linkedin_messages_count + reddit_messages_count
            logger.info(f"Found {messages_generated_count} total messages generated ({linkedin_messages_count} LinkedIn, {reddit_messages_count} Reddit)")
        except Exception as e:
            logger.error(f"Error processing message data: {str(e)}")
        
        # Create report text
        report = f"""
PEAK TRANSFORMATION COACHING - LEAD GENERATION REPORT
{today.strftime("%A, %B %d, %Y")}
===============================================================

SUMMARY:
-------
Total new leads: {linkedin_leads_count + reddit_leads_count}
- LinkedIn: {linkedin_leads_count} leads ({linkedin_qualified_count} qualified)
- Reddit: {reddit_leads_count} leads ({reddit_qualified_count} qualified)

Messages generated: {messages_generated_count}

QUALIFIED LEADS BREAKDOWN:
------------------------
LinkedIn qualified leads: {linkedin_qualified_count} ({linkedin_qualified_count/linkedin_leads_count*100:.1f}% of total) if linkedin_leads_count > 0 else "N/A"
Reddit qualified leads: {reddit_qualified_count} ({reddit_qualified_count/reddit_leads_count*100:.1f}% of total) if reddit_leads_count > 0 else "N/A"

TOP LEADS TO CONTACT:
-------------------"""

        # Add top LinkedIn leads
        if linkedin_leads_count > 0:
            try:
                # Get top 5 qualified LinkedIn leads
                top_linkedin = linkedin_df[linkedin_df['qualified'] == True].sort_values(by='final_score', ascending=False).head(5)
                
                report += "\n\nTop LinkedIn leads:"
                
                for i, (_, lead) in enumerate(top_linkedin.iterrows()):
                    report += f"\n{i+1}. {lead.get('name', 'Unknown')} - {lead.get('headline', 'Unknown')}"
                    report += f"\n   Score: {lead.get('final_score', 0):.2f} | {lead.get('profile_url', '')}"
                    if 'ai_notes' in lead and pd.notna(lead['ai_notes']):
                        report += f"\n   Notes: {lead['ai_notes'][:150]}..."
            except Exception as e:
                logger.error(f"Error adding top LinkedIn leads to report: {str(e)}")
                report += "\n\nCould not process LinkedIn leads due to an error."
        
        # Add top Reddit leads
        if reddit_leads_count > 0:
            try:
                # Get top 5 qualified Reddit leads
                top_reddit = reddit_df[reddit_df['qualified'] == True].sort_values(by='final_score', ascending=False).head(5)
                
                report += "\n\nTop Reddit leads:"
                
                for i, (_, lead) in enumerate(top_reddit.iterrows()):
                    report += f"\n{i+1}. u/{lead.get('username', 'Unknown')} in r/{lead.get('subreddit', 'Unknown')}"
                    report += f"\n   Score: {lead.get('final_score', 0):.2f} | {lead.get('post_url', '')}"
                    report += f"\n   Post: {lead.get('post_title', '')[:100]}..."
                    if 'ai_notes' in lead and pd.notna(lead['ai_notes']):
                        report += f"\n   Notes: {lead['ai_notes'][:150]}..."
            except Exception as e:
                logger.error(f"Error adding top Reddit leads to report: {str(e)}")
                report += "\n\nCould not process Reddit leads due to an error."
        
        report += f"""

NEXT STEPS:
----------
1. Review and connect with qualified leads
2. Personalize auto-generated messages before sending
3. Follow up with any leads that responded to previous outreach

Report generated automatically by Peak Transformation Lead Generation System.
"""
        
        return report

    def send_report(self, report_content, subject=None):
        """
        Send an email report.
        
        Args:
            report_content: Text content of the report
            subject: Email subject (optional)
            
        Returns:
            True if successful, False otherwise
        """
        if subject is None:
            subject = f"Lead Generation Report - {datetime.now().strftime('%Y-%m-%d')}"
            
        try:
            msg = MIMEMultipart()
            msg["From"] = self.sender_email
            msg["To"] = self.recipient_email
            msg["Subject"] = subject
            
            # Add text body
            msg.attach(MIMEText(report_content, "plain"))
            
            # Add attachments if available
            attachments = [
                "data/scored_linkedin_leads.csv",
                "data/scored_reddit_leads.csv",
                "data/linkedin_messages.csv",
                "data/reddit_messages.csv"
            ]
            
            for file_path in attachments:
                if os.path.exists(file_path):
                    with open(file_path, "rb") as attachment:
                        part = MIMEApplication(attachment.read(), Name=os.path.basename(file_path))
                        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                        msg.attach(part)
            
            # Send the email
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, self.recipient_email, msg.as_string())

            logger.info(f"Email report successfully sent to {self.recipient_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False

    def generate_and_send_report(self, days_back=1, response_days=7):
        """
        Generate and send a daily report.
        
        Args:
            days_back: Number of days to look back for new leads
            response_days: Number of days to look back for response rate calculation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate report
            report_content = self.generate_daily_report(
                days_back=days_back,
                response_days=response_days
            )
            
            # Send report
            return self.send_report(report_content)
        except Exception as e:
            logger.error(f"Error generating and sending report: {str(e)}")
            return False


def run_email_reporter(sheets_client=None, days_back=1, response_days=7):
    """
    Run the email reporter as a standalone function.
    
    Args:
        sheets_client: Google Sheets client (optional, not used)
        days_back: Number of days to look back for new leads
        response_days: Number of days to look back for response rate calculation
        
    Returns:
        True if successful, False otherwise
    """
    try:
        reporter = EmailReporter()
        return reporter.generate_and_send_report(
            days_back=days_back,
            response_days=response_days
        )
    except Exception as e:
        logger.error(f"Error running email reporter: {str(e)}")
        return False
