import os
import logging
import time
import random
import requests
import zipfile
import win32api
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
from datetime import datetime

# Load environment variables
load_dotenv()

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)
os.makedirs('debug', exist_ok=True)  # Create a debug directory
os.makedirs('data', exist_ok=True)   # Create a data directory for results

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/linkedin_scraper.log'
)
logger = logging.getLogger('linkedin_scraper')

CHROMEDRIVER_DIR = "D:/lead_gen_tool/"
CHROMEDRIVER_PATH = os.path.join(CHROMEDRIVER_DIR, "chromedriver.exe")
FORCE_CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

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

    # Enhanced JavaScript profile extraction method
def extract_profiles_js(self, driver):
    """
    Updated JavaScript method to extract profile information using current LinkedIn HTML structure.
    Handles multiple possible DOM variations.
    """
    js_script = """
    function extractProfiles() {
        var profiles = []; 
        
        // Try multiple selectors to find profile containers
        var containers = [];
        
        // Method 1: Standard search results container
        var standardContainers = document.querySelectorAll('.reusable-search__result-container');
        if (standardContainers && standardContainers.length > 0) {
            containers = standardContainers;
        } 
        // Method 2: Ember view items (alternative structure)
        else {
            var emberItems = document.querySelectorAll('li.ember-view');
            if (emberItems && emberItems.length > 0) {
                containers = emberItems;
            }
        }
        
        // Process each container to extract profile information
        containers.forEach(function(container) {
            // Find profile link - try multiple selectors
            var profileLink = null;
            var linkSelectors = [
                '.app-aware-link[href*="/in/"]', 
                'a[href*="/in/"]',
                '.entity-result__title-text a',
                'a[data-control-name="search_srp_result"]'
            ];
            
            for (var i = 0; i < linkSelectors.length; i++) {
                var links = container.querySelectorAll(linkSelectors[i]);
                if (links && links.length > 0) {
                    profileLink = links[0].href;
                    break;
                }
            }
            
            if (!profileLink) return; // Skip if no profile link found
            
            // Extract name - try multiple selectors
            var name = "Unknown";
            var nameSelectors = [
                '.entity-result__title-text span[aria-hidden="true"]',
                '.entity-result__title-line a span span',
                '.actor-name',
                'span.name',
                'span[dir="ltr"]',
                '.artdeco-entity-lockup__title span'
            ];
            
            for (var j = 0; j < nameSelectors.length; j++) {
                var nameElements = container.querySelectorAll(nameSelectors[j]);
                if (nameElements && nameElements.length > 0 && nameElements[0].innerText) {
                    name = nameElements[0].innerText.trim();
                    break;
                }
            }
            
            // Extract headline - try multiple selectors
            var headline = "No headline";
            var headlineSelectors = [
                '.entity-result__primary-subtitle',
                '.search-result__info .subline-level-1',
                '.entity-result__summary span',
                '.artdeco-entity-lockup__subtitle',
                'p.subline-level-1',
                '.member-insights__title'
            ];
            
            for (var k = 0; k < headlineSelectors.length; k++) {
                var headlineElements = container.querySelectorAll(headlineSelectors[k]);
                if (headlineElements && headlineElements.length > 0 && headlineElements[0].innerText) {
                    headline = headlineElements[0].innerText.trim();
                    break;
                }
            }
            
            // Extract location - try multiple selectors
            var location = "Unknown location";
            var locationSelectors = [
                '.entity-result__secondary-subtitle',
                '.search-result__info .subline-level-2',
                '.artdeco-entity-lockup__caption',
                'p.subline-level-2',
                '.member-insights__location'
            ];
            
            for (var l = 0; l < locationSelectors.length; l++) {
                var locationElements = container.querySelectorAll(locationSelectors[l]);
                if (locationElements && locationElements.length > 0 && locationElements[0].innerText) {
                    location = locationElements[0].innerText.trim();
                    break;
                }
            }
            
            // Add extracted profile to list
            profiles.push({
                url: profileLink,
                name: name,
                headline: headline,
                location: location
            });
        });
        
        // Fallback: Search for any profile links on the page if no profiles found
        if (profiles.length === 0) {
            var allLinks = document.querySelectorAll('a[href*="/in/"]');
            allLinks.forEach(function(link) {
                if (link.href.includes('/in/')) {
                    var name = link.innerText.trim() || "Unknown";
                    if (name.length > 1) {
                        profiles.push({
                            url: link.href,
                            name: name,
                            headline: "Not available",
                            location: "Not available"
                        });
                    }
                }
            });
        }
        
        return profiles;
    }
    
    return extractProfiles();
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
        
def extract_profiles_selenium(self, driver):
    """
    Updated Selenium method to extract profile information.
    Tries multiple selector patterns to adapt to LinkedIn's changing structure.
    """
    profiles = []
    
    # Try multiple selectors for finding profile containers
    container_selectors = [
        '.reusable-search__result-container',
        'li.ember-view',
        '.entity-result',
        '.search-results__list > li',
        'ul.reusable-search__entity-result-list > li',
        '[data-chameleon-result-urn]',
        '.artdeco-list__item'
    ]
    
    # Try to find profile containers using different selectors
    found_containers = False
    for selector in container_selectors:
        try:
            containers = driver.find_elements(By.CSS_SELECTOR, selector)
            if containers and len(containers) > 0:
                logger.info(f"Found {len(containers)} profile containers using selector: {selector}")
                found_containers = True
                
                for container in containers:
                    try:
                        profile_data = {}
                        
                        # Try to find profile link
                        try:
                            link_element = container.find_element(By.CSS_SELECTOR, 'a[href*="/in/"]')
                            profile_data['url'] = link_element.get_attribute('href')
                        except NoSuchElementException:
                            # Skip if no profile link found
                            continue
                        
                        # Try to find name with multiple selectors
                        name_selectors = [
                            '.entity-result__title-text span[aria-hidden="true"]',
                            '.entity-result__title-line a span span',
                            'span.name',
                            'span[dir="ltr"]',
                            '.artdeco-entity-lockup__title span'
                        ]
                        
                        for name_selector in name_selectors:
                            try:
                                name_element = container.find_element(By.CSS_SELECTOR, name_selector)
                                profile_data['name'] = name_element.text.strip()
                                break
                            except NoSuchElementException:
                                continue
                        
                        if 'name' not in profile_data:
                            profile_data['name'] = "Unknown"
                        
                        # Try to find headline with multiple selectors
                        headline_selectors = [
                            '.entity-result__primary-subtitle',
                            '.search-result__info .subline-level-1',
                            '.artdeco-entity-lockup__subtitle',
                            'p.subline-level-1'
                        ]
                        
                        for headline_selector in headline_selectors:
                            try:
                                headline_element = container.find_element(By.CSS_SELECTOR, headline_selector)
                                profile_data['headline'] = headline_element.text.strip()
                                break
                            except NoSuchElementException:
                                continue
                        
                        if 'headline' not in profile_data:
                            profile_data['headline'] = "No headline"
                        
                        # Try to find location with multiple selectors
                        location_selectors = [
                            '.entity-result__secondary-subtitle',
                            '.search-result__info .subline-level-2',
                            '.artdeco-entity-lockup__caption',
                            'p.subline-level-2'
                        ]
                        
                        for location_selector in location_selectors:
                            try:
                                location_element = container.find_element(By.CSS_SELECTOR, location_selector)
                                profile_data['location'] = location_element.text.strip()
                                break
                            except NoSuchElementException:
                                continue
                        
                        if 'location' not in profile_data:
                            profile_data['location'] = "Unknown location"
                        
                        # Add profile to results if it has at least a URL
                        if 'url' in profile_data:
                            profiles.append(profile_data)
                    
                    except Exception as e:
                        logger.warning(f"Error extracting profile data: {str(e)}")
                        continue
                
                break  # Exit the selector loop if containers were found
            
        except Exception as e:
            logger.debug(f"Error with selector {selector}: {str(e)}")
    
    if not found_containers:
        # Fallback: Try to find any profile links directly
        try:
            all_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/in/"]')
            logger.info(f"Fallback: Found {len(all_links)} profile links directly")
            
            for link in all_links:
                try:
                    url = link.get_attribute('href')
                    if '/in/' in url:
                        text = link.text.strip()
                        if text and len(text) > 1:
                            profiles.append({
                                'url': url,
                                'name': text,
                                'headline': "Not available",
                                'location': "Not available"
                            })
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"Fallback extraction failed: {str(e)}")
    
    logger.info(f"Successfully extracted {len(profiles)} profiles via Selenium")
    return profiles
        
def extract_profiles_selenium(self, driver):
    """
    Updated Selenium method to extract profile information.
    Tries multiple selector patterns to adapt to LinkedIn's changing structure.
    """
    profiles = []
    
    # Try multiple selectors for finding profile containers
    container_selectors = [
        '.reusable-search__result-container',
        'li.ember-view',
        '.entity-result',
        '.search-results__list > li',
        'ul.reusable-search__entity-result-list > li',
        '[data-chameleon-result-urn]',
        '.artdeco-list__item'
    ]
    
    # Try to find profile containers using different selectors
    found_containers = False
    for selector in container_selectors:
        try:
            containers = driver.find_elements(By.CSS_SELECTOR, selector)
            if containers and len(containers) > 0:
                logger.info(f"Found {len(containers)} profile containers using selector: {selector}")
                found_containers = True
                
                for container in containers:
                    try:
                        profile_data = {}
                        
                        # Try to find profile link
                        try:
                            link_element = container.find_element(By.CSS_SELECTOR, 'a[href*="/in/"]')
                            profile_data['url'] = link_element.get_attribute('href')
                        except NoSuchElementException:
                            # Skip if no profile link found
                            continue
                        
                        # Try to find name with multiple selectors
                        name_selectors = [
                            '.entity-result__title-text span[aria-hidden="true"]',
                            '.entity-result__title-line a span span',
                            'span.name',
                            'span[dir="ltr"]',
                            '.artdeco-entity-lockup__title span'
                        ]
                        
                        for name_selector in name_selectors:
                            try:
                                name_element = container.find_element(By.CSS_SELECTOR, name_selector)
                                profile_data['name'] = name_element.text.strip()
                                break
                            except NoSuchElementException:
                                continue
                        
                        if 'name' not in profile_data:
                            profile_data['name'] = "Unknown"
                        
                        # Try to find headline with multiple selectors
                        headline_selectors = [
                            '.entity-result__primary-subtitle',
                            '.search-result__info .subline-level-1',
                            '.artdeco-entity-lockup__subtitle',
                            'p.subline-level-1'
                        ]
                        
                        for headline_selector in headline_selectors:
                            try:
                                headline_element = container.find_element(By.CSS_SELECTOR, headline_selector)
                                profile_data['headline'] = headline_element.text.strip()
                                break
                            except NoSuchElementException:
                                continue
                        
                        if 'headline' not in profile_data:
                            profile_data['headline'] = "No headline"
                        
                        # Try to find location with multiple selectors
                        location_selectors = [
                            '.entity-result__secondary-subtitle',
                            '.search-result__info .subline-level-2',
                            '.artdeco-entity-lockup__caption',
                            'p.subline-level-2'
                        ]
                        
                        for location_selector in location_selectors:
                            try:
                                location_element = container.find_element(By.CSS_SELECTOR, location_selector)
                                profile_data['location'] = location_element.text.strip()
                                break
                            except NoSuchElementException:
                                continue
                        
                        if 'location' not in profile_data:
                            profile_data['location'] = "Unknown location"
                        
                        # Add profile to results if it has at least a URL
                        if 'url' in profile_data:
                            profiles.append(profile_data)
                    
                    except Exception as e:
                        logger.warning(f"Error extracting profile data: {str(e)}")
                        continue
                
                break  # Exit the selector loop if containers were found
            
        except Exception as e:
            logger.debug(f"Error with selector {selector}: {str(e)}")
    
    if not found_containers:
        # Fallback: Try to find any profile links directly
        try:
            all_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/in/"]')
            logger.info(f"Fallback: Found {len(all_links)} profile links directly")
            
            for link in all_links:
                try:
                    url = link.get_attribute('href')
                    if '/in/' in url:
                        text = link.text.strip()
                        if text and len(text) > 1:
                            profiles.append({
                                'url': url,
                                'name': text,
                                'headline': "Not available",
                                'location': "Not available"
                            })
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"Fallback extraction failed: {str(e)}")
    
    logger.info(f"Successfully extracted {len(profiles)} profiles via Selenium")
    return profiles
            
    # Enhanced Selenium profile extraction method
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

    # Method used by GUI - it takes a search_url directly
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
                logger.warning(f"No profiles extracted from page {page+1}")
            
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

    def _is_logged_in(self):
        """Check if the user is logged in to LinkedIn."""
        current_url = self.driver.current_url
        return "feed" in current_url or "mynetwork" in current_url or "messaging" in current_url

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
    
    def scrape_for_coaching_leads(self, num_pages=3, target_count=50):
        """
        Scrape LinkedIn for potential life coaching leads by trying different combinations
        of industries, roles, and keywords to find the best prospects.
        
        Args:
            num_pages (int): Number of pages to scrape per search
            target_count (int): Target number of leads to find before stopping
            
        Returns:
            list: A list of dictionaries containing profile data
        """
        all_leads = []
        seen_urls = set()
        
        # Try combinations of industries and roles
        for industry in TARGET_INDUSTRIES:
            if len(all_leads) >= target_count:
                break
                
            for role in TARGET_ROLES:
                if len(all_leads) >= target_count:
                    break
                    
                # Create search query
                search_query = f"{industry} {role}"
                logger.info(f"Searching for: {search_query}")
                
                # Search and get results
                results = self.scrape_by_industry_and_role(industry, role, num_pages)
                
                # Add new unique results
                for result in results:
                    if "profile_url" in result and result["profile_url"] not in seen_urls:
                        seen_urls.add(result["profile_url"])
                        all_leads.append(result)
                
                # Sleep a bit to avoid rate limiting
                time.sleep(random.uniform(5, 10))
        
        # Try specific coaching-related keywords as well
        if len(all_leads) < target_count:
            for keyword in TARGET_KEYWORDS:
                if len(all_leads) >= target_count:
                    break
                    
                # Create search URL
                search_url = f"https://www.linkedin.com/search/results/people/?keywords={keyword.replace(' ', '%20')}&origin=GLOBAL_SEARCH_HEADER&sid=kgM"
                logger.info(f"Searching for keyword: {keyword}")
                
                # Search and get results
                results = self.scrape_profiles(search_url, num_pages=2)  # Fewer pages for keyword searches
                
                # Add new unique results
                for result in results:
                    if "profile_url" in result and result["profile_url"] not in seen_urls:
                        seen_urls.add(result["profile_url"])
                        all_leads.append(result)
                
                # Sleep to avoid rate limiting
                time.sleep(random.uniform(5, 10))
        
        # Sort by coaching fit score (highest first)
        all_leads.sort(key=lambda x: x.get('coaching_fit_score', 0), reverse=True)
        
        # Save to CSV
        self._save_profiles_to_csv(all_leads, "data/life_coaching_leads.csv")
        
        logger.info(f"Found {len(all_leads)} unique potential life coaching leads")
        return all_leads

    def close(self):
        """Close the browser and clean up resources."""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed.")

# Function to be imported and used by the GUI or main script
def run_linkedin_scraper(sheets_client=None, max_leads=50, headless=True):
    """
    Run the LinkedIn scraper as a standalone function.
    
    Args:
        sheets_client: Google Sheets client for saving results (optional)
        max_leads: Maximum number of leads to collect
        headless: Run browser in headless mode
        
    Returns:
        list: Collected leads
    """
    logger.info("Starting LinkedIn scraper...")
    
    try:
        # Initialize the scraper
        scraper = LinkedInScraper(headless=headless)
        
        # Log in to LinkedIn
        scraper.login()
        
        # Scrape for coaching leads
        leads = scraper.scrape_for_coaching_leads(num_pages=3, target_count=max_leads)
        
        # Save to Google Sheets if client provided
        if sheets_client:
            try:
                worksheet = sheets_client.open('LeadGenerationData').worksheet('LinkedInLeads')
                
                # Convert leads to rows for Google Sheets
                rows = []
                for lead in leads:
                    row = [
                        lead.get('name', 'Unknown'),
                        lead.get('headline', 'No headline'),
                        lead.get('location', 'Unknown location'),
                        lead.get('profile_url', 'No URL'),
                        lead.get('coaching_fit_score', 0),
                        lead.get('coaching_notes', '')
                    ]
                    rows.append(row)
                
                # Append to worksheet
                for row in rows:
                    worksheet.append_row(row)
                    # Sleep to avoid API rate limits
                    time.sleep(1)
                
                logger.info(f"Successfully saved {len(rows)} LinkedIn leads to Google Sheets")
            except Exception as e:
                logger.error(f"Error saving to Google Sheets: {str(e)}")
        
        # Close the browser
        scraper.close()
        
        return leads
        
    except Exception as e:
        logger.error(f"LinkedIn scraper error: {str(e)}")
        try:
            scraper.close()
        except:
            pass
        raise


if __name__ == "__main__":
    try:
        # For testing the script directly
        leads = run_linkedin_scraper(headless=False, max_leads=10)
        print(f"Found {len(leads)} LinkedIn leads")
    except Exception as e:
        print(f"Error: {e}")
