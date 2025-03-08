import os
import re
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='lead_scorer.log'
)
logger = logging.getLogger('lead_scorer')

class LeadScorer:
    """Class to evaluate and score leads based on engagement and data."""

    def __init__(self, threshold: float = 0.5):
        """Initialize Lead Scorer with a scoring threshold."""
        self.threshold = threshold

    def score_leads(self, leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score leads based on predefined criteria."""
        scored_leads = []
        
        for lead in leads:
            engagement_score = lead.get("engagement_score", 0)
            response_likelihood = lead.get("response_likelihood", 0)
            final_score = (engagement_score * 0.6) + (response_likelihood * 0.4)
            
            lead["final_score"] = final_score
            lead["qualified"] = final_score >= self.threshold
            scored_leads.append(lead)
        
        return scored_leads

# Function to be imported and used by GUI
def run_lead_scorer(leads: List[Dict[str, Any]], threshold: float = 0.5):
    """Runs the lead scorer and returns scored leads."""
    scorer = LeadScorer(threshold)
    return scorer.score_leads(leads)
