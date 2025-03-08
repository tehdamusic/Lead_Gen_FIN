"""
Profile extraction methods for LinkedIn.
"""

import logging
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from .selectors import (
    NAME_SELECTORS, 
    HEADLINE_SELECTORS, 
    LOCATION_SELECTORS,
    ROLE_KEYWORD_SCORES,
    COACHING_KEYWORDS,
    TARGET_LOCATIONS
)

# Configure logging
logger = logging.getLogger('linkedin.extractors')

def extract_profiles_js(driver):
    """
    Extract profile information using JavaScript for better reliability.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        List of profile dictionaries
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

def extract_profiles_selenium(driver):
    """
    Extract profile information using Selenium as a fallback method.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        List of profile dictionaries
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

def extract_profiles(driver):
    """
    Extract profiles using both methods and combine results.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        List of profile dictionaries
    """
    # Try JavaScript method first (faster and more reliable)
    profiles = extract_profiles_js(driver)
    
    # If JavaScript method failed or found no profiles, try Selenium method
    if not profiles:
        logger.info("JavaScript extraction returned no results, trying Selenium extraction")
        profiles = extract_profiles_selenium(driver)
    
    # Log the results
    if profiles:
        logger.info(f"Successfully extracted {len(profiles)} profiles in total")
    else:
        logger.warning("No profiles extracted using either method")
    
    return profiles

def extract_additional_info(profile_data):
    """
    Rate the lead based on how good a fit they might be for life coaching.
    
    Args:
        profile_data: Dictionary containing profile data
        
    Returns:
        Updated profile data with scoring information
    """
    # Simple scoring criteria
    score = 50  # Base score
    
    if "headline" in profile_data:
        headline = profile_data["headline"].lower()
        
        # Check for coaching-related keywords in headline
        for keyword in COACHING_KEYWORDS:
            if keyword in headline:
                score += 5
        
        # Check for role keywords
        for keyword, points in ROLE_KEYWORD_SCORES.items():
            if keyword in headline:
                score += points
    
    # Location-based scoring - modify based on Peak Transformation's target locations
    if "location" in profile_data:
        location = profile_data["location"].lower()
        for target in TARGET_LOCATIONS:
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
        for keyword in ROLE_KEYWORD_SCORES:
            if keyword in profile_data["headline"].lower():
                notes.append(f"{profile_data['name']} is a {keyword.upper()} - key decision maker")
                role_match = True
                break
        
        if not role_match and "headline" in profile_data:
            notes.append(f"Role: {profile_data['headline']}")
    
    if "location" in profile_data:
        location_match = False
        for target in TARGET_LOCATIONS:
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
