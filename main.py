#!/usr/bin/env python3
"""
Lead Generation Automation Tool
------------------------------
A complete system for automating lead generation from LinkedIn and Reddit,
including personalized message generation, lead scoring, and reporting.
"""

import os
import sys
import logging
import traceback
import argparse
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

# Ensure necessary directories exist
os.makedirs('logs', exist_ok=True)
os.makedirs('data', exist_ok=True)
os.makedirs('data/cache', exist_ok=True)
os.makedirs('data/output', exist_ok=True)
os.makedirs('debug', exist_ok=True)

# Configure base logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/lead_generation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('main')

# Load environment variables
load_dotenv()

def check_environment() -> bool:
    """Check that all required environment variables are set."""
    required_vars = [
        'LINKEDIN_USERNAME',
        'LINKEDIN_PASSWORD',
        'REDDIT_CLIENT_ID',
        'REDDIT_CLIENT_SECRET',
        'REDDIT_USERNAME',
        'REDDIT_PASSWORD',
        'OPENAI_API_KEY',
        'EMAIL_ADDRESS',
        'EMAIL_PASSWORD',
        'GOOGLE_SHEETS_CREDENTIALS_FILE'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing environment variables: {', '.join(missing_vars)}")
        print(f"Error: Missing environment variables: {', '.join(missing_vars)}")
        print("Please create a .env file with all required variables.")
        return False
    
    return True

def check_dependencies() -> bool:
    """Check that all required Python dependencies are installed."""
    try:
        # Check core dependencies one by one to pinpoint any issues
        print("Checking dependencies...")
        
        # Web scraping
        import selenium
        print("✓ Selenium")
        import bs4
        print("✓ BeautifulSoup")
        
        # API clients
        import praw
        print("✓ PRAW (Reddit API)")
        import openai
        print("✓ OpenAI API")
        import gspread
        print("✓ gspread (Google Sheets API)")
        import googleapiclient
        print("✓ Google API Client")
        
        # Data processing
        import pandas
        print("✓ Pandas")
        import numpy
        print("✓ NumPy")
        
        # Environment & GUI
        import dotenv
        print("✓ python-dotenv")
        import tkinter
        print("✓ tkinter")
        
        print("All dependencies successfully imported!")
        logger.info("All required dependencies are installed")
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {str(e)}")
        print(f"Error: Missing dependency: {str(e)}")
        print("Please install all required dependencies using 'pip install -r requirements.txt'")
        return False

def test_google_sheets_connection():
    """Test connection to Google Sheets."""
    try:
        print("Testing Google Sheets connection...")
        
        # Import sheets_manager module
        from utils.sheets_manager import get_sheets_client, create_sheet_if_not_exists
        
        # Try connecting
        client = get_sheets_client()
        
        # Try creating a test sheet
        worksheet = create_sheet_if_not_exists('LeadGenerationData', 'TestSheet')
        
        # Write a test row
        worksheet.append_row(['Test', 'Data', datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        
        print("✓ Google Sheets connection successful!")
        return True
    except Exception as e:
        logger.error(f"Error connecting to Google Sheets: {str(e)}")
        print(f"Error connecting to Google Sheets: {str(e)}")
        print("\nPossible troubleshooting steps:")
        print("1. Verify your credentials.json file is correct and in the right location")
        print("2. Make sure you've enabled the Google Sheets API in your Google Cloud Console")
        print("3. Check that your GOOGLE_SHEETS_SPREADSHEET_ID in .env is correct")
        return False

def start_gui():
    """Start the Lead Generation GUI."""
    try:
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Import gui module and create the GUI application
        from gui.lead_gen_gui import LeadGenerationGUI
        import tkinter as tk
        
        root = tk.Tk()
        app = LeadGenerationGUI(root)
        root.mainloop()
    except Exception as e:
        logger.error(f"Error starting GUI: {str(e)}")
        print(f"Error starting GUI: {str(e)}")
        print(f"Error details: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        print("\nPossible troubleshooting steps:")
        print("1. Check that GUI module exists in the correct location")
        print("2. Ensure all required dependencies are installed (especially tkinter)")
        print("3. Check the import paths in main.py and GUI files")
        sys.exit(1)

def run_linkedin_scraper(args):
    """Run LinkedIn scraper component."""
    try:
        from scrapers.linkedin_scraper import run_linkedin_scraper
        from utils.sheets_manager import get_sheets_client
        
        print("Starting LinkedIn scraper...")
        sheets_client = get_sheets_client()
        
        # Get max leads from args or use default
        max_leads = getattr(args, 'max_leads', 50)
        headless = getattr(args, 'headless', True)
        
        # Run the scraper
        results = run_linkedin_scraper(
            sheets_client=sheets_client,
            max_leads=max_leads,
            headless=headless
        )
        
        print(f"LinkedIn scraper completed. Collected {results.get('leads_scraped', 0)} leads.")
        return results
    except Exception as e:
        logger.error(f"Error running LinkedIn scraper: {str(e)}")
        print(f"Error running LinkedIn scraper: {str(e)}")
        traceback.print_exc()
        return {
            "leads_scraped": 0,
            "source": "linkedin",
            "success": False,
            "error": str(e)
        }

def run_reddit_scraper(args) -> Dict[str, Any]:
    """Run Reddit scraper component."""
    try:
        from scrapers.reddit_scraper import run_reddit_scraper
        from utils.sheets_manager import get_sheets_client
        
        print("Starting Reddit scraper...")
        sheets_client = get_sheets_client()
        
        # Get parameters from args
        max_leads = getattr(args, 'max_leads', 50)
        save_csv = getattr(args, 'save_csv', True)
        subreddits = getattr(args, 'subreddits', None)
        keywords = getattr(args, 'keywords', None)
        time_filter = getattr(args, 'time_filter', "month")
        post_limit = getattr(args, 'post_limit', 100)
        
        # Run the scraper
        leads = run_reddit_scraper(
            sheets_client=sheets_client,
            subreddits=subreddits,
            keywords=keywords,
            time_filter=time_filter,
            post_limit=post_limit,
            save_csv=save_csv,
            max_leads=max_leads
        )
        
        results = {
            "leads_scraped": len(leads),
            "source": "reddit",
            "success": True
        }
        
        print(f"Reddit scraper completed. Collected {len(leads)} leads.")
        return results
    except Exception as e:
        logger.error(f"Error running Reddit scraper: {str(e)}")
        print(f"Error running Reddit scraper: {str(e)}")
        traceback.print_exc()
        return {
            "leads_scraped": 0,
            "source": "reddit",
            "success": False,
            "error": str(e)
        }

def run_lead_scorer(args) -> Dict[str, Any]:
    """Run lead scoring component."""
    try:
        from analysis.lead_scorer import run_lead_scorer
        from utils.sheets_manager import get_sheets_client
        
        print("Starting lead scoring...")
        sheets_client = get_sheets_client()
        
        # Get parameters from args or use defaults
        max_linkedin_leads = getattr(args, 'max_linkedin_leads', 50)
        max_reddit_leads = getattr(args, 'max_reddit_leads', 50)
        use_ai_analysis = getattr(args, 'use_ai', True)
        model = getattr(args, 'model', "gpt-4")
        threshold = getattr(args, 'threshold', 0.5)
        
        # Run the lead scorer
        results = run_lead_scorer(
            sheets_client=sheets_client,
            max_linkedin_leads=max_linkedin_leads,
            max_reddit_leads=max_reddit_leads,
            use_ai_analysis=use_ai_analysis,
            model=model,
            threshold=threshold
        )
        
        results['success'] = True
        
        print(f"Lead scoring completed. Processed {results.get('total_leads_scored', 0)} leads.")
        return results
    except Exception as e:
        logger.error(f"Error running lead scorer: {str(e)}")
        print(f"Error running lead scorer: {str(e)}")
        traceback.print_exc()
        return {
            "leads_scored": 0,
            "success": False,
            "error": str(e)
        }

def run_message_generator(args) -> Dict[str, Any]:
    """Run message generation component."""
    try:
        from communication.message_generator import run_message_generator
        from utils.sheets_manager import get_sheets_client
        
        print("Starting message generation...")
        sheets_client = get_sheets_client()
        
        # Get parameters from args or use defaults
        max_linkedin_leads = getattr(args, 'max_linkedin_leads', 10)
        max_reddit_leads = getattr(args, 'max_reddit_leads', 10)
        model = getattr(args, 'model', "gpt-4")
        
        # Run the message generator
        results = run_message_generator(
            sheets_client=sheets_client,
            max_linkedin_leads=max_linkedin_leads,
            max_reddit_leads=max_reddit_leads,
            model=model
        )
        
        results['success'] = True
        
        print(f"Message generation completed. Generated {results.get('total_messages_generated', 0)} messages.")
        return results
    except Exception as e:
        logger.error(f"Error running message generator: {str(e)}")
        print(f"Error running message generator: {str(e)}")
        traceback.print_exc()
        return {
            "messages_generated": 0,
            "success": False,
            "error": str(e)
        }

def run_email_reporter(args) -> Dict[str, Any]:
    """Run email reporting component."""
    try:
        from reporting.email_reporter import run_email_reporter
        from utils.sheets_manager import get_sheets_client
        
        print("Starting email reporter...")
        sheets_client = get_sheets_client()
        
        # Get parameters from args or use defaults
        days_back = getattr(args, 'days_back', 1)
        response_days = getattr(args, 'response_days', 7)
        
        # Run the email reporter
        success = run_email_reporter(
            sheets_client=sheets_client,
            days_back=days_back,
            response_days=response_days
        )
        
        results = {
            "emails_sent": 1 if success else 0,
            "success": success
        }
        
        if success:
            print("Email report sent successfully!")
        else:
            print("Failed to send email report.")
            
        return results
    except Exception as e:
        logger.error(f"Error running email reporter: {str(e)}")
        print(f"Error running email reporter: {str(e)}")
        traceback.print_exc()
        return {
            "emails_sent": 0,
            "success": False,
            "error": str(e)
        }

def run_full_pipeline(args) -> Dict[str, Any]:
    """Run the complete lead generation pipeline."""
    results = {
        "components": {},
        "success": True,
        "total_leads": 0,
        "total_messages": 0
    }
    
    print("\n=== Starting Full Pipeline ===\n")
    
    # Step 1: Run LinkedIn scraper
    if getattr(args, 'run_linkedin', True):
        linkedin_results = run_linkedin_scraper(args)
        results["components"]["linkedin"] = linkedin_results
        results["total_leads"] += linkedin_results.get("leads_scraped", 0)
        
        if not linkedin_results.get("success", False):
            results["success"] = False
    
    # Step 2: Run Reddit scraper
    if getattr(args, 'run_reddit', True):
        reddit_results = run_reddit_scraper(args)
        results["components"]["reddit"] = reddit_results
        results["total_leads"] += reddit_results.get("leads_scraped", 0)
        
        if not reddit_results.get("success", False):
            results["success"] = False
    
    # Step 3: Run lead scorer
    if getattr(args, 'run_scorer', True):
        scorer_results = run_lead_scorer(args)
        results["components"]["scorer"] = scorer_results
        
        if not scorer_results.get("success", False):
            results["success"] = False
    
    # Step 4: Run message generator
    if getattr(args, 'run_messages', True):
        message_results = run_message_generator(args)
        results["components"]["messages"] = message_results
        results["total_messages"] += message_results.get("total_messages_generated", 0)
        
        if not message_results.get("success", False):
            results["success"] = False
    
    # Step 5: Run email reporter
    if getattr(args, 'run_email', True):
        email_results = run_email_reporter(args)
        results["components"]["email"] = email_results
        
        if not email_results.get("success", False):
            results["success"] = False
    
    # Print summary
    print("\n=== Pipeline Summary ===")
    print(f"Total Leads Collected: {results['total_leads']}")
    print(f"Total Messages Generated: {results['total_messages']}")
    print(f"Overall Status: {'Success' if results['success'] else 'Some components failed'}")
    print("=========================\n")
    
    return results

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description='Lead Generation Automation Tool')
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # GUI command
    gui_parser = subparsers.add_parser('gui', help='Start the graphical user interface')
    
    # LinkedIn scraper command
    linkedin_parser = subparsers.add_parser('linkedin', help='Run LinkedIn scraper')
    linkedin_parser.add_argument('--max-leads', type=int, default=50, help='Maximum number of leads to collect')
    linkedin_parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    
    # Reddit scraper command
    reddit_parser = subparsers.add_parser('reddit', help='Run Reddit scraper')
    reddit_parser.add_argument('--max-leads', type=int, default=50, help='Maximum number of leads to collect')
    reddit_parser.add_argument('--save-csv', action='store_true', help='Save results to CSV')
    reddit_parser.add_argument('--time-filter', choices=['day', 'week', 'month', 'year', 'all'], default='month', help='Time filter for posts')
    reddit_parser.add_argument('--post-limit', type=int, default=100, help='Maximum posts per subreddit')
    
    # Lead scorer command
    scorer_parser = subparsers.add_parser('scorer', help='Run lead scorer')
    scorer_parser.add_argument('--max-linkedin', type=int, dest='max_linkedin_leads', default=50)
    scorer_parser.add_argument('--max-reddit', type=int, dest='max_reddit_leads', default=50)
    scorer_parser.add_argument('--no-ai', dest='use_ai', action='store_false', help='Disable AI analysis')
    scorer_parser.add_argument('--model', choices=['gpt-4', 'gpt-3.5-turbo'], default='gpt-4')
    scorer_parser.add_argument('--threshold', type=float, default=0.5, help='Score threshold (0.0-1.0)')
    
    # Message generator command
    message_parser = subparsers.add_parser('messages', help='Run message generator')
    message_parser.add_argument('--max-linkedin', type=int, dest='max_linkedin_leads', default=10)
    message_parser.add_argument('--max-reddit', type=int, dest='max_reddit_leads', default=10)
    message_parser.add_argument('--model', choices=['gpt-4', 'gpt-3.5-turbo'], default='gpt-4')
    
    # Email reporter command
    email_parser = subparsers.add_parser('email', help='Run email reporter')
    email_parser.add_argument('--days-back', type=int, default=1)
    email_parser.add_argument('--response-days', type=int, default=7)
    
    # Pipeline command
    pipeline_parser = subparsers.add_parser('pipeline', help='Run the full pipeline')
    pipeline_parser.add_argument('--no-linkedin', dest='run_linkedin', action='store_false')
    pipeline_parser.add_argument('--no-reddit', dest='run_reddit', action='store_false')
    pipeline_parser.add_argument('--no-scorer', dest='run_scorer', action='store_false')
    pipeline_parser.add_argument('--no-messages', dest='run_messages', action='store_false')
    pipeline_parser.add_argument('--no-email', dest='run_email', action='store_false')
    pipeline_parser.add_argument('--max-leads', type=int, default=50)
    pipeline_parser.add_argument('--model', choices=['gpt-4', 'gpt-3.5-turbo'], default='gpt-4')
    pipeline_parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Check environment and dependencies
    if not check_environment():
        return
        
    if not check_dependencies():
        return
    
    if args.command == 'gui':
        # Start the GUI
        start_gui()
    elif args.command == 'linkedin':
        # Run LinkedIn scraper
        run_linkedin_scraper(args)
    elif args.command == 'reddit':
        # Run Reddit scraper
        run_reddit_scraper(args)
    elif args.command == 'scorer':
        # Run lead scorer
        run_lead_scorer(args)
    elif args.command == 'messages':
        # Run message generator
        run_message_generator(args)
    elif args.command == 'email':
        # Run email reporter
        run_email_reporter(args)
    elif args.command == 'pipeline':
        # Run full pipeline
        run_full_pipeline(args)
    else:
        # Default: start GUI
        start_gui()


if __name__ == "__main__":
    print("\n================================")
    print("Starting Lead Generation Tool...")
    print("================================\n")
    
    main()
