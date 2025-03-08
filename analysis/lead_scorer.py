import os
import re
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import time
import openai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/lead_scorer.log'
)
logger = logging.getLogger('lead_scorer')

# Ensure directories exist
os.makedirs('logs', exist_ok=True)
os.makedirs('data/output', exist_ok=True)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class LeadScorer:
    """Class to evaluate and score leads based on engagement and data."""

    def __init__(self, threshold: float = 0.5, use_ai: bool = False, model: str = "gpt-4"):
        """
        Initialize Lead Scorer with a scoring threshold.
        
        Args:
            threshold: Score threshold for qualifying leads (0.0 to 1.0)
            use_ai: Whether to use AI for advanced scoring (requires OpenAI API key)
            model: OpenAI model to use for AI scoring
        """
        self.threshold = threshold
        self.use_ai = use_ai
        self.model = model
        
        if use_ai:
            self.api_key = os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                logger.error("Missing OpenAI API key in .env file. AI scoring will be disabled.")
                self.use_ai = False
            else:
                openai.api_key = self.api_key
                logger.info(f"AI scoring enabled with model: {model}")
        
        logger.info(f"Lead scorer initialized with threshold: {threshold}, AI: {use_ai}")

    def score_leads(self, leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score leads based on predefined criteria."""
        scored_leads = []
        
        for lead in leads:
            # Basic scoring
            engagement_score = lead.get("engagement_score", 0)
            if not engagement_score and "score" in lead:
                engagement_score = lead["score"] / 100.0  # Normalize LinkedIn scores
            
            response_likelihood = lead.get("response_likelihood", 0)
            if not response_likelihood and "coaching_fit_score" in lead:
                response_likelihood = lead["coaching_fit_score"] / 100.0  # Normalize coaching scores
                
            # Default values if still not set
            if not engagement_score:
                engagement_score = 0.5
            if not response_likelihood:
                response_likelihood = 0.5
                
            # Calculate final score
            final_score = (engagement_score * 0.6) + (response_likelihood * 0.4)
            
            # Add scores to lead data
            lead["engagement_score"] = round(engagement_score, 2)
            lead["response_likelihood"] = round(response_likelihood, 2)
            lead["final_score"] = round(final_score, 2)
            lead["qualified"] = final_score >= self.threshold
            
            # Use AI for advanced scoring if enabled
            if self.use_ai:
                try:
                    ai_score = self._get_ai_score(lead)
                    if ai_score:
                        lead["ai_score"] = round(ai_score, 2)
                        # Blend AI score with rule-based score (60% AI, 40% rule-based)
                        lead["final_score"] = round((ai_score * 0.6) + (final_score * 0.4), 2)
                        lead["qualified"] = lead["final_score"] >= self.threshold
                except Exception as e:
                    logger.error(f"Error in AI scoring: {str(e)}")
            
            scored_leads.append(lead)
            
        return scored_leads
    
    def _get_ai_score(self, lead: Dict[str, Any]) -> Optional[float]:
        """Use AI to score a lead based on its data."""
        try:
            # Create a prompt for the AI
            prompt = self._create_scoring_prompt(lead)
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert lead qualification system. Your job is to analyze lead data and provide a qualification score from 0.0 to 1.0, where 1.0 is the highest quality lead."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            # Extract the score from the response
            content = response["choices"][0]["message"]["content"].strip()
            
            # Try to find a float value in the content (score between 0 and 1)
            score_match = re.search(r'score: ([0-9.]+)', content.lower())
            if score_match:
                score = float(score_match.group(1))
                # Ensure score is between 0 and 1
                score = max(0.0, min(1.0, score))
                return score
            
            # If no score format found, look for any float
            float_match = re.search(r'([0-9]+\.[0-9]+)', content)
            if float_match:
                score = float(float_match.group(1))
                # If score appears to be on a 0-100 scale, normalize it
                if score > 1.0:
                    score = score / 100.0
                # Ensure score is between 0 and 1
                score = max(0.0, min(1.0, score))
                return score
                
            logger.warning(f"Could not extract score from AI response: {content}")
            return None
            
        except Exception as e:
            logger.error(f"Error in AI scoring: {str(e)}")
            return None
    
    def _create_scoring_prompt(self, lead: Dict[str, Any]) -> str:
        """Create a prompt for AI scoring based on lead data."""
        # Determine the type of lead (LinkedIn or Reddit)
        is_linkedin = "headline" in lead or "profile_url" in lead
        is_reddit = "post_title" in lead or "post_content" in lead or "subreddit" in lead
        
        if is_linkedin:
            return self._create_linkedin_prompt(lead)
        elif is_reddit:
            return self._create_reddit_prompt(lead)
        else:
            # Generic prompt if lead type is unclear
            return f"""
            Please analyze this lead and provide a qualification score from 0.0 to 1.0:
            
            Lead Data:
            {json.dumps(lead, indent=2)}
            
            Consider all available factors to determine the likelihood this lead:
            1. Would benefit from professional life coaching services
            2. Has decision-making capacity
            3. Is likely to respond positively to outreach
            
            Return your analysis and final score in this format:
            Analysis: [your analysis]
            Score: [0.0-1.0]
            """
    
    def _create_linkedin_prompt(self, lead: Dict[str, Any]) -> str:
        """Create a prompt specific to LinkedIn leads."""
        name = lead.get("name", "Unknown")
        headline = lead.get("headline", "Unknown position")
        location = lead.get("location", "Unknown location")
        coaching_score = lead.get("coaching_fit_score", "Not scored")
        coaching_notes = lead.get("coaching_notes", "No notes available")
        
        return f"""
        Please analyze this LinkedIn lead and provide a qualification score from 0.0 to 1.0:
        
        Name: {name}
        Position: {headline}
        Location: {location}
        Initial Coaching Fit Score: {coaching_score}/100
        Notes: {coaching_notes}
        
        Consider these factors for a professional life coaching prospect:
        1. Leadership position or decision-making authority
        2. Industry alignment with coaching services (e.g., executives, managers, professionals)
        3. Geographic relevance for our coaching business
        4. Indicators of career transition, growth, or challenges that coaching could address
        
        Return your analysis and final score in this format:
        Analysis: [your analysis]
        Score: [0.0-1.0]
        """
    
    def _create_reddit_prompt(self, lead: Dict[str, Any]) -> str:
        """Create a prompt specific to Reddit leads."""
        username = lead.get("username", "Unknown")
        title = lead.get("post_title", "No title")
        subreddit = lead.get("subreddit", "Unknown subreddit")
        keywords = lead.get("matched_keywords", "No keywords")
        
        # Get a snippet of the content (first 300 chars)
        content = lead.get("post_content", "No content")
        if content and len(content) > 300:
            content = content[:297] + "..."
        
        return f"""
        Please analyze this Reddit lead and provide a qualification score from 0.0 to 1.0:
        
        Username: {username}
        Subreddit: r/{subreddit}
        Post Title: {title}
        Matched Keywords: {keywords}
        Post Content Snippet: "{content}"
        
        Consider these factors for a professional coaching prospect on Reddit:
        1. Is the person expressing challenges that coaching could address?
        2. Are they showing openness to receiving help or guidance?
        3. Is there evidence they might be a professional who could afford coaching?
        4. Level of engagement and thoughtfulness in their post
        
        Return your analysis and final score in this format:
        Analysis: [your analysis]
        Score: [0.0-1.0]
        """
    
    def score_linkedin_leads(self, csv_path: str = "data/linkedin_leads.csv", output_path: str = "data/output/scored_linkedin_leads.csv", max_leads: int = None) -> List[Dict[str, Any]]:
        """
        Score LinkedIn leads from a CSV file.
        
        Args:
            csv_path: Path to LinkedIn leads CSV
            output_path: Path to save scored leads
            max_leads: Maximum number of leads to score
            
        Returns:
            List of scored leads
        """
        try:
            if not os.path.exists(csv_path):
                logger.error(f"LinkedIn leads file not found: {csv_path}")
                return []
                
            # Load leads from CSV
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded {len(df)} LinkedIn leads from {csv_path}")
            
            # Convert to list of dictionaries
            leads = df.to_dict('records')
            
            # Limit the number of leads if specified
            if max_leads and len(leads) > max_leads:
                leads = leads[:max_leads]
                logger.info(f"Limited to {max_leads} LinkedIn leads")
            
            # Score the leads
            scored_leads = self.score_leads(leads)
            logger.info(f"Scored {len(scored_leads)} LinkedIn leads")
            
            # Convert back to DataFrame and save
            scored_df = pd.DataFrame(scored_leads)
            scored_df.to_csv(output_path, index=False)
            logger.info(f"Saved scored LinkedIn leads to {output_path}")
            
            return scored_leads
            
        except Exception as e:
            logger.error(f"Error scoring LinkedIn leads: {str(e)}")
            return []
    
    def score_reddit_leads(self, csv_path: str = "data/reddit_leads.csv", output_path: str = "data/output/scored_reddit_leads.csv", max_leads: int = None) -> List[Dict[str, Any]]:
        """
        Score Reddit leads from a CSV file.
        
        Args:
            csv_path: Path to Reddit leads CSV
            output_path: Path to save scored leads
            max_leads: Maximum number of leads to score
            
        Returns:
            List of scored leads
        """
        try:
            if not os.path.exists(csv_path):
                logger.error(f"Reddit leads file not found: {csv_path}")
                return []
                
            # Load leads from CSV
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded {len(df)} Reddit leads from {csv_path}")
            
            # Convert to list of dictionaries
            leads = df.to_dict('records')
            
            # Limit the number of leads if specified
            if max_leads and len(leads) > max_leads:
                leads = leads[:max_leads]
                logger.info(f"Limited to {max_leads} Reddit leads")
            
            # Score the leads
            scored_leads = self.score_leads(leads)
            logger.info(f"Scored {len(scored_leads)} Reddit leads")
            
            # Convert back to DataFrame and save
            scored_df = pd.DataFrame(scored_leads)
            scored_df.to_csv(output_path, index=False)
            logger.info(f"Saved scored Reddit leads to {output_path}")
            
            return scored_leads
            
        except Exception as e:
            logger.error(f"Error scoring Reddit leads: {str(e)}")
            return []

# Function to be imported and used by main.py
def run_lead_scorer(sheets_client=None, max_linkedin_leads=50, max_reddit_leads=50, use_ai_analysis=False, model="gpt-4", threshold=0.5):
    """
    Runs the lead scorer and returns scored leads.
    
    Args:
        sheets_client: Google Sheets client for saving results
        max_linkedin_leads: Maximum number of LinkedIn leads to score
        max_reddit_leads: Maximum number of Reddit leads to score
        use_ai_analysis: Whether to use AI for advanced scoring
        model: OpenAI model to use for AI scoring
        threshold: Score threshold for qualifying leads
        
    Returns:
        Dict with scoring results
    """
    try:
        logger.info(f"Starting lead scorer (AI: {use_ai_analysis}, Model: {model})")
        results = {
            "linkedin_leads_scored": 0,
            "reddit_leads_scored": 0,
            "total_leads_scored": 0,
            "high_priority_leads": 0
        }
        
        # Create scorer
        scorer = LeadScorer(threshold=threshold, use_ai=use_ai_analysis, model=model)
        
        # Score LinkedIn leads
        linkedin_leads = scorer.score_linkedin_leads(
            max_leads=max_linkedin_leads
        )
        results["linkedin_leads_scored"] = len(linkedin_leads)
        
        # Score Reddit leads
        reddit_leads = scorer.score_reddit_leads(
            max_leads=max_reddit_leads
        )
        results["reddit_leads_scored"] = len(reddit_leads)
        
        # Count high-priority leads
        high_priority_linkedin = sum(1 for lead in linkedin_leads if lead.get("qualified", False))
        high_priority_reddit = sum(1 for lead in reddit_leads if lead.get("qualified", False))
        
        results["high_priority_leads"] = high_priority_linkedin + high_priority_reddit
        results["total_leads_scored"] = results["linkedin_leads_scored"] + results["reddit_leads_scored"]
        
        # Save to Google Sheets if provided
        if sheets_client:
            try:
                # Save LinkedIn leads to Google Sheets
                if linkedin_leads:
                    worksheet = sheets_client.open('LeadGenerationData').worksheet('ScoredLeads')
                    
                    # Clear existing data
                    worksheet.clear()
                    
                    # Add header row
                    header = ["Source", "Name/Username", "Score", "Qualified", "Details", "URL"]
                    worksheet.append_row(header)
                    
                    # Add LinkedIn leads
                    for lead in linkedin_leads:
                        if lead.get("qualified", False):
                            row = [
                                "LinkedIn",
                                lead.get("name", "Unknown"),
                                lead.get("final_score", 0),
                                "Yes" if lead.get("qualified", False) else "No",
                                lead.get("headline", ""),
                                lead.get("profile_url", "")
                            ]
                            worksheet.append_row(row)
                    
                    # Add Reddit leads
                    for lead in reddit_leads:
                        if lead.get("qualified", False):
                            row = [
                                "Reddit",
                                lead.get("username", "Unknown"),
                                lead.get("final_score", 0),
                                "Yes" if lead.get("qualified", False) else "No",
                                lead.get("post_title", ""),
                                lead.get("post_url", "")
                            ]
                            worksheet.append_row(row)
                    
                    logger.info(f"Saved {high_priority_linkedin + high_priority_reddit} qualified leads to Google Sheets")
            except Exception as e:
                logger.error(f"Error saving scored leads to Google Sheets: {str(e)}")
        
        logger.info(f"Lead scoring completed. Scored {results['total_leads_scored']} leads, {results['high_priority_leads']} qualified")
        return results
        
    except Exception as e:
        logger.error(f"Error running lead scorer: {str(e)}")
        return {
            "linkedin_leads_scored": 0,
            "reddit_leads_scored": 0,
            "total_leads_scored": 0,
            "high_priority_leads": 0,
            "error": str(e)
        }

# For testing
if __name__ == "__main__":
    results = run_lead_scorer(max_linkedin_leads=20, max_reddit_leads=20, use_ai_analysis=False)
    print(f"Scored {results['total_leads_scored']} leads, {results['high_priority_leads']} qualified")
