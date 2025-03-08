import os
import smtplib
import logging
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Configure logging
os.makedirs('logs', exist_ok=True)
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

    def send_report(self, report_content, subject="Daily Lead Generation Report"):
        """
        Send an email report.
        
        Args:
            report_content: Content of the email report
            subject: Email subject line
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            msg = MIMEMultipart()
            msg["From"] = self.sender_email
            msg["To"] = self.recipient_email
            msg["Subject"] = subject
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
    
    def get_recent_leads(self, days_back: int = 1) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get leads collected in the last X days.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            Dictionary with leads categorized by source
        """
        results = {
            "linkedin": [],
            "reddit": []
        }
        
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days_back)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d")
        
        # Check LinkedIn leads
        try:
            if os.path.exists('data/linkedin_leads.csv'):
                linkedin_df = pd.read_csv('data/linkedin_leads.csv')
                
                # If there's a date column, filter by it
                if 'date_added' in linkedin_df.columns:
                    linkedin_df = linkedin_df[linkedin_df['date_added'] >= cutoff_str]
                
                results["linkedin"] = linkedin_df.to_dict('records')
                logger.info(f"Found {len(results['linkedin'])} recent LinkedIn leads")
        except Exception as e:
            logger.error(f"Error getting LinkedIn leads: {str(e)}")
        
        # Check Reddit leads
        try:
            if os.path.exists('data/reddit_leads.csv'):
                reddit_df = pd.read_csv('data/reddit_leads.csv')
                
                # If there's a date column, filter by it
                if 'date_added' in reddit_df.columns:
                    reddit_df = reddit_df[reddit_df['date_added'] >= cutoff_str]
                
                results["reddit"] = reddit_df.to_dict('records')
                logger.info(f"Found {len(results['reddit'])} recent Reddit leads")
        except Exception as e:
            logger.error(f"Error getting Reddit leads: {str(e)}")
        
        return results
    
    def get_recent_messages(self, days_back: int = 1) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get messages generated in the last X days.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            Dictionary with messages categorized by source
        """
        results = {
            "linkedin": [],
            "reddit": []
        }
        
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days_back)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d")
        
        # Check LinkedIn messages
        try:
            if os.path.exists('data/output/linkedin_messages.csv'):
                linkedin_df = pd.read_csv('data/output/linkedin_messages.csv')
                
                # If there's a date column, filter by it
                if 'Date Generated' in linkedin_df.columns:
                    linkedin_df = linkedin_df[linkedin_df['Date Generated'] >= cutoff_str]
                
                results["linkedin"] = linkedin_df.to_dict('records')
                logger.info(f"Found {len(results['linkedin'])} recent LinkedIn messages")
        except Exception as e:
            logger.error(f"Error getting LinkedIn messages: {str(e)}")
        
        # Check Reddit messages
        try:
            if os.path.exists('data/output/reddit_messages.csv'):
                reddit_df = pd.read_csv('data/output/reddit_messages.csv')
                
                # If there's a date column, filter by it
                if 'Date Generated' in reddit_df.columns:
                    reddit_df = reddit_df[reddit_df['Date Generated'] >= cutoff_str]
                
                results["reddit"] = reddit_df.to_dict('records')
                logger.info(f"Found {len(results['reddit'])} recent Reddit messages")
        except Exception as e:
            logger.error(f"Error getting Reddit messages: {str(e)}")
        
        return results
    
    def generate_report(self, days_back: int = 1, response_days: int = 7) -> str:
        """
        Generate a daily lead generation report.
        
        Args:
            days_back: Number of days to look back for leads and messages
            response_days: Number of days to give leads to respond
            
        Returns:
            Formatted report as a string
        """
        report_sections = []
        
        # Header
        report_sections.append("=" * 60)
        report_sections.append("PEAK TRANSFORMATION COACHING - LEAD GENERATION REPORT")
        report_sections.append("=" * 60)
        report_sections.append(f"Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report_sections.append(f"Period: Last {days_back} day(s)")
        report_sections.append("")
        
        # Get recent data
        recent_leads = self.get_recent_leads(days_back)
        recent_messages = self.get_recent_messages(days_back)
        
        # SUMMARY SECTION
        report_sections.append("SUMMARY")
        report_sections.append("-" * 60)
        
        total_linkedin_leads = len(recent_leads["linkedin"])
        total_reddit_leads = len(recent_leads["reddit"])
        total_leads = total_linkedin_leads + total_reddit_leads
        
        total_linkedin_messages = len(recent_messages["linkedin"])
        total_reddit_messages = len(recent_messages["reddit"])
        total_messages = total_linkedin_messages + total_reddit_messages
        
        report_sections.append(f"Total New Leads: {total_leads}")
        report_sections.append(f"  - LinkedIn: {total_linkedin_leads}")
        report_sections.append(f"  - Reddit: {total_reddit_leads}")
        report_sections.append("")
        report_sections.append(f"Total Messages Generated: {total_messages}")
        report_sections.append(f"  - LinkedIn: {total_linkedin_messages}")
        report_sections.append(f"  - Reddit: {total_reddit_messages}")
        report_sections.append("")
        
        # LINKEDIN SECTION
        if total_linkedin_leads > 0:
            report_sections.append("LINKEDIN LEADS")
            report_sections.append("-" * 60)
            
            # Sort LinkedIn leads by coaching_fit_score if available
            if total_linkedin_leads > 0 and 'coaching_fit_score' in recent_leads["linkedin"][0]:
                sorted_leads = sorted(
                    recent_leads["linkedin"], 
                    key=lambda x: x.get('coaching_fit_score', 0), 
                    reverse=True
                )
            else:
                sorted_leads = recent_leads["linkedin"]
            
            # Show top leads
            max_leads_to_show = min(10, total_linkedin_leads)
            report_sections.append(f"Top {max_leads_to_show} LinkedIn Leads:")
            
            for i, lead in enumerate(sorted_leads[:max_leads_to_show]):
                name = lead.get('name', 'Unknown')
                headline = lead.get('headline', 'No headline')
                location = lead.get('location', 'Unknown location')
                score = lead.get('coaching_fit_score', 'N/A')
                url = lead.get('profile_url', '')
                
                report_sections.append(f"{i+1}. {name} - {headline}")
                report_sections.append(f"   Location: {location}")
                report_sections.append(f"   Fit Score: {score}")
                report_sections.append(f"   Profile: {url}")
                report_sections.append("")
            
            report_sections.append("")
        
        # REDDIT SECTION
        if total_reddit_leads > 0:
            report_sections.append("REDDIT LEADS")
            report_sections.append("-" * 60)
            
            # Show top Reddit leads
            max_leads_to_show = min(10, total_reddit_leads)
            report_sections.append(f"Top {max_leads_to_show} Reddit Leads:")
            
            for i, lead in enumerate(recent_leads["reddit"][:max_leads_to_show]):
                username = lead.get('username', 'Unknown')
                subreddit = lead.get('subreddit', 'Unknown')
                post_title = lead.get('post_title', 'Unknown')
                keywords = lead.get('matched_keywords', '')
                url = lead.get('post_url', '')
                
                report_sections.append(f"{i+1}. u/{username} in r/{subreddit}")
                report_sections.append(f"   Post: {post_title}")
                report_sections.append(f"   Keywords: {keywords}")
                report_sections.append(f"   URL: {url}")
                report_sections.append("")
            
            report_sections.append("")
        
        # FOLLOW-UP REMINDERS SECTION
        report_sections.append("FOLLOW-UP REMINDERS")
        report_sections.append("-" * 60)
        response_cutoff = datetime.now() - timedelta(days=response_days)
        response_cutoff_str = response_cutoff.strftime("%Y-%m-%d")
        
        report_sections.append(f"Leads who haven't responded within {response_days} days should be followed up with:")
        
        # Add dummy data for demonstration - replace with real follow-up logic in production
        report_sections.append("")
        report_sections.append("1. Sarah Johnson - Director of Operations")
        report_sections.append("   Original Contact: 2025-03-01")
        report_sections.append("   Contact Method: LinkedIn")
        report_sections.append("")
        report_sections.append("2. Michael Chen - VP of Engineering")
        report_sections.append("   Original Contact: 2025-03-02")
        report_sections.append("   Contact Method: LinkedIn")
        report_sections.append("")
        
        # FOOTER
        report_sections.append("=" * 60)
        report_sections.append("NEXT STEPS")
        report_sections.append("-" * 60)
        report_sections.append("1. Review and personalize the generated messages")
        report_sections.append("2. Send connection requests to LinkedIn leads")
        report_sections.append("3. Direct message Reddit leads")
        report_sections.append("4. Schedule follow-up for non-responsive leads")
        report_sections.append("")
        report_sections.append("Report automatically generated by Peak Transformation Lead Generation Tool")
        report_sections.append("=" * 60)
        
        # Combine all sections
        return "\n".join(report_sections)


def run_email_reporter(sheets_client=None, days_back: int = 1, response_days: int = 7) -> bool:
    """
    Run the email reporter as a standalone function.
    
    Args:
        sheets_client: Google Sheets client (not used but kept for consistency)
        days_back: Number of days to look back for the report
        response_days: Number of days to give leads to respond
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    try:
        logger.info("Starting email reporter...")
        
        # Create reporter
        reporter = EmailReporter()
        
        # Generate report
        report_content = reporter.generate_report(
            days_back=days_back,
            response_days=response_days
        )
        
        # Create subject with date
        subject = f"Lead Generation Report - {datetime.now().strftime('%Y-%m-%d')}"
        
        # Send email
        success = reporter.send_report(
            report_content=report_content,
            subject=subject
        )
        
        if success:
            logger.info("Email report sent successfully")
        else:
            logger.error("Failed to send email report")
        
        return success
    
    except Exception as e:
        logger.error(f"Error running email reporter: {str(e)}")
        return False


# Function for GUI to use
def send_summary_email(summary_content):
    """Sends a summary email with the given content."""
    reporter = EmailReporter()
    return reporter.send_report(summary_content)


if __name__ == "__main__":
    # This allows the script to be run directly for testing
    success = run_email_reporter(
        days_back=1,
        response_days=7
    )
    
    print(f"Email report {'sent successfully' if success else 'failed to send'}")
