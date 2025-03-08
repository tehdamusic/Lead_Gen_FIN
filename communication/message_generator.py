import os
import logging
import openai
import pandas as pd
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
import time
import json

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/message_generator.log'
)
logger = logging.getLogger('message_generator')

# Load environment variables
load_dotenv()

class MessageGenerator:
    """
    AI-powered message generator for personalized outreach.
    """
    
    def __init__(self, model="gpt-4"):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("Missing OpenAI API key in .env file.")
            raise ValueError("Missing OpenAI API key.")
        self.model = model
        # Initialize OpenAI client with new SDK format
        self.client = openai.OpenAI(api_key=self.api_key)

    def generate_message(self, lead_data: Dict[str, Any], retries: int = 3) -> Optional[str]:
        """Generates a personalized outreach message using OpenAI's GPT model."""
        prompt = (
            f"""
            You are a professional sales representative. Generate a personalized message
            to reach out to a lead based on the following details:
            
            Name: {lead_data.get('name', 'Unknown')}
            Industry: {lead_data.get('industry', 'Unknown')}
            {f"Job Title: {lead_data.get('headline', '')}" if lead_data.get('headline') else ""}
            {f"Location: {lead_data.get('location', '')}" if lead_data.get('location') else ""}
            Interests: {lead_data.get('interests', 'Unknown')}
            Engagement Level: {lead_data.get('engagement_score', 'Unknown')}
            {f"Additional Notes: {lead_data.get('coaching_notes', '')}" if lead_data.get('coaching_notes') else ""}
            
            Keep the message professional, concise, and engaging. The message should be no longer than 2-3 paragraphs.
            Focus on how professional coaching services could benefit them in their current role.
            """
        )
        
        for attempt in range(retries):
            try:
                # Using the new OpenAI client library format
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert outreach specialist."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                
                # Get message from the updated API response format
                message = response.choices[0].message.content.strip()
                return message
            except Exception as e:
                logger.error(f"OpenAI API error: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff for retries
        
        logger.error("Failed to generate message after multiple attempts.")
        return None

    def generate_linkedin_messages(self, leads: List[Dict[str, Any]], max_leads: int = 10) -> List[Dict[str, Any]]:
        """
        Generate personalized outreach messages for a list of LinkedIn leads.
        
        Args:
            leads: List of lead data dictionaries from LinkedIn
            max_leads: Maximum number of leads to process
            
        Returns:
            List of lead dictionaries with added 'message' field
        """
        logger.info(f"Generating messages for {min(len(leads), max_leads)} LinkedIn leads")
        
        processed_leads = []
        count = 0
        
        for lead in leads:
            if count >= max_leads:
                break
                
            try:
                # Process industry from headline if available
                if 'headline' in lead and lead['headline']:
                    headline = lead['headline'].lower()
                    industry_keywords = {
                        'tech': 'Technology', 
                        'software': 'Technology',
                        'financial': 'Finance',
                        'finance': 'Finance',
                        'banking': 'Finance',
                        'health': 'Healthcare',
                        'medical': 'Healthcare',
                        'education': 'Education',
                        'teaching': 'Education',
                        'consult': 'Consulting',
                        'media': 'Media',
                        'market': 'Marketing',
                        'entrepreneur': 'Entrepreneurship',
                        'hr': 'Human Resources',
                        'human resources': 'Human Resources'
                    }
                    
                    # Extract industry from headline
                    lead_industry = 'General Business'
                    for keyword, industry in industry_keywords.items():
                        if keyword in headline:
                            lead_industry = industry
                            break
                            
                    lead['industry'] = lead_industry
                else:
                    lead['industry'] = 'Unknown'
                
                # Generate personalized message
                message = self.generate_message(lead)
                
                if message:
                    lead['message'] = message
                    processed_leads.append(lead)
                    count += 1
                    logger.info(f"Generated message for {lead.get('name', 'Unknown')}")
                else:
                    logger.warning(f"Failed to generate message for {lead.get('name', 'Unknown')}")
                
                # Add a small delay between API calls
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error processing lead {lead.get('name', 'Unknown')}: {str(e)}")
                continue
        
        logger.info(f"Successfully generated {len(processed_leads)} LinkedIn messages")
        return processed_leads
    
    def generate_reddit_messages(self, leads: List[Dict[str, Any]], max_leads: int = 10) -> List[Dict[str, Any]]:
        """
        Generate personalized outreach messages for a list of Reddit leads.
        
        Args:
            leads: List of lead data dictionaries from Reddit
            max_leads: Maximum number of leads to process
            
        Returns:
            List of lead dictionaries with added 'message' field
        """
        logger.info(f"Generating messages for {min(len(leads), max_leads)} Reddit leads")
        
        processed_leads = []
        count = 0
        
        for lead in leads:
            if count >= max_leads:
                break
                
            try:
                # Extract more context for the message generation
                subreddit = lead.get('subreddit', 'Unknown')
                keywords = lead.get('matched_keywords', '').split(', ')
                post_title = lead.get('post_title', '')
                post_snippet = lead.get('post_content', '')[:200] + '...' if len(lead.get('post_content', '')) > 200 else lead.get('post_content', '')
                
                # Prepare lead data with Reddit-specific information
                reddit_lead = {
                    'name': lead.get('username', 'Redditor'),
                    'industry': 'Unknown',
                    'interests': ', '.join(keywords) if keywords else 'career development',
                    'engagement_score': lead.get('score', 0),
                    'reddit_context': f"Posted in r/{subreddit} about: '{post_title}' with content: '{post_snippet}'",
                    'matched_keywords': lead.get('matched_keywords', '')
                }
                
                # Generate personalized message
                message = self.generate_message(reddit_lead)
                
                if message:
                    lead['message'] = message
                    processed_leads.append(lead)
                    count += 1
                    logger.info(f"Generated message for Reddit user {lead.get('username', 'Unknown')}")
                else:
                    logger.warning(f"Failed to generate message for Reddit user {lead.get('username', 'Unknown')}")
                
                # Add a small delay between API calls
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error processing Reddit lead {lead.get('username', 'Unknown')}: {str(e)}")
                continue
        
        logger.info(f"Successfully generated {len(processed_leads)} Reddit messages")
        return processed_leads
    
    def save_messages_to_csv(self, linkedin_leads: List[Dict[str, Any]], reddit_leads: List[Dict[str, Any]]) -> bool:
        """
        Save generated messages to CSV files.
        
        Args:
            linkedin_leads: List of LinkedIn leads with messages
            reddit_leads: List of Reddit leads with messages
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os.makedirs('data/output', exist_ok=True)
            
            # Save LinkedIn messages
            if linkedin_leads:
                linkedin_df = pd.DataFrame(linkedin_leads)
                linkedin_df.to_csv('data/output/linkedin_messages.csv', index=False)
                logger.info(f"Saved {len(linkedin_leads)} LinkedIn messages to CSV")
            
            # Save Reddit messages
            if reddit_leads:
                reddit_df = pd.DataFrame(reddit_leads)
                reddit_df.to_csv('data/output/reddit_messages.csv', index=False)
                logger.info(f"Saved {len(reddit_leads)} Reddit messages to CSV")
            
            return True
        except Exception as e:
            logger.error(f"Error saving messages to CSV: {str(e)}")
            return False
    
    def update_sheets(self, sheets_client, linkedin_leads: List[Dict[str, Any]], reddit_leads: List[Dict[str, Any]]) -> bool:
        """
        Update Google Sheets with generated messages.
        
        Args:
            sheets_client: Google Sheets client
            linkedin_leads: List of LinkedIn leads with messages
            reddit_leads: List of Reddit leads with messages
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not sheets_client:
                logger.warning("No Google Sheets client provided")
                return False
            
            # Update LinkedIn leads worksheet
            if linkedin_leads:
                try:
                    linkedin_worksheet = sheets_client.open('LeadGenerationData').worksheet('LinkedInMessages')
                    
                    # Clear existing content
                    linkedin_worksheet.clear()
                    
                    # Prepare headers
                    headers = ['Name', 'Position', 'Location', 'Profile URL', 'Message', 'Date Generated']
                    linkedin_worksheet.append_row(headers)
                    
                    # Add data rows
                    now = time.strftime("%Y-%m-%d %H:%M:%S")
                    for lead in linkedin_leads:
                        row = [
                            lead.get('name', 'Unknown'),
                            lead.get('headline', ''),
                            lead.get('location', ''),
                            lead.get('profile_url', ''),
                            lead.get('message', ''),
                            now
                        ]
                        linkedin_worksheet.append_row(row)
                    
                    logger.info(f"Updated Google Sheets with {len(linkedin_leads)} LinkedIn messages")
                except Exception as e:
                    logger.error(f"Error updating LinkedIn worksheet: {str(e)}")
            
            # Update Reddit leads worksheet
            if reddit_leads:
                try:
                    reddit_worksheet = sheets_client.open('LeadGenerationData').worksheet('RedditMessages')
                    
                    # Clear existing content
                    reddit_worksheet.clear()
                    
                    # Prepare headers
                    headers = ['Username', 'Subreddit', 'Post Title', 'Keywords', 'Message', 'Post URL', 'Date Generated']
                    reddit_worksheet.append_row(headers)
                    
                    # Add data rows
                    now = time.strftime("%Y-%m-%d %H:%M:%S")
                    for lead in reddit_leads:
                        row = [
                            lead.get('username', 'Unknown'),
                            lead.get('subreddit', ''),
                            lead.get('post_title', '')[:100] + '...' if len(lead.get('post_title', '')) > 100 else lead.get('post_title', ''),
                            lead.get('matched_keywords', ''),
                            lead.get('message', ''),
                            lead.get('post_url', ''),
                            now
                        ]
                        reddit_worksheet.append_row(row)
                    
                    logger.info(f"Updated Google Sheets with {len(reddit_leads)} Reddit messages")
                except Exception as e:
                    logger.error(f"Error updating Reddit worksheet: {str(e)}")
            
            return True
        except Exception as e:
            logger.error(f"Error updating Google Sheets: {str(e)}")
            return False


def run_message_generator(sheets_client=None, 
                         max_linkedin_leads: int = 10, 
                         max_reddit_leads: int = 10,
                         model: str = "gpt-4") -> Dict[str, Any]:
    """
    Run the message generator as a standalone function.
    
    Args:
        sheets_client: Google Sheets client for saving results
        max_linkedin_leads: Maximum number of LinkedIn leads to process
        max_reddit_leads: Maximum number of Reddit leads to process
        model: OpenAI model to use for generation
        
    Returns:
        Dictionary containing process results
    """
    results = {
        "linkedin_leads_processed": 0,
        "reddit_leads_processed": 0,
        "messages_generated": 0
    }
    
    try:
        # Create the message generator
        generator = MessageGenerator(model=model)
        
        # Load LinkedIn leads
        linkedin_leads = []
        try:
            if os.path.exists('data/linkedin_leads.csv'):
                linkedin_df = pd.read_csv('data/linkedin_leads.csv')
                linkedin_leads = linkedin_df.to_dict('records')
                logger.info(f"Loaded {len(linkedin_leads)} LinkedIn leads from CSV")
        except Exception as e:
            logger.error(f"Error loading LinkedIn leads: {str(e)}")
        
        # Load Reddit leads
        reddit_leads = []
        try:
            if os.path.exists('data/reddit_leads.csv'):
                reddit_df = pd.read_csv('data/reddit_leads.csv')
                reddit_leads = reddit_df.to_dict('records')
                logger.info(f"Loaded {len(reddit_leads)} Reddit leads from CSV")
        except Exception as e:
            logger.error(f"Error loading Reddit leads: {str(e)}")
        
        # Generate messages for LinkedIn leads
        linkedin_with_messages = []
        if linkedin_leads:
            linkedin_with_messages = generator.generate_linkedin_messages(
                linkedin_leads, 
                max_leads=max_linkedin_leads
            )
            results["linkedin_leads_processed"] = len(linkedin_with_messages)
        
        # Generate messages for Reddit leads
        reddit_with_messages = []
        if reddit_leads:
            reddit_with_messages = generator.generate_reddit_messages(
                reddit_leads,
                max_leads=max_reddit_leads
            )
            results["reddit_leads_processed"] = len(reddit_with_messages)
        
        # Calculate total messages generated
        results["messages_generated"] = results["linkedin_leads_processed"] + results["reddit_leads_processed"]
        
        # Save messages to CSV
        generator.save_messages_to_csv(linkedin_with_messages, reddit_with_messages)
        
        # Update Google Sheets if client provided
        if sheets_client:
            generator.update_sheets(sheets_client, linkedin_with_messages, reddit_with_messages)
        
        logger.info(f"Message generation completed. Generated {results['messages_generated']} messages.")
        return results
    
    except Exception as e:
        logger.error(f"Error running message generator: {str(e)}")
        results["error"] = str(e)
        return results


if __name__ == "__main__":
    # This allows the script to be run directly for testing
    from utils.sheets_manager import get_sheets_client
    
    # Get Google Sheets client
    try:
        sheets_client = get_sheets_client()
    except Exception as e:
        logger.error(f"Could not connect to Google Sheets: {str(e)}")
        sheets_client = None
    
    # Run the message generator
    results = run_message_generator(
        sheets_client=sheets_client,
        max_linkedin_leads=5,
        max_reddit_leads=5,
        model="gpt-4"
    )
    
    print(f"Generated {results['messages_generated']} messages")
