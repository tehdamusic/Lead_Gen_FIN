def run_linkedin_scraper(sheets_client=None, max_leads=50, headless=False):
    """
    Run the LinkedIn scraper as a standalone function.
    
    Args:
        sheets_client: Google Sheets client for saving results (optional)
        max_leads: Maximum number of leads to collect
        headless: Whether to run the browser in headless mode
        
    Returns:
        List of leads collected
    """
    import random
    from datetime import datetime
    
    try:
        # Create the scraper
        scraper = LinkedInScraper(headless=headless)
        
        # Run the scraper to find coaching leads
        leads = scraper.scrape_for_coaching_leads(
            num_pages=3,
            target_count=max_leads
        )
        
        # Save to Google Sheets if client provided
        if sheets_client:
            try:
                worksheet = sheets_client.open('LeadGenerationData').worksheet('LinkedInLeads')
                
                # Prepare data for sheets
                rows = []
                for lead in leads:
                    row = [
                        lead.get('name', ''), 
                        lead.get('headline', ''),
                        lead.get('location', ''),
                        lead.get('profile_url', ''),
                        lead.get('coaching_fit_score', 0),
                        lead.get('coaching_notes', '')
                    ]
                    rows.append(row)
                
                # Append to Google Sheet
                for row in rows:
                    worksheet.append_row(row)
                logger.info(f"Successfully saved {len(rows)} LinkedIn leads to Google Sheets")
            except Exception as e:
                logger.error(f"Error saving to Google Sheets: {str(e)}")
        
        # Close the scraper
        scraper.close()
        
        return leads
    except Exception as e:
        logger.error(f"Error running LinkedIn scraper: {str(e)}")
        return []"""
LinkedIn scraper for extracting lead data.
"""

import os
import time
import logging
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    WebDriverException, 
    NoSuchElementException, 
    TimeoutException, 
    StaleElementReferenceException
)

from .utils import (
    find_chromedriver, 
    configure_chrome_options, 
    random_sleep, 
    save_profiles_to_csv
)
from .extractors import (
    extract_profiles, 
    extract_additional_info
)
from .selectors import (
    NEXT_BUTTON_SELECTORS, 
    TARGET_INDUSTRIES, 
    TARGET_ROLES, 
    TARGET_KEYWORDS
)

# Ensure directories exist
os.makedirs('logs', exist_ok=True)
os.makedirs('debug', exist_ok=True)
os.makedirs('data', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/linkedin_scraper.log'
)
logger = logging.getLogger('linkedin.scraper')

class LinkedInScraper:
    """Scraper for extracting LinkedIn lead data for life coaching."""

    def __init__(self, headless=False):
        """
        Initialize the LinkedIn scraper with a Selenium WebDriver.
        
        Args:
            headless: Whether to run browser in headless mode
        """
        self.username = os.getenv("LINKEDIN_USERNAME")
        self.password = os.getenv("LINKEDIN_PASSWORD")
        self.driver = None

        if not self.username or not self.password:
            raise ValueError("LinkedIn credentials are missing. Set LINKEDIN_USERNAME and LINKEDIN_PASSWORD in your .env file.")

        # Configure Chrome options
        options = configure_chrome_options(headless=headless)
        
        # Find the ChromeDriver
        try:
            chromedriver_path = find_chromedriver()
            logger.info(f"Using ChromeDriver at: {chromedriver_path}")
        except FileNotFoundError as e:
            logger.error(f"ChromeDriver not found: {str(e)}")
            raise

        # Start WebDriver
        try:
            service = Service(chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Apply stealth mode
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
                """
            })
            
            logger.info(f"Successfully initialized WebDriver with ChromeDriver at {chromedriver_path}.")
        except WebDriverException as e:
            logger.error(f"WebDriver failed to start: {str(e)}")
            error_msg = str(e)
            if "This version of ChromeDriver only supports Chrome version" in error_msg:
                logger.error("ChromeDriver version mismatch. Please download a compatible version.")
                raise RuntimeError("ChromeDriver version doesn't match your Chrome browser version. Please download a compatible ChromeDriver from https://sites.google.com/chromium.org/driver/")
            raise RuntimeError(f"Failed to start Chrome WebDriver: {str(e)}")

    def _is_logged_in(self):
        """
        Check if the user is logged in to LinkedIn.
        
        Returns:
            True if logged in, False otherwise
        """
        current_url = self.driver.current_url
        return "feed" in current_url or "mynetwork" in current_url or "messaging" in current_url

    def _type_like_human(self, element, text):
        """
        Type text like a human would, with random delays between keystrokes.
        
        Args:
            element: Element to type into
            text: Text to type
        """
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))  # Random delay between keystrokes

    def login(self):
        """
        Log into LinkedIn and handle possible CAPTCHA.
        
        Returns:
            True if login successful, False otherwise
        """
        logger.info("Logging into LinkedIn...")
        self.driver.get("https://www.linkedin.com/login")
        
        # Allow page to load with a proper wait condition
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
        except TimeoutException:
            logger.error("Login page did not load properly")
            raise RuntimeError("LinkedIn login page failed to load")

        try:
            # Find and fill the username field
            username_field = self.driver.find_element(By.ID, "username")
            username_field.clear()
            self._type_like_human(username_field, self.username)

            # Find and fill the password field
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            self._type_like_human(password_field, self.password)

            # Submit the form
            password_field.send_keys(Keys.RETURN)
            
            # Allow time for login to complete
            time.sleep(5)

            # Check if CAPTCHA is present
            if "checkpoint/challenge" in self.driver.current_url:
                logger.warning("CAPTCHA detected. Please complete it manually.")
                input("Press ENTER after completing CAPTCHA...")

            # Verify if login was successful
            if "feed" in self.driver.current_url or "mynetwork" in self.driver.current_url:
                logger.info("Successfully logged into LinkedIn.")
                return True
            else:
                logger.warning("Login may have failed. Check for CAPTCHA or incorrect credentials.")
                # Save page source for debugging
                with open("debug/linkedin_login_debug.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                raise RuntimeError("LinkedIn login failed. CAPTCHA may be required.")

        except NoSuchElementException as e:
            logger.error(f"Login failed: {str(e)}")
            if self.driver:
                self.driver.quit()
            raise RuntimeError("LinkedIn login failed. CAPTCHA may be required.")

    def _scroll_down(self, scroll_count=5, wait_time=2):
        """
        Scroll down the page to load more profiles.
        
        Args:
            scroll_count: Number of scroll actions to perform
            wait_time: Time to wait between scrolls
            
        Returns:
            Number of scrolls performed
        """
        # Get initial page height
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scrolls_performed = 0
        
        for i in range(scroll_count):
            # Scroll to bottom of page
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            scrolls_performed += 1
            
            # Wait for page to load
            time.sleep(wait_time)
            
            # Check if we've reached the bottom
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                # Try clicking "Show more results" button if it exists
                try:
                    show_more_button = self.driver.find_element(By.CSS_SELECTOR, 
                                                           "button.artdeco-button--muted")
                    if "show more results" in show_more_button.text.lower():
                        show_more_button.click()
                        time.sleep(wait_time)
                except:
                    pass
                
                # One more check in case the button did something
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                    
            last_height = new_height
            
        return scrolls_performed

    def scrape_profiles(self, search_url, num_pages=3):
        """
        Scrapes LinkedIn profiles from a given search URL.
        
        Args:
            search_url: LinkedIn search URL to scrape
            num_pages: Number of pages to scrape
            
        Returns:
            List of dictionaries containing profile data
        """
        # Check if we need to log in first
        if not self._is_logged_in():
            logger.warning("Not logged in. Logging in first.")
            self.login()
            
        logger.info(f"Navigating to search URL: {search_url}")
        self.driver.get(search_url)
        time.sleep(5)
        
        # Add a delay between actions to avoid detection
        random_sleep(3, 5)
        
        # Save the HTML for debugging
        with open("debug/debug_linkedin.html", "w", encoding="utf-8") as f:
            f.write(self.driver.page_source)
        logger.info("Saved LinkedIn search page HTML for debugging.")
        
        # Take a screenshot as well for visual debugging
        self.driver.save_screenshot("debug/linkedin_search_page.png")
        
        profiles = []
        for page in range(num_pages):
            logger.info(f"Scraping page {page + 1} of {num_pages}")
            
            # Improved scrolling with longer wait times
            self._scroll_down(scroll_count=5, wait_time=3)
            
            # Take a screenshot after scrolling
            self.driver.save_screenshot(f"debug/linkedin_search_page_{page+1}_after_scroll.png")
            
            # Use the extractors to get profile data
            extracted_profiles = extract_profiles(self.driver)
            
            if extracted_profiles:
                page_profiles = []
                for index, profile in enumerate(extracted_profiles):
                    try:
                        # Convert from the extraction format to our standard format
                        profile_data = {
                            "index": len(profiles) + index + 1,
                            "name": profile.get('name', 'Unknown'),
                            "profile_url": profile.get('url', '').split("?")[0],
                            "headline": profile.get('headline', 'No headline'),
                            "location": profile.get('location', 'Unknown location')
                        }
                        
                        # Add scoring and additional info
                        profile_data = extract_additional_info(profile_data)
                        page_profiles.append(profile_data)
                        
                    except Exception as e:
                        logger.warning(f"Error processing profile {index}: {str(e)}")
                        continue
                
