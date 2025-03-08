def __init__(self, headless=False, chromedriver_path=None):
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
    
    # Use provided path or default
    driver_path = chromedriver_path or CHROMEDRIVER_PATH
    
    # Ensure ChromeDriver exists
    if not os.path.exists(driver_path):
        logger.error(f"ChromeDriver not found at {driver_path}")
        raise FileNotFoundError(f"ChromeDriver not found at {driver_path}. Please set the CHROMEDRIVER_PATH environment variable or ensure it is downloaded.")

    # Start WebDriver
    try:
        service = Service(driver_path)
        self.driver = webdriver.Chrome(service=service, options=options)
        
        # Apply stealth mode
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
            """
        })
        
        logger.info(f"Successfully initialized WebDriver with ChromeDriver at {driver_path}.")
    except WebDriverException as e:
        logger.error(f"WebDriver failed to start: {str(e)}")
        raise RuntimeError("Failed to start Chrome WebDriver. Ensure Chrome and ChromeDriver are compatible.")
