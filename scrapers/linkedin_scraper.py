import os
import logging
import time
import random
import requests
import zipfile
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException, StaleElementReferenceException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/linkedin_scraper.log'
)
logger = logging.getLogger('linkedin_scraper')

# Get ChromeDriver path from environment variable or use default paths
def get_chromedriver_path():
    """Get the ChromeDriver path from environment variables or use sensible defaults."""
    env_path = os.getenv('CHROMEDRIVER_PATH')
    if env_path and os.path.exists(env_path):
        return env_path
        
    # Try to find ChromeDriver in common locations
    possible_paths = [
        # Current directory
        os.path.join(os.getcwd(), "chromedriver.exe"),
        os.path.join(os.getcwd(), "chromedriver"),
        
        # Tool directory
        os.path.join(os.getcwd(), "tools", "chromedriver.exe"),
        os.path.join(os.getcwd(), "tools", "chromedriver"),
        
        # Drivers directory
        os.path.join(os.getcwd(), "drivers", "chromedriver.exe"),
        os.path.join(os.getcwd(), "drivers", "chromedriver"),
        
        # Old hard-coded path as fallback
        os.path.join("D:/lead_gen_tool/", "chromedriver.exe"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"Found ChromeDriver at: {path}")
            return path
            
    # Return the first path as default - this will fail if the file doesn't exist
    # but at least the error will be clear about where it was looking
    return possible_paths[0]

CHROMEDRIVER_PATH = get_chromedriver_path()

# Define target audiences for life coaching
TARGET_INDUSTRIES = [
    "Technology", 
    "Finance", 
    "Healthcare", 
    "Education", 
    "Consulting", 
    "Media",
    "Marketing",
    "Entrepreneurship",
    "Human Resources"
]

TARGET_ROLES = [
    "CEO", 
    "CTO", 
    "CFO", 
    "Director", 
    "Manager", 
    "Executive", 
    "VP", 
    "President",
    "Founder",
    "Owner",
    "Leader",
    "Head",
    "Professional"
]

TARGET_KEYWORDS = [
    "career transition",
    "professional development",
    "leadership development",
    "work life balance",
    "burnout",
    "career growth",
    "personal development",
    "executive coaching",
    "leadership coaching",
    "professional coaching",
    "business coaching",
    "transformation"
]

class LinkedInScraper:
    """Scraper for extracting LinkedIn lead data for life coaching."""

    def __init__(self, headless=False):
        """Initialize the LinkedIn scraper with a Selenium WebDriver."""
        self.username = os.getenv("LINKEDIN_USERNAME")
        self.password = os.getenv("LINKEDIN_PASSWORD")

        if not self.username or not self.password:
            raise ValueError("LinkedIn credentials are missing. Set LINKEDIN_USERNAME and LINKEDIN_PASSWORD in your .env file.")

        options = Options()
        if headless:
            options.add_argument("--headless")
        
        # Add anti-bot measures
        options = self._add_anti_bot_measures(options)
        
        # Ensure ChromeDriver exists
        if not os.path.exists(CHROMEDRIVER_PATH):
            raise FileNotFoundError(f"ChromeDriver not found at {CHROMEDRIVER_PATH}. Ensure it is downloaded.")

        # Start WebDriver
        try:
            service = Service(CHROMEDRIVER_PATH)
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Apply stealth mode
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
                """
            })
            
            logger.info(f"Successfully initialized WebDriver with ChromeDriver at {CHROMEDRIVER_PATH}.")
        except WebDriverException as e:
            logger.error(f"WebDriver failed to start: {str(e)}")
            raise RuntimeError("Failed to start Chrome WebDriver. Ensure Chrome and ChromeDriver are compatible.")

    def _rotate_user_agent(self):
        """Rotate user agent to avoid detection."""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0"
        ]
        return random.choice(user_agents)

    def _add_anti_bot_measures(self, options):
        """Add additional anti-bot measures to Chrome options."""
        # Randomize user agent
        options.add_argument(f"user-agent={self._rotate_user_agent()}")
        
        # Add additional plugins and preferences that make us look more like a real browser
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
        
    def _random_sleep(self, min_seconds=1, max_seconds=3):
        """Sleep for a random amount of time to avoid detection."""
        time.sleep(random.uniform(min_seconds, max_seconds))

    def login(self):
        """Log into LinkedIn and handle possible CAPTCHA."""
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
            else:
                logger.warning("Login may have failed. Check for CAPTCHA or incorrect credentials.")
                # Save page source for debugging
                with open("debug/linkedin_login_debug.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                raise RuntimeError("LinkedIn login failed. CAPTCHA may be required.")

        except NoSuchElementException as e:
            logger.error(f"Login failed: {str(e)}")
            self.driver.quit()
            raise RuntimeError("LinkedIn login failed. CAPTCHA may be required.")

    def _type_like_human(self, element, text):
        """Type text like a human would, with random delays between keystrokes."""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))  # Random delay between keystrokes

    def _scroll_down(self, scroll_count=5, wait_time=2):
        """Scroll down the page to load more profiles."""
        # Get initial page height
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        for i in range(scroll_count):
            # Scroll to bottom of page
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
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
    
    def _extract_additional_info(self, profile_data):
        """
        Rate the lead based on how good a fit they might be for life coaching.
        This is a very simple model and could be enhanced with more advanced scoring.
        """
        # Simple scoring criteria
        score = 50  # Base score
        
        # Title/role-based scoring
        role_keywords = {
            "ceo": 20, "chief executive": 20, "founder": 15, "president": 15,
            "director": 10, "manager": 8, "head": 8, "vp": 10, "vice president": 10,
            "leader": 5, "executive": 10, "officer": 5, "professional": 3,
            "hr": 5, "human resources": 5
        }
        
        if "headline" in profile_data:
            headline = profile_data["headline"].lower()
            
            # Check for coaching-related keywords in headline
            coaching_keywords = ["development", "growth", "transition", "leadership", 
                                "change", "transform", "burnout", "balance", "career"]
            
            for keyword in coaching_keywords:
                if keyword in headline:
                    score += 5
            
            # Check for role keywords
            for keyword, points in role_keywords.items():
                if keyword in headline:
                    score += points
        
        # Location-based scoring - modify based on Peak Transformation's target locations
        target_locations = ["london", "uk", "united kingdom", "england", 
                           "manchester", "birmingham", "leeds", "bristol"]
        
        if "location" in profile_data:
            location = profile_data["location"].lower()
            for target in target_locations:
                if target in location:
                    score += 10
                    break
        
        # Cap the score at 100
        score = min(score, 100)
        
        # Add the score to the profile data
        profile_data["coaching_fit_score"] = score
        
        # Add a few notes about why this might be a good lead
        notes = []
        if "headline" in profile_data and "name" in profile_data:
            role_match = False
            for keyword in role_keywords:
                if keyword in profile_data["headline"].lower():
                    notes.append(f"{profile_data['name']} is a {keyword.upper()} - key decision maker")
                    role_match = True
                    break
            
            if not role_match and "headline" in profile_data:
                notes.append(f"Role: {profile_data['headline']}")
        
        if "location" in profile_data:
            location_match = False
            for target in target_locations:
                if target in profile_data["location"].lower():
                    notes.append(f"Located in {profile_data['location']} - within Peak Transformation's target area")
                    location_match = True
                    break
            
            if not location_match:
                notes.append(f"Location: {profile_data['location']}")
        
        # Add Peak Transformation specific notes
        if score >= 80:
            notes.append("HIGH POTENTIAL: Executive/leadership role ideal for Peak Transformation coaching")
        elif score >= 60:
            notes.append("GOOD MATCH: Professional background aligns with Peak Transformation services")
        
        profile_data["coaching_notes"] = " | ".join(notes)
        
        return profile_data

    # New enhanced JavaScript profile extraction method
    def extract_profiles_js(self, driver):
        """
        Extract profile information using JavaScript for better reliability.
        Handles null/undefined values and uses current LinkedIn HTML structure.
        """
        js_script = """
        var profiles = []; 
        document.querySelectorAll('.reusable-search__result-container').forEach(function(profile) { 
            var nameElement = profile.querySelector('.entity-result__title-text span[aria-hidden="true"]'); 
            var linkElement = profile.querySelector('.app-aware-link[href*="/in/"]'); 
            var headlineElement = profile.querySelector('.entity-result__primary-subtitle'); 
            var locationElement = profile.querySelector('.entity-result__secondary-subtitle'); 
            
            if (linkElement) { 
                profiles.push({ 
                    url: linkElement.href.trim(), 
                    name: nameElement ? nameElement.innerText.trim() : "Unknown", 
                    headline: headlineElement ? headlineElement.innerText.trim() : "No headline", 
                    location: locationElement ? locationElement.innerText.trim() : "Unknown location" 
                }); 
            } 
        }); 
        return profiles;
        """
        
        try:
            profiles_data = driver.execute_script(js_script)
            if not profiles_data:
                logger.warning("No profiles found on the page using JavaScript extraction")
                return []
                
            logger.info(f"Successfully extracted {len(profiles_data)} profiles via JavaScript")
            return profiles_data
        except Exception as e:
            logger.error(f"JavaScript extraction failed: {str(e)}")
            return []
            
    # New enhanced Selenium profile extraction method
    def extract_profiles_selenium(self, driver):
        """
        Extract profile information using Selenium as a fallback method.
        Uses the same selectors as the JavaScript method for consistency.
        """
        profiles = []
        
        try:
            # Find all profile containers
            profile_containers = driver.find_elements(By.CSS_SELECTOR, '.reusable-search__result-container')
            
            for profile in profile_containers:
                try:
                    # Find profile link (which contains the URL)
                    link_element = profile.find_element(By.CSS_SELECTOR, '.app-aware-link[href*="/in/"]')
                    profile_url = link_element.get_attribute('href')
                    
                    # Find name, headline, and location with error handling
                    try:
                        name_element = profile.find_element(By.CSS_SELECTOR, '.entity-result__title-text span[aria-hidden="true"]')
                        profile_name = name_element.text.strip()
                    except NoSuchElementException:
                        profile_name = "Unknown"
                        
                    try:
                        headline_element = profile.find_element(By.CSS_SELECTOR, '.entity-result__primary-subtitle')
                        headline = headline_element.text.strip()
                    except NoSuchElementException:
                        headline = "No headline"
                        
                    try:
                        location_element = profile.find_element(By.CSS_SELECTOR, '.entity-result__secondary-subtitle')
                        location = location_element.text.strip()
                    except NoSuchElementException:
                        location = "Unknown location"
                    
                    # Create profile dict and add to list
                    profile_data = {
                        'url': profile_url,
                        'name': profile_name,
                        'headline': headline,
                        'location': location
                    }
                    
                    profiles.append(profile_data)
                    
                except NoSuchElementException as e:
                    logger.warning(f"Skipping a profile because of missing element: {str(e)}")
                    continue
                    
            logger.info(f"Successfully extracted {len(profiles)} profiles via Selenium")
            return profiles
            
        except Exception as e:
            logger.error(f"Selenium extraction failed: {str(e)}")
            return []
            
    # Combined extraction method that uses both approaches
    def extract_profiles(self, driver):
        """
        Extract profiles using both methods and combine results.
        JavaScript is tried first, then Selenium as fallback.
        """
        # Try JavaScript method first (faster and more reliable)
        profiles = self.extract_profiles_js(driver)
        
        # If JavaScript method failed or found no profiles, try Selenium method
        if not profiles:
            logger.info("JavaScript extraction returned no results, trying Selenium extraction")
            profiles = self.extract_profiles_selenium(driver)
        
        # Log the results
        if profiles:
            logger.info(f"Successfully extracted {len(profiles)} profiles in total")
        else:
            logger.warning("No profiles extracted using either method")
        
        return profiles

    # This is the method used by your GUI - it takes a search_url directly
    def scrape_profiles(self, search_url, num_pages=3):
        """
        Scrapes LinkedIn profiles from a given search URL.
        
        Args:
            search_url (str): LinkedIn search URL to scrape.
            num_pages (int): Number of pages to scrape.
            
        Returns:
            list: List of dictionaries containing profile data.
        """
        # Check if we need to log in first
        if not self._is_logged_in():
            logger.warning("Not logged in. Logging in first.")
            self.login()
            
        logger.info(f"Navigating to search URL: {search_url}")
        self.driver.get(search_url)
        time.sleep(5)
        
        # Add a delay between actions to avoid detection
        self._random_sleep(3, 5)
        
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
            
            # Use the new extraction methods
            extracted_profiles = self.extract_profiles(self.driver)
            
            if extracted_profiles:
                page_profiles = []
                for index, profile in enumerate(extracted_profiles):
                    try:
                        # Convert from the JavaScript format to our standard format
                        profile_data = {
                            "index": len(profiles) + index + 1,
                            "name": profile.get('name', 'Unknown'),
                            "profile_url": profile.get('url', '').split("?")[0],
                            "headline": profile.get('headline', 'No headline'),
                            "location": profile.get('location', 'Unknown location')
                        }
                        
                        # Add scoring and additional info
                        profile_data = self._extract_additional_info(profile_data)
                        page_profiles.append(profile_data)
                        
                    except Exception as e:
                        logger.warning(f"Error processing profile {index}: {str(e)}")
                        continue
                
                logger.info(f"Extracted {len(page_profiles)} profiles from page {page+1}")
                profiles.extend(page_profiles)
            else:
                # Fallback to the old method if the new ones fail completely
                logger.warning("New extraction methods failed. Falling back to the original method.")
                
                # JavaScript approach has been the most successful
                try:
                    # Extract ALL links on the page that have /in/ in them
                    profile_links = self.driver.execute_script("""
                        var links = document.getElementsByTagName('a');
                        var profileLinks = [];
                        for (var i = 0; i < links.length; i++) {
                            if (links[i].href && links[i].href.includes('/in/')) {
                                // Get name from the link text or nearby elements
                                var name = '';
                                var linkText = links[i].innerText.trim();
                                if (linkText && linkText.length > 2) {
                                    name = linkText;
                                }
                                
                                // Look for headline near the profile link
                                var headline = '';
                                var parentElement = links[i].parentElement;
                                if (parentElement) {
                                    // Look for elements that might contain the headline
                                    var subtitleElements = document.querySelectorAll('.entity-result__primary-subtitle, .search-result__subtitle');
                                    for (var j = 0; j < subtitleElements.length; j++) {
                                        if (subtitleElements[j].closest('li') === parentElement.closest('li')) {
                                            headline = subtitleElements[j].innerText.trim();
                                            break;
                                        }
                                    }
                                }
                                
                                // Look for location information
                                var location = '';
                                var locationElements = document.querySelectorAll('.entity-result__secondary-subtitle, [aria-hidden="true"]');
                                for (var j = 0; j < locationElements.length; j++) {
                                    var elementText = locationElements[j].innerText.trim();
                                    if (elementText && elementText.includes(',') && 
                                        locationElements[j].closest('li') === parentElement.closest('li')) {
                                        location = elementText;
                                        break;
                                    }
                                }
                                
                                profileLinks.push({
                                    url: links[i].href,
                                    text: name,
                                    headline: headline,
                                    location: location
                                });
                            }
                        }
                        return profileLinks;
                    """)
                    
                    logger.info(f"Found {len(profile_links)} profile links with JavaScript on page {page+1}")
                    
                    # Process these links directly
                    if profile_links and len(profile_links) > 0:
                        for link in profile_links:
                            profile_data = {
                                "index": len(profiles) + 1,
                                "profile_url": link['url'].split("?")[0]
                            }
                            
                            # Get name from link text if it's not empty
                            if link['text'] and len(link['text']) > 2:
                                profile_data["name"] = link['text'].strip()
                                
                            # Get headline from nearby text
                            if link['headline'] and len(link['headline']) > 2:
                                profile_data["headline"] = link['headline'].strip()
                                
                            # Get location if available
                            if link['location'] and len(link['location']) > 2:
                                profile_data["location"] = link['location'].strip()
                            
                            # Add scoring and additional info
                            profile_data = self._extract_additional_info(profile_data)
                            
                            profiles.append(profile_data)
                            logger.info(f"Added profile: {profile_data.get('name', 'Unknown')} - {profile_data['profile_url']}")
                    
                except Exception as e:
                    logger.warning(f"JavaScript extraction failed: {str(e)}")
                
                # Try the standard approach as a backup
                selectors_to_try = [
                    "li.reusable-search__result-container", 
                    ".entity-result",
                    "li.ember-view",
                    "[data-test-search-result]",
                    "ul.reusable-search__entity-result-list > li",
                    ".search-results__list > li",
                    "ul li.feed-search-results-list",
                    "[data-chameleon-result-urn]",  # New LinkedIn format
                    ".artdeco-list__item"  # Another common container
                ]
                
                for selector in selectors_to_try:
                    profile_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if profile_elements:
                        logger.info(f"Found {len(profile_elements)} profiles using selector: {selector}")
                        
                        page_profiles = []
                        for index, profile in enumerate(profile_elements):
                            try:
                                profile_data = self._extract_profile_data(profile, index)
                                
                                if profile_data and ('name' in profile_data or 'profile_url' in profile_data):
                                    # Add scoring and additional info
                                    profile_data = self._extract_additional_info(profile_data)
                                    
                                    page_profiles.append(profile_data)
                            except Exception as e:
                                logger.warning(f"Error extracting profile {index}: {str(e)}")
                                continue
                        
                        logger.info(f"Extracted {len(page_profiles)} profiles from page {page+1}")
                        profiles.extend(page_profiles)
                        break
            
            # Wait before going to next page to avoid being detected
            self._random_sleep(2, 4)
            
            # Try to go to the next page if there are more pages to scrape
            if page < num_pages - 1:
                next_button_clicked = False
                next_button_selectors = [
                    "button[aria-label='Next']",
                    ".artdeco-pagination__button--next",
                    ".artdeco-pagination__button.artdeco-pagination__button--next",
                    "[data-test-pagination-page-btn='next']",
                    ".artdeco-pagination__button--next:not(.artdeco-button--disabled)",
                    "li.artdeco-pagination__indicator--number.active + li a"
                ]
                
                for selector in next_button_selectors:
                    try:
                        next_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if next_buttons:
                            for btn in next_buttons:
                                if btn.is_enabled() and btn.is_displayed():
                                    self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                                    time.sleep(1)
                                    btn.click()
                                    next_button_clicked = True
                                    logger.info(f"Clicked next button with selector: {selector}")
                                    # Longer wait for page to load
                                    time.sleep(5)
                                    break
                        
                        if next_button_clicked:
                            break
                    except Exception as e:
                        logger.debug(f"Error with selector {selector}: {str(e)}")
                
                if not next_button_clicked:
                    logger.info("Next button not found or disabled. Stopping pagination.")
                    break
        
        # Deduplicate profiles based on URL
        unique_profiles = []
        seen_urls = set()
        
        for profile in profiles:
            if "profile_url" in profile and profile["profile_url"] not in seen_urls:
                seen_urls.add(profile["profile_url"])
                unique_profiles.append(profile)
        
        # Sort by coaching fit score (highest first)
        unique_profiles.sort(key=lambda x: x.get('coaching_fit_score', 0), reverse=True)
        
        logger.info(f"Scraped {len(unique_profiles)} unique profiles total.")
        
        # Save to CSV for backup
        self._save_profiles_to_csv(unique_profiles, "data/linkedin_leads.csv")
        
        return unique_profiles

    def _save_profiles_to_csv(self, profiles, filename):
        """Save profiles to CSV file."""
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
        except Exception as e:
            logger.error(f"Error saving profiles to CSV: {str(e)}")

    def scrape_by_industry_and_role(self, industry="Technology", role="Software Engineer", num_pages=3):
    """
    Scrapes LinkedIn profiles based on industry and job role.
    
    Args:
        industry (str): The industry to search for.
        role (str): The job role to search for.
        num_pages (int): The number of pages to scrape.
        
    Returns:
        list: A list of dictionaries containing profile data.
    """
    logger.info(f"Starting LinkedIn scrape for industry: {industry}, role: {role}")
    
    # Ensure the scraper is logged in before searching
    if not self._is_logged_in():
        logger.warning("Not logged in. Logging in first.")
        self.login()
    
    # Format search query
    search_query = f"{industry} {role}"
    
    # Use a more specific search URL with additional parameters
    search_url = f"https://www.linkedin.com/search/results/people/?keywords={search_query.replace(' ', '%20')}&origin=GLOBAL_SEARCH_HEADER&sid=kgM"
    
    # Call the main scrape_profiles method with our constructed URL
    return self.scrape_profiles(search_url, num_pages)

def _is_logged_in(self):
    """Check if the user is logged in to LinkedIn."""
    if not hasattr(self, 'driver') or self.driver is None:
        return False
    try:
        current_url = self.driver.current_url
        return "feed" in current_url or "mynetwork" in current_url or "messaging" in current_url
    except Exception as e:
        logger.error(f"Error checking login status: {str(e)}")
        return False

def _extract_profile_data(self, container, index):
    """Extract profile data from a container."""
    profile_data = {}
    
    # Add index for reference
    profile_data["index"] = index + 1
    
    # First, save this specific container HTML to a debug file
    try:
        container_html = container.get_attribute("outerHTML")
        with open(f"debug/profile_container_{index+1}.html", "w", encoding="utf-8") as f:
            f.write(container_html)
        logger.debug(f"Saved container HTML to debug/profile_container_{index+1}.html")
    except Exception as e:
        logger.debug(f"Could not save container HTML: {str(e)}")
    
    # Updated selectors for LinkedIn's current structure
    try:
        # Find profile links
        link_elements = container.find_elements(By.CSS_SELECTOR, "a.app-aware-link")
        for link in link_elements:
            href = link.get_attribute("href")
            if href and "/in/" in href:
                profile_data["profile_url"] = href.split("?")[0]
                break
                
        # Find name - check for the current LinkedIn structure
        name_selectors = [
            ".entity-result__title-text a",
            ".search-result__info .actor-name",
            ".app-aware-link span[aria-hidden='true']",
            ".entity-result__title-line a span span",
            "span[dir='ltr']",
            ".artdeco-entity-lockup__title span"
        ]
        
        for selector in name_selectors:
            try:
                name_elements = container.find_elements(By.CSS_SELECTOR, selector)
                for element in name_elements:
                    name_text = element.text.strip()
                    if name_text and len(name_text) > 2:
                        profile_data["name"] = name_text
                        break
                if "name" in profile_data:
                    break
            except Exception:
                continue
                
        # Find headline
        headline_selectors = [
            ".entity-result__primary-subtitle",
            ".search-result__info .subline-level-1",
            ".entity-result__summary span",
            ".entity-result__primary-subtitle span",
            ".artdeco-entity-lockup__subtitle"
        ]
        
        for selector in headline_selectors:
            try:
                headline_elements = container.find_elements(By.CSS_SELECTOR, selector)
                for element in headline_elements:
                    headline_text = element.text.strip()
                    if headline_text:
                        profile_data["headline"] = headline_text
                        break
                if "headline" in profile_data:
                    break
            except Exception:
                continue
                
        # Find location
        location_selectors = [
            ".entity-result__secondary-subtitle",
            ".search-result__info .subline-level-2",
            ".entity-result__secondary-subtitle span",
            ".artdeco-entity-lockup__caption"
        ]
        for selector in location_selectors:
            try:
                location_elements = container.find_elements(By.CSS_SELECTOR, selector)
                for element in location_elements:
                    location_text = element.text.strip()
                    if location_text and "," in location_text:
                        profile_data["location"] = location_text
                        break
                if "location" in profile_data:
                    break
            except Exception:
                continue
                
    except Exception as e:
        logger.debug(f"Error extracting profile data: {str(e)}")
    
    # If we found any meaningful data, return it
    if "profile_url" in profile_data or "name" in profile_data:
        found_fields = [k for k in profile_data.keys() if k != "index"]
        logger.info(f"Profile {index+1}: Found {', '.join(found_fields)}")
        return profile_data
    else:
        logger.warning(f"Profile {index+1}: Could not extract any data")
        return profile_data
        
def close(self):
    """Close the browser and clean up resources."""
    if self.driver:
        self.driver.quit()
        logger.info("WebDriver closed.")
