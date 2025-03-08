import os
import logging
import openai
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
import time
import pandas as pd

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
        openai.api_key = self.api_key
        self.model = model
        logger.info(f"Initialized MessageGenerator with model: {model}")

    def generate_message(self, lead_data: Dict[str, Any], retries: int = 3) -> Optional[str]:
        """Generates a personalized outreach message using OpenAI's GPT model."""
        prompt = (
            f"""
            You are a professional sales representative. Generate a personalized message
            to reach out to a lead based on the following details:
            
            Name: {lead_data.get('name', 'Unknown')}
            Industry: {lead_data.get('industry', 'Unknown')}
            Position/Title: {lead_data.get('headline', 'Unknown')}
            Location: {lead_data.get('location', 'Unknown')}
            Interests: {lead_data.get('interests', 'Unknown')}
            Engagement Level: {lead_data.get('engagement_score', 'Unknown')}
            Profile URL: {lead_data.get('profile_url', 'Unknown')}
            
            The message should be for someone who might benefit from professional life coaching services.
            Focus on how coaching can help with career development, work-life balance, leadership skills,
            or personal growth depending on their position and industry.
            
            Keep the message professional, concise, engaging, and authentic. Aim for 150-200 words maximum.
            Do not use generic phrases like "I noticed your profile" or "I came across your profile".
            """
        )
        
        for attempt in range(retries):
            try:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[{"role": "system", "content": "You are an expert outreach specialist for a professional life coaching business."},
                              {"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=500
                )
                message = response["choices"][0]["message"]["content"].strip()
                return message
            except Exception as e:
                logger.error(f"OpenAI API error: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff for retries
        
        logger.error("Failed to generate message after multiple attempts.")
        return None
        
    def process_linkedin_leads(self, leads_data: List[Dict[str, Any]], max_leads: int = 10) -> List[Dict[str, Any]]:
        """
        Process LinkedIn leads and generate personalized messages.
        
        Args:
            leads_data: List of LinkedIn lead data
            max_leads: Maximum number of leads to process
            
        Returns:
            List of leads with generated messages
        """
        logger.info(f"Processing up to {max_leads} LinkedIn leads")
        
        processed_leads = []
        count = 0
        
        for lead in leads_data[:max_leads]:
            try:
                # Generate personalized message
                message = self.generate_message(lead)
                
                if message:
                    # Add message to lead data
                    lead['generated_message'] = message
                    lead['message_generated_at'] = time.strftime("%Y-%m-%d %H:%M:%S")
                    lead['message_status'] = 'generated'
                    processed_leads.append(lead)
                    count += 1
                    
                    logger.info(f"Generated message for {lead.get('name', 'Unknown')}")
                else:
                    logger.warning(f"Failed to generate message for {lead.get('name', 'Unknown')}")
                    lead['message_status'] = 'failed'
                    processed_leads.append(lead)
                
                # Avoid rate limiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing lead {lead.get('name', 'Unknown')}: {str(e)}")
                lead['message_status'] = 'error'
                processed_leads.append(lead)
        
        logger.info(f"Successfully generated messages for {count} out of {len(processed_leads)} LinkedIn leads")
        return processed_leads
    
    def process_reddit_leads(self, leads_data: List[Dict[str, Any]], max_leads: int = 10) -> List[Dict[str, Any]]:
        """
        Process Reddit leads and generate personalized messages.
        
        Args:
            leads_data: List of Reddit lead data
            max_leads: Maximum number of leads to process
            
        Returns:
            List of leads with generated messages
        """
        logger.info(f"Processing up to {max_leads} Reddit leads")
        
        processed_leads = []
        count = 0
        
        for lead in leads_data[:max_leads]:
            try:
                # Extract context from post content
                context = lead.get('post_content', '')[:1000] if lead.get('post_content') else ''
                
                # Add additional context for Reddit-specific message
                lead['interests'] = lead.get('matched_keywords', '')
                lead['industry'] = 'Unknown (Reddit user)'
                
                # Customize prompt for Reddit
                reddit_prompt = (
                    f"""
                    Generate a personalized and empathetic Reddit DM to a user who posted about:
                    
                    Topic: {lead.get('matched_keywords', 'Unknown')}
                    Post Title: {lead.get('post_title', 'Unknown')}
                    Reddit Username: {lead.get('username', 'Unknown')}
                    
                    Here's an excerpt from their post for context:
                    "{context}"
                    
                    Your message should be helpful and not sales-y. Position yourself as a professional 
                    life coach who can help with their specific situation. Be authentic, empathetic, and 
                    relate to their concerns. Keep it under 150 words and conversational for Reddit.
                    """
                )
                
                # Generate Reddit-specific message
                for attempt in range(3):
                    try:
                        response = openai.ChatCompletion.create(
                            model=self.model,
                            messages=[
                                {"role": "system", "content": "You are an empathetic outreach specialist for a professional life coaching business."},
                                {"role": "user", "content": reddit_prompt}
                            ],
                            temperature=0.7,
                            max_tokens=500
                        )
                        message = response["choices"][0]["message"]["content"].strip()
                        break
                    except Exception as e:
                        logger.error(f"OpenAI API error for Reddit message: {e}")
                        time.sleep(2 ** attempt)
                        message = None
                
                if message:
                    # Add message to lead data
                    lead['generated_message'] = message
                    lead['message_generated_at'] = time.strftime("%Y-%m-%d %H:%M:%S")
                    lead['message_status'] = 'generated'
                    processed_leads.append(lead)
                    count += 1
                    
                    logger.info(f"Generated message for Reddit user {lead.get('username', 'Unknown')}")
                else:
                    logger.warning(f"Failed to generate message for Reddit user {lead.get('username', 'Unknown')}")
                    lead['message_status'] = 'failed'
                    processed_leads.append(lead)
                
                # Avoid rate limiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing Reddit lead {lead.get('username', 'Unknown')}: {str(e)}")
                lead['message_status'] = 'error'
                processed_leads.append(lead)
        
        logger.info(f"Successfully generated messages for {count} out of {len(processed_leads)} Reddit leads")
        return processed_leads
    
    def save_messages_to_csv(self, leads: List[Dict[str, Any]], filename: str) -> bool:
        """
        Save leads with generated messages to CSV file.
        
        Args:
            leads: List of leads with generated messages
            filename: Output CSV filename
            
        Returns:
            True if saving was successful, False otherwise
        """
        try:
            if not leads:
                logger.warning("No leads with messages to save to CSV")
                return False
                
            # Convert to DataFrame
            df = pd.DataFrame(leads)
            
            # Save to CSV
            df.to_csv(filename, index=False)
            logger.info(f"Successfully saved {len(leads)} leads with messages to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving leads with messages to CSV: {str(e)}")
            return False

# Function to be imported and used by main.py
def run_message_generator(sheets_client=None, max_linkedin_leads=10, max_reddit_leads=10, model="gpt-4"):
    """
    Runs the message generator for LinkedIn and Reddit leads.
    
    Args:
        sheets_client: Google Sheets client for saving results
        max_linkedin_leads: Maximum number of LinkedIn leads to process
        max_reddit_leads: Maximum number of Reddit leads to process
        model: OpenAI model to use ("gpt-4" or "gpt-3.5-turbo")
        
    Returns:
        Dict with results of message generation
    """
    try:
        logger.info(f"Starting message generation with model {model}")
        results = {
            "linkedin_leads_processed": 0,
            "reddit_leads_processed": 0,
            "total_messages_generated": 0
        }
        
        # Create message generator
        message_gen = MessageGenerator(model=model)
        
        # Process LinkedIn leads if available
        try:
            linkedin_file = "data/linkedin_leads.csv"
            if os.path.exists(linkedin_file):
                # Load LinkedIn leads
                linkedin_df = pd.read_csv(linkedin_file)
                linkedin_leads = linkedin_df.to_dict('records')
                
                # Process leads
                processed_linkedin = message_gen.process_linkedin_leads(
                    linkedin_leads, 
                    max_leads=max_linkedin_leads
                )
                
                # Save results
                message_gen.save_messages_to_csv(
                    processed_linkedin, 
                    "data/output/linkedin_messages.csv"
                )
                
                # Update results
                results["linkedin_leads_processed"] = len(processed_linkedin)
                successful_linkedin = sum(1 for lead in processed_linkedin 
                                        if lead.get('message_status') == 'generated')
                results["linkedin_messages_generated"] = successful_linkedin
                
                logger.info(f"Processed {len(processed_linkedin)} LinkedIn leads")
                
                # Save to Google Sheets if provided
                if sheets_client:
                    try:
                        worksheet = sheets_client.open('LeadGenerationData').worksheet('LinkedInMessages')
                        
                        # Prepare data for sheets
                        for lead in processed_linkedin:
                            if lead.get('message_status') == 'generated':
                                row = [
                                    lead.get('name', ''),
                                    lead.get('headline', ''),
                                    lead.get('location', ''),
                                    lead.get('profile_url', ''),
                                    lead.get('generated_message', ''),
                                    lead.get('message_generated_at', ''),
                                    lead.get('coaching_fit_score', 0)
                                ]
                                worksheet.append_row(row)
                        
                        logger.info(f"Saved {successful_linkedin} LinkedIn messages to Google Sheets")
                    except Exception as e:
                        logger.error(f"Error saving LinkedIn messages to Google Sheets: {str(e)}")
            else:
                logger.warning(f"LinkedIn leads file not found: {linkedin_file}")
        except Exception as e:
            logger.error(f"Error processing LinkedIn leads: {str(e)}")
        
        # Process Reddit leads if available
        try:
            reddit_file = "data/reddit_leads.csv"
            if os.path.exists(reddit_file):
                # Load Reddit leads
                reddit_df = pd.read_csv(reddit_file)
                reddit_leads = reddit_df.to_dict('records')
                
                # Process leads
                processed_reddit = message_gen.process_reddit_leads(
                    reddit_leads, 
                    max_leads=max_reddit_leads
                )
                
                # Save results
                message_gen.save_messages_to_csv(
                    processed_reddit, 
                    "data/output/reddit_messages.csv"
                )
                
                # Update results
                results["reddit_leads_processed"] = len(processed_reddit)
                successful_reddit = sum(1 for lead in processed_reddit 
                                    if lead.get('message_status') == 'generated')
                results["reddit_messages_generated"] = successful_reddit
                
                logger.info(f"Processed {len(processed_reddit)} Reddit leads")
                
                # Save to Google Sheets if provided
                if sheets_client:
                    try:
                        worksheet = sheets_client.open('LeadGenerationData').worksheet('RedditMessages')
                        
                        # Prepare data for sheets
                        for lead in processed_reddit:
                            if lead.get('message_status') == 'generated':
                                row = [
                                    lead.get('username', ''),
                                    lead.get('post_title', ''),
                                    lead.get('subreddit', ''),
                                    lead.get('post_url', ''),
                                    lead.get('generated_message', ''),
                                    lead.get('message_generated_at', ''),
                                    lead.get('matched_keywords', '')
                                ]
                                worksheet.append_row(row)
                        
                        logger.info(f"Saved {successful_reddit} Reddit messages to Google Sheets")
                    except Exception as e:
                        logger.error(f"Error saving Reddit messages to Google Sheets: {str(e)}")
            else:
                logger.warning(f"Reddit leads file not found: {reddit_file}")
        except Exception as e:
            logger.error(f"Error processing Reddit leads: {str(e)}")
        
        # Calculate total messages generated
        results["total_messages_generated"] = results.get("linkedin_messages_generated", 0) + results.get("reddit_messages_generated", 0)
        
        logger.info(f"Message generation completed: {results['total_messages_generated']} messages generated")
        return results
        
    except Exception as e:
        logger.error(f"Error running message generator: {str(e)}")
        return {
            "linkedin_leads_processed": 0,
            "reddit_leads_processed": 0,
            "total_messages_generated": 0,
            "error": str(e)
        }

# For testing
if __name__ == "__main__":
    results = run_message_generator(max_linkedin_leads=5, max_reddit_leads=5)
    print(f"Generated {results['total_messages_generated']} messages:")
    print(f"- LinkedIn: {results.get('linkedin_messages_generated', 0)}")
    print(f"- Reddit: {results.get('reddit_messages_generated', 0)}")
