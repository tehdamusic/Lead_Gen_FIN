"""
Utility functions for LinkedIn scraper.
"""

import os
import time
import random
import logging
import platform
from selenium.webdriver.chrome.options import Options

# Configure logging
logger = logging.getLogger('linkedin.utils')

def find_chromedriver():
    """Find the ChromeDriver executable path."""
    # Define possible paths based on operating system
    if platform.system() == "Windows":
        possible_paths = [
            "chromedriver.exe",
            os.path.join(os.getcwd(), "chromedriver.exe"),
            os.path.join(os.getcwd(), "drivers", "chromedriver.exe"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "drivers", "chromedriver.exe"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "chromedriver.exe"),
        ]
    elif platform.system() == "Darwin":  # macOS
        possible_paths = [
            "chromedriver",
            os.path.join(os.getcwd(), "chromedriver"),
            os.path.join(os.getcwd(), "drivers", "chromedriver"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "drivers", "chromedriver"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "chromedriver"),
        ]
    else:  # Linux
        possible_paths = [
            "chromedriver",
            os.path.join(os.getcwd(), "chromedriver"),
            os.path.join(os.getcwd(), "drivers", "chromedriver"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "drivers", "chromedriver"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "chromedriver"),
            "/usr/local/bin/chromedriver",
            "/usr/bin/chromedriver",
        ]

    # Check if any of the possible paths exist
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"Found ChromeDriver at: {path}")
            # Check if the file is executable
            if os.access(path, os.X_OK) or platform.system() == "Windows":
                return path
            else:
                logger.warning(f"ChromeDriver found at {path} but is not executable")
    
    # If we get here, no ChromeDriver was found
    logger.error("ChromeDriver not found in any expected location.")
    logger.error(f"Tried: {possible_paths}")
    raise FileNotFoundError("ChromeDriver not found. Please ensure it is in one of the expected locations and is executable.")

def get_random_user_agent():
    """Return a random user agent string to avoid detection."""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0"
    ]
    return random.choice(user_agents)

def configure_chrome_options(headless=False):
    """
    Configure Chrome options with anti-bot measures.
    
    Args:
        headless: Whether to run Chrome in headless mode
        
    Returns:
        Configured Chrome options
    """
    options = Options()
    if headless:
        options.add_argument("--headless")
    
    # Randomize user agent
    options.add_argument(f"user-agent={get_random_user_agent()}")
    
    # Add additional plugins and preferences
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # Additional advanced options
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.default_content_settings.popups": 0,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)
    
    # Basic anti-detection measures
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")
    
    return options

def random_sleep(min_seconds=1, max_seconds=3):
    """Sleep for a random amount of time to avoid detection."""
    sleep_time = random.uniform(min_seconds, max_seconds)
    time.sleep(sleep_time)
    return sleep_time

def save_profiles_to_csv(profiles, filename):
    """
    Save profiles to CSV file.
    
    Args:
        profiles: List of profile dictionaries
        filename: Output CSV filename
    """
    import csv
    
    # Define CSV columns
    fieldnames = ["index", "name", "headline", "location", "profile_url", 
                "coaching_fit_score", "coaching_notes"]
    
    try:
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for i, profile in enumerate(profiles):
                # Ensure all fields exist
                row = {field: profile.get(field, "") for field in fieldnames}
                # Always set index
                row["index"] = i + 1
                writer.writerow(row)
        
        logger.info(f"Saved {len(profiles)} profiles to {filename}")
        return True
    except Exception as e:
        logger.error(f"Error saving profiles to CSV: {str(e)}")
        return False
