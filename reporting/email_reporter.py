import os
import smtplib
import logging
import pandas as pd
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

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
            
        logger.info(f"Email reporter initialized with sender: {self.sender_email}, recipient: {self.recipient_email}")

    def send_report(self, report_content, subject="Daily Lead Generation Report") -> bool:
        """
        Send an email report.
        
        Args:
            report_content: Content of the email
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
            
    def generate_daily_report(self, days_back=1) -> str:
        """
        Generate a daily report of lead generation activities.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            String containing the formatted report
        """
        # Calculate date range
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=days_back)
        date_range_str = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        
        report_parts = []
        report_parts.append(f"LEAD GENERATION REPORT - {date_range_str}")
        report_parts.append("=" * 70 + "\n")
        
        # LinkedIn leads summary
        linkedin_summary = self._get_linkedin_summary()
        report_parts.append("LINKEDIN LEADS SUMMARY:")
        report_parts.append(linkedin_summary + "\n")
        
        # Reddit leads summary
        reddit_summary = self._get_reddit_summary()
        report_parts.append("REDDIT LEADS SUMMARY:")
        report_parts.append(reddit_summary + "\n")
        
        # Message generation summary
        message_summary = self._get_message_summary()
        report_parts.append("MESSAGE GENERATION SUMMARY:")
        report_parts.append(message_summary + "\n")
        
        # High potential leads
        high_potential_leads = self._get_high_potential_leads()
        report_parts.append("HIGH POTENTIAL LEADS:")
        report_parts.append(high_potential_leads + "\n")
        
        # Upcoming follow-ups
        follow_ups = self._get_follow_up_leads(days=7)
        report_parts.append("UPCOMING FOLLOW-UPS (Next 7 Days):")
        report_parts.append(follow_ups + "\n")
        
        # Footer
        report_parts.append("-" * 70)
        report_parts.append("This report was generated automatically by the Lead Generation Tool.")
        report_parts.append(f"Generated on: {end_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return "\n".join(report_parts)
    
    def _get_linkedin_summary(self) -> str:
        """Get summary of LinkedIn leads."""
        try:
            linkedin_file = "data/linkedin_leads.csv"
            if not os.path.exists(linkedin_file):
                return "No LinkedIn leads data found."
                
            df = pd.read_csv(linkedin_file)
            
            total_leads = len(df)
            high_score_leads = len(df[df['coaching_fit_score'] >= 80]) if 'coaching_fit_score' in df.columns else 0
            medium_score_leads = len(df[(df['coaching_fit_score'] >= 60) & (df['coaching_fit_score'] < 80)]) if 'coaching_fit_score' in df.columns else 0
            
            summary = []
            summary.append(f"Total LinkedIn Leads: {total_leads}")
            summary.append(f"High Potential Leads (Score >= 80): {high_score_leads}")
            summary.append(f"Medium Potential Leads (Score 60-79): {medium_score_leads}")
            
            # Get industries distribution if available
            if 'headline' in df.columns:
                industry_counts = {}
                for headline in df['headline']:
                    if not isinstance(headline, str):
                        continue
                        
                    headline = headline.lower()
                    for industry in ["technology", "finance", "healthcare", "education", 
                                    "consulting", "marketing", "media", "human resources"]:
                        if industry in headline:
                            industry_counts[industry] = industry_counts.get(industry, 0) + 1
                
                if industry_counts:
                    summary.append("\nIndustry Distribution:")
                    for industry, count in sorted(industry_counts.items(), key=lambda x: x[1], reverse=True):
                        summary.append(f"- {industry.capitalize()}: {count}")
            
            return "\n".join(summary)
            
        except Exception as e:
            logger.error(f"Error getting LinkedIn summary: {e}")
            return "Error generating LinkedIn summary."
    
    def _get_reddit_summary(self) -> str:
        """Get summary of Reddit leads."""
        try:
            reddit_file = "data/reddit_leads.csv"
            if not os.path.exists(reddit_file):
                return "No Reddit leads data found."
                
            df = pd.read_csv(reddit_file)
            
            total_leads = len(df)
            
            summary = []
            summary.append(f"Total Reddit Leads: {total_leads}")
            
            # Get subreddit distribution
            if 'subreddit' in df.columns:
                subreddit_counts = df['subreddit'].value_counts().head(5)
                
                if not subreddit_counts.empty:
                    summary.append("\nTop Subreddits:")
                    for subreddit, count in subreddit_counts.items():
                        summary.append(f"- r/{subreddit}: {count}")
            
            # Get keyword distribution
            if 'matched_keywords' in df.columns:
                keyword_counts = {}
                for keywords in df['matched_keywords']:
                    if not isinstance(keywords, str):
                        continue
                        
                    for keyword in keywords.split(', '):
                        keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
                
                if keyword_counts:
                    summary.append("\nTop Keywords:")
                    top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                    for keyword, count in top_keywords:
                        summary.append(f"- {keyword}: {count}")
            
            return "\n".join(summary)
            
        except Exception as e:
            logger.error(f"Error getting Reddit summary: {e}")
            return "Error generating Reddit summary."
    
    def _get_message_summary(self) -> str:
        """Get summary of generated messages."""
        try:
            linkedin_file = "data/output/linkedin_messages.csv"
            reddit_file = "data/output/reddit_messages.csv"
            
            linkedin_count = 0
            reddit_count = 0
            
            if os.path.exists(linkedin_file):
                linkedin_df = pd.read_csv(linkedin_file)
                linkedin_count = len(linkedin_df)
            
            if os.path.exists(reddit_file):
                reddit_df = pd.read_csv(reddit_file)
                reddit_count = len(reddit_df)
            
            total_messages = linkedin_count + reddit_count
            
            if total_messages == 0:
                return "No message data found."
            
            summary = []
            summary.append(f"Total Messages Generated: {total_messages}")
            summary.append(f"LinkedIn Messages: {linkedin_count}")
            summary.append(f"Reddit Messages: {reddit_count}")
            
            return "\n".join(summary)
            
        except Exception as e:
            logger.error(f"Error getting message summary: {e}")
            return "Error generating message summary."
    
    def _get_high_potential_leads(self, min_score=80, max_leads=5) -> str:
        """Get list of high potential leads."""
        try:
            linkedin_file = "data/linkedin_leads.csv"
            if not os.path.exists(linkedin_file):
                return "No LinkedIn leads data found."
                
            df = pd.read_csv(linkedin_file)
            
            if 'coaching_fit_score' not in df.columns:
                return "No scoring data available for leads."
                
            high_potential = df[df['coaching_fit_score'] >= min_score].sort_values(
                by='coaching_fit_score', ascending=False
            ).head(max_leads)
            
            if high_potential.empty:
                return f"No leads with score >= {min_score} found."
            
            result = []
            for _, lead in high_potential.iterrows():
                name = lead.get('name', 'Unknown')
                score = lead.get('coaching_fit_score', 0)
                headline = lead.get('headline', 'No headline')
                location = lead.get('location', 'Unknown location')
                url = lead.get('profile_url', '')
                
                result.append(f"- {name} ({score}/100)")
                result.append(f"  {headline}")
                result.append(f"  {location}")
                result.append(f"  {url}")
                result.append("")
            
            return "\n".join(result)
            
        except Exception as e:
            logger.error(f"Error getting high potential leads: {e}")
            return "Error generating high potential leads list."
    
    def _get_follow_up_leads(self, days=7) -> str:
        """Get list of leads that need follow-up in the next few days."""
        try:
            messages_file = "data/output/linkedin_messages.csv"
            if not os.path.exists(messages_file):
                return "No message data found for follow-ups."
                
            df = pd.read_csv(messages_file)
            
            if 'message_generated_at' not in df.columns:
                return "No message timestamp data available."
            
            # This is a placeholder since we don't have actual follow-up timestamps
            # In a real system, you would calculate based on actual follow-up dates
            result = []
            result.append("Follow-up tracking is not fully implemented yet.")
            result.append(f"Messages sent in the last {days} days that may need follow-up:")
            
            # Get messages from the last N days
            current_date = datetime.datetime.now()
            recent_messages = df.copy()
            recent_messages['days_ago'] = 0  # Placeholder
            
            if 'message_generated_at' in recent_messages.columns:
                for i, timestamp in enumerate(recent_messages['message_generated_at']):
                    try:
                        message_date = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                        days_ago = (current_date - message_date).days
                        recent_messages.loc[i, 'days_ago'] = days_ago
                    except:
                        pass
            
            # Filter to recent messages
            recent_messages = recent_messages[recent_messages['days_ago'] <= days]
            recent_messages = recent_messages.sort_values(by='days_ago')
            
            if recent_messages.empty:
                return "No recent messages found for follow-up."
            
            for _, message in recent_messages.head(5).iterrows():
                name = message.get('name', 'Unknown')
                days_ago = int(message.get('days_ago', 0))
                follow_up_day = days - days_ago
                
                result.append(f"- {name} (sent {days_ago} days ago, follow up in {follow_up_day} days)")
            
            return "\n".join(result)
            
        except Exception as e:
            logger.error(f"Error getting follow-up leads: {e}")
            return "Error generating follow-up leads list."

# Function to be imported and used by main.py
def run_email_reporter(sheets_client=None, days_back=1, response_days=7):
    """
    Run the email reporter to send lead generation summary.
    
    Args:
        sheets_client: Google Sheets client (optional)
        days_back: Number of days to look back for the report
        response_days: Number of days to include for follow-up tracking
        
    Returns:
        True if the email was sent successfully, False otherwise
    """
    try:
        logger.info(f"Starting email reporter (days_back={days_back}, response_days={response_days})")
        
        # Create reporter
        reporter = EmailReporter()
        
        # Generate report
        report_content = reporter.generate_daily_report(days_back=days_back)
        
        # Send report
        subject = f"Lead Generation Report - {datetime.datetime.now().strftime('%Y-%m-%d')}"
        success = reporter.send_report(report_content, subject=subject)
        
        if success:
            logger.info("Email report sent successfully")
        else:
            logger.error("Failed to send email report")
        
        # Save report to file for reference
        try:
            os.makedirs('data/output', exist_ok=True)
            report_file = f"data/output/report_{datetime.datetime.now().strftime('%Y%m%d')}.txt"
            with open(report_file, 'w') as f:
                f.write(report_content)
            logger.info(f"Saved report to {report_file}")
        except Exception as e:
            logger.error(f"Error saving report to file: {e}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error running email reporter: {e}")
        return False

# Function to be imported and used by GUI
def send_summary_email(summary_content, subject="Lead Generation Summary"):
    """Sends a summary email with the given content."""
    reporter = EmailReporter()
    return reporter.send_report(summary_content, subject=subject)

# For testing
if __name__ == "__main__":
    success = run_email_reporter(days_back=7, response_days=7)
    print(f"Email report {'sent successfully' if success else 'failed to send'}")
