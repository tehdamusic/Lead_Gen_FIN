"""
Scrapers package for the Lead Generation Tool.
Includes scrapers for LinkedIn and Reddit.
"""

from scrapers.linkedin import LinkedInScraper, run_linkedin_scraper
from scrapers.reddit.scraper import RedditScraper, run_scraper

__all__ = ['LinkedInScraper', 'run_linkedin_scraper', 'RedditScraper', 'run_scraper']
