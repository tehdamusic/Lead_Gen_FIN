import os
import logging
import openai
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import time

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
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("Missing OpenAI API key in .env file.")
            raise ValueError("Missing OpenAI API key.")
        openai.api_key = self.api_key

    def generate_message(self, lead_data: Dict[str, Any], retries: int = 3) -> Optional[str]:
        """Generates a personalized outreach message using OpenAI's GPT model."""
        prompt = (
            f"""
            You are a professional sales representative. Generate a personalized message
            to reach out to a lead based on the following details:
            
            Name: {lead_data.get('name', 'Unknown')}
            Industry: {lead_data.get('industry', 'Unknown')}
            Interests: {lead_data.get('interests', 'Unknown')}
            Engagement Level: {lead_data.get('engagement_score', 'Unknown')}
            
            Keep the message professional, concise, and engaging.
            """
        )
        
        for attempt in range(retries):
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[{"role": "system", "content": "You are an expert outreach specialist."},
                              {"role": "user", "content": prompt}],
                    temperature=0.7
                )
                message = response["choices"][0]["message"]["content"].strip()
                return message
            except openai.error.OpenAIError as e:
                logger.error(f"OpenAI API error: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff for retries
        
        logger.error("Failed to generate message after multiple attempts.")
        return None
