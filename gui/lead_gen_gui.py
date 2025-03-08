import os
import logging
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, StringVar
from dotenv import load_dotenv

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/gui.log'
)
logger = logging.getLogger('lead_gen_gui')

# Load environment variables
load_dotenv()

# Import the LinkedIn scraper from the scrapers package
try:
    # Make sure the parent directory is in the Python path
    import sys
    import os
    
    # Add the root directory to the path if not already there
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
    
    # Now try to import from the modular scrapers package
    from scrapers.linkedin import LinkedInScraper
    logger.info("Successfully imported LinkedInScraper from modular scrapers package")
except ImportError as e:
    logger.error(f"Failed to import LinkedInScraper: {str(e)}")
    messagebox.showerror("Import Error", 
                        f"Could not import LinkedInScraper.\n\nError: {str(e)}\n\n"
                        f"Please ensure the scrapers/linkedin package exists with the necessary files.")

# Import other modules dynamically
try:
    from scrapers.reddit_scraper import RedditScraper
    from analysis.lead_scorer import LeadScorer
    from communication.message_generator import MessageGenerator
    from reporting.email_reporter import EmailReporter
except ImportError as e:
    logger.warning(f"Optional module import error: {str(e)}")
    # We'll continue even if these modules aren't available

class LeadGenerationGUI:
    """GUI for controlling lead generation tasks."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Peak Transformation Coaching - Lead Generation")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        # Initialize variables for user input
        self.industry_var = StringVar(value="Technology")
        self.role_var = StringVar(value="CEO")
        self.num_pages_var = StringVar(value="3")
        self.keyword_var = StringVar(value="leadership development")

        # Initialize LinkedIn Scraper
        self.linkedin_scraper = None
        try:
            if LinkedInScraper is not None:
                self.linkedin_scraper = LinkedInScraper(headless=False)
                logger.info("LinkedIn Scraper initialized")
            else:
                raise ImportError("LinkedInScraper module not found")
        except Exception as e:
            logger.error(f"Failed to initialize LinkedIn Scraper: {str(e)}")
            messagebox.showerror("Initialization Error", f"Failed to initialize LinkedIn Scraper: {str(e)}\n\nPlease ensure all LinkedIn scraper modules are in the correct locations.")

        self.create_widgets()
        logger.info("GUI Initialized")
    
    def create_widgets(self):
        """Create GUI elements."""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        self.create_main_tab()
        self.create_linkedin_tab()
        self.create_coaching_tab()
        self.create_logs_tab()
    
    def create_main_tab(self):
        """Create controls for running scripts."""
        main_tab = ttk.Frame(self.notebook)
        self.notebook.add(main_tab, text="Lead Gen Tasks")

        # Add a logo or title header
        title_frame = ttk.Frame(main_tab)
        title_frame.pack(fill=tk.X, pady=20)
        
        ttk.Label(title_frame, text="Peak Transformation Coaching LTD", 
                 font=("Arial", 16, "bold")).pack()
        ttk.Label(title_frame, text="Professional Lead Generation Tool", 
                 font=("Arial", 12)).pack()
        
        # Divider
        ttk.Separator(main_tab, orient='horizontal').pack(fill=tk.X, padx=20, pady=10)
        
        # Main buttons
        buttons_frame = ttk.Frame(main_tab)
        buttons_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=20)

        ttk.Button(buttons_frame, text="LinkedIn Lead Generation", 
                  command=self.show_linkedin_tab, width=30).pack(pady=10)
        ttk.Button(buttons_frame, text="Coaching Prospect Finder", 
                  command=self.show_coaching_tab, width=30).pack(pady=10)
        ttk.Button(buttons_frame, text="Run Reddit Scraper", 
                  command=self.run_reddit_scraper, width=30).pack(pady=10)
        ttk.Button(buttons_frame, text="Generate AI Messages", 
                  command=self.run_message_generator, width=30).pack(pady=10)
        ttk.Button(buttons_frame, text="Score Leads", 
                  command=self.run_lead_scorer, width=30).pack(pady=10)
        ttk.Button(buttons_frame, text="Send Email Report", 
                  command=self.run_email_reporter, width=30).pack(pady=10)
        
        # Footer with version info
        ttk.Label(main_tab, text="v1.2.0 | © 2025 Peak Transformation Coaching LTD", 
                 font=("Arial", 8)).pack(side=tk.BOTTOM, pady=10)
    
    def create_linkedin_tab(self):
        """Create LinkedIn specific controls."""
        linkedin_tab = ttk.Frame(self.notebook)
        self.notebook.add(linkedin_tab, text="LinkedIn Scraper")
        
        # Create form for LinkedIn parameters
        form_frame = ttk.LabelFrame(linkedin_tab, text="Search Parameters", padding=20)
        form_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Industry field
        ttk.Label(form_frame, text="Industry:").grid(row=0, column=0, sticky=tk.W, pady=5)
        industry_entry = ttk.Entry(form_frame, textvariable=self.industry_var, width=30)
        industry_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Industry dropdown suggestions
        ttk.Label(form_frame, text="Suggestions:").grid(row=0, column=2, sticky=tk.W, pady=5, padx=5)
        industry_combo = ttk.Combobox(form_frame, values=[
            "Technology", "Finance", "Healthcare", "Education", "Consulting", 
            "Media", "Marketing", "Entrepreneurship", "Human Resources"
        ])
        industry_combo.bind("<<ComboboxSelected>>", 
                          lambda e: self.industry_var.set(industry_combo.get()))
        industry_combo.grid(row=0, column=3, sticky=tk.W, pady=5, padx=5)
        
        # Role field
        ttk.Label(form_frame, text="Role:").grid(row=1, column=0, sticky=tk.W, pady=5)
        role_entry = ttk.Entry(form_frame, textvariable=self.role_var, width=30)
        role_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Role dropdown suggestions
        ttk.Label(form_frame, text="Suggestions:").grid(row=1, column=2, sticky=tk.W, pady=5, padx=5)
        role_combo = ttk.Combobox(form_frame, values=[
            "CEO", "CTO", "CFO", "Director", "Manager", "Executive", 
            "VP", "President", "Founder", "Owner", "Leader"
        ])
        role_combo.bind("<<ComboboxSelected>>", 
                      lambda e: self.role_var.set(role_combo.get()))
        role_combo.grid(row=1, column=3, sticky=tk.W, pady=5, padx=5)
        
        # Number of pages
        ttk.Label(form_frame, text="Pages to scrape:").grid(row=2, column=0, sticky=tk.W, pady=5)
        pages_entry = ttk.Entry(form_frame, textvariable=self.num_pages_var, width=10)
        pages_entry.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Run button
        ttk.Button(form_frame, text="Start Scraping", 
                  command=self.run_linkedin_with_params).grid(row=3, column=0, columnspan=4, pady=20)
        
        # Results frame
        results_frame = ttk.LabelFrame(linkedin_tab, text="Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.linkedin_results = scrolledtext.ScrolledText(results_frame, height=15)
        self.linkedin_results.pack(fill=tk.BOTH, expand=True)
        
        # Add a save button for results
        button_frame = ttk.Frame(linkedin_tab)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(button_frame, text="Save Results to CSV", 
                  command=self.save_linkedin_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Results", 
                  command=self.clear_linkedin_results).pack(side=tk.LEFT, padx=5)
    
    def create_coaching_tab(self):
        """Create coaching prospects-specific tab."""
        coaching_tab = ttk.Frame(self.notebook)
        self.notebook.add(coaching_tab, text="Coaching Prospects")
        
        # Header
        ttk.Label(coaching_tab, text="Find Professional Life Coaching Prospects", 
                 font=("Arial", 12, "bold")).pack(pady=10)
        
        # Options frame
        options_frame = ttk.LabelFrame(coaching_tab, text="Search Options", padding=20)
        options_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Keyword search
        ttk.Label(options_frame, text="Search Keyword:").grid(row=0, column=0, sticky=tk.W, pady=5)
        keyword_entry = ttk.Entry(options_frame, textvariable=self.keyword_var, width=30)
        keyword_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Keyword suggestions
        ttk.Label(options_frame, text="Suggestions:").grid(row=0, column=2, sticky=tk.W, pady=5, padx=5)
        keyword_combo = ttk.Combobox(options_frame, values=[
            "leadership development", "career transition", "professional development",
            "work life balance", "burnout", "career growth", "executive coaching"
        ], width=25)
        keyword_combo.bind("<<ComboboxSelected>>", 
                         lambda e: self.keyword_var.set(keyword_combo.get()))
        keyword_combo.grid(row=0, column=3, sticky=tk.W, pady=5, padx=5)
        
        # Search buttons
        buttons_frame = ttk.Frame(options_frame)
        buttons_frame.grid(row=1, column=0, columnspan=4, pady=10)
        
        ttk.Button(buttons_frame, text="Search by Keyword", 
                  command=self.search_coaching_by_keyword).pack(side=tk.LEFT, padx=10)
                  
        ttk.Button(buttons_frame, text="Run Full Coaching Prospect Search", 
                  command=self.run_coaching_prospect_search).pack(side=tk.LEFT, padx=10)
        
        # Results frame
        results_frame = ttk.LabelFrame(coaching_tab, text="Coaching Prospects", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.coaching_results = scrolledtext.ScrolledText(results_frame, height=15)
        self.coaching_results.pack(fill=tk.BOTH, expand=True)
        
        # Actions frame
        actions_frame = ttk.Frame(coaching_tab)
        actions_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(actions_frame, text="Save Prospects to CSV", 
                  command=self.save_coaching_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Clear Results", 
                  command=self.clear_coaching_results).pack(side=tk.LEFT, padx=5)
    
    def create_logs_tab(self):
        """Create a log viewer tab."""
        logs_tab = ttk.Frame(self.notebook)
        self.notebook.add(logs_tab, text="Logs")
        
        self.log_console = scrolledtext.ScrolledText(logs_tab, height=20)
        self.log_console.pack(fill=tk.BOTH, expand=True)
        
        controls_frame = ttk.Frame(logs_tab)
        controls_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(controls_frame, text="Refresh Logs", 
                  command=self.refresh_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Clear Logs", 
                  command=self.clear_logs).pack(side=tk.LEFT, padx=5)
    
    def show_linkedin_tab(self):
        """Switch to LinkedIn tab."""
        self.notebook.select(1)  # Index 1 is the LinkedIn tab
    
    def show_coaching_tab(self):
        """Switch to Coaching Prospects tab."""
        self.notebook.select(2)  # Index 2 is the Coaching tab
    
    def refresh_logs(self):
        """Refresh log output in the log tab."""
        try:
            if not os.path.exists("logs/gui.log"):
                open("logs/gui.log", "w").close()
            with open("logs/gui.log", "r") as log_file:
                content = log_file.read()
            self.log_console.delete(1.0, tk.END)
            self.log_console.insert(tk.END, content)
        except Exception as e:
            logger.error(f"Failed to load logs: {str(e)}")
    
    def clear_logs(self):
        """Clear the log file."""
        try:
            with open("logs/gui.log", "w") as log_file:
                log_file.write("")
            self.refresh_logs()
            logger.info("Logs cleared")
        except Exception as e:
            logger.error(f"Failed to clear logs: {str(e)}")
    
    def run_task(self, task_func, task_name):
        """Run a task in a separate thread."""
        threading.Thread(target=self.task_wrapper, args=(task_func, task_name), daemon=True).start()
    
    def task_wrapper(self, task_func, task_name):
        """Run a task and handle errors."""
        try:
            logger.info(f"Starting {task_name}...")
            result = task_func()
            logger.info(f"{task_name} completed successfully.")
            return result
        except Exception as e:
            logger.error(f"Error running {task_name}: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Task Error", f"Error running {task_name}: {str(e)}"))
    
    def run_reddit_scraper(self):
        """Placeholder for Reddit scraper functionality."""
        messagebox.showinfo("Not Implemented", "Reddit scraper not yet implemented")
        logger.info("Reddit scraper function called (not implemented)")

    def run_message_generator(self):
        """Placeholder for message generator functionality."""
        messagebox.showinfo("Not Implemented", "Message generator not yet implemented")
        logger.info("Message generator function called (not implemented)")

    def run_lead_scorer(self):
        """Placeholder for lead scorer functionality."""
        messagebox.showinfo("Not Implemented", "Lead scorer not yet implemented")
        logger.info("Lead scorer function called (not implemented)")

    def run_email_reporter(self):
        """Placeholder for email reporter functionality."""
        messagebox.showinfo("Not Implemented", "Email reporter not yet implemented")
        logger.info("Email reporter function called (not implemented)")

    def run_linkedin_with_params(self):
        """Run LinkedIn scraper with parameters from the form."""
        if not self.linkedin_scraper:
            messagebox.showerror("Error", "LinkedIn scraper not initialized")
            return
        
        industry = self.industry_var.get()
        role = self.role_var.get()
        try:
            num_pages = int(self.num_pages_var.get())
        except ValueError:
            messagebox.showerror("Error", "Number of pages must be a number")
            return
        
        self.linkedin_results.delete(1.0, tk.END)
        self.linkedin_results.insert(tk.END, f"Starting LinkedIn search for {industry} {role}...\n")

        # Run in a separate thread
        self.run_task(
            lambda: self._execute_linkedin_search(industry, role, num_pages),
            f"LinkedIn search for {industry} {role}"
        )

    def _execute_linkedin_search(self, industry, role, num_pages):
        """Execute LinkedIn search and update results."""
        try:
            results = self.linkedin_scraper.scrape_by_industry_and_role(
                industry=industry, 
                role=role, 
                num_pages=num_pages
            )
            
            # Update UI from main thread
            self.root.after(0, lambda: self._update_linkedin_results(results))
            return results
        except Exception as e:
            logger.error(f"Error in LinkedIn search: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Search Error", f"Error: {str(e)}"))

    def _update_linkedin_results(self, results):
        """Update the results text area with search results."""
        self.linkedin_results.delete(1.0, tk.END)
        
        if not results or len(results) == 0:
            self.linkedin_results.insert(tk.END, "No results found.")
            return
        
        self.linkedin_results.insert(tk.END, f"Found {len(results)} profiles:\n\n")
        
        for profile in results:
            name = profile.get('name', 'Unknown')
            headline = profile.get('headline', 'No headline')
            location = profile.get('location', 'Unknown location')
            url = profile.get('profile_url', 'No URL')
            score = profile.get('coaching_fit_score', 0)
            
            self.linkedin_results.insert(tk.END, f"Name: {name}\n")
            self.linkedin_results.insert(tk.END, f"Headline: {headline}\n")
            self.linkedin_results.insert(tk.END, f"Location: {location}\n")
            self.linkedin_results.insert(tk.END, f"Score: {score}/100\n")
            self.linkedin_results.insert(tk.END, f"URL: {url}\n")
            self.linkedin_results.insert(tk.END, "-" * 50 + "\n\n")

    def save_linkedin_results(self):
        """Save LinkedIn results to CSV."""
        messagebox.showinfo("Save", "Results are automatically saved to data/linkedin_leads.csv")
        logger.info("LinkedIn results save function called")

    def clear_linkedin_results(self):
        """Clear LinkedIn results."""
        self.linkedin_results.delete(1.0, tk.END)
        logger.info("LinkedIn results cleared")

    def search_coaching_by_keyword(self):
        """Search LinkedIn for coaching prospects using keyword."""
        if not self.linkedin_scraper:
            messagebox.showerror("Error", "LinkedIn scraper not initialized")
            return
        
        keyword = self.keyword_var.get()
        if not keyword:
            messagebox.showerror("Error", "Please enter a keyword")
            return
        
        self.coaching_results.delete(1.0, tk.END)
        self.coaching_results.insert(tk.END, f"Searching for prospects with keyword: {keyword}...\n")
        
        # Construct search URL
        search_url = f"https://www.linkedin.com/search/results/people/?keywords={keyword.replace(' ', '%20')}&origin=GLOBAL_SEARCH_HEADER"
        
        # Run in a separate thread
        self.run_task(
            lambda: self._execute_keyword_search(search_url),
            f"Coaching prospect search for '{keyword}'"
        )

    def _execute_keyword_search(self, search_url):
        """Execute a keyword search and update results."""
        try:
            results = self.linkedin_scraper.scrape_profiles(
                search_url=search_url,
                num_pages=2
            )
            
            # Update UI from main thread
            self.root.after(0, lambda: self._update_coaching_results(results))
            return results
        except Exception as e:
            logger.error(f"Error in keyword search: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Search Error", f"Error: {str(e)}"))

    def run_coaching_prospect_search(self):
        """Run comprehensive coaching prospect search."""
        if not self.linkedin_scraper:
            messagebox.showerror("Error", "LinkedIn scraper not initialized")
            return
        
        self.coaching_results.delete(1.0, tk.END)
        self.coaching_results.insert(tk.END, "Starting comprehensive coaching prospect search...\n")
        self.coaching_results.insert(tk.END, "This may take several minutes. Please be patient.\n\n")
        
        # Run in a separate thread
        self.run_task(
            lambda: self._execute_comprehensive_search(),
            "Comprehensive coaching prospect search"
        )

    def _execute_comprehensive_search(self):
        """Execute comprehensive search for coaching prospects."""
        try:
            results = self.linkedin_scraper.scrape_for_coaching_leads(
                num_pages=2,
                target_count=30
            )
            
            # Update UI from main thread
            self.root.after(0, lambda: self._update_coaching_results(results))
            return results
        except Exception as e:
            logger.error(f"Error in comprehensive search: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Search Error", f"Error: {str(e)}"))

    def _update_coaching_results(self, results):
        """Update the coaching results text area."""
        self.coaching_results.delete(1.0, tk.END)
        
        if not results or len(results) == 0:
            self.coaching_results.insert(tk.END, "No coaching prospects found.")
            return
        
        self.coaching_results.insert(tk.END, f"Found {len(results)} potential coaching prospects:\n\n")
        
        for profile in results:
            name = profile.get('name', 'Unknown')
            headline = profile.get('headline', 'No headline')
            location = profile.get('location', 'Unknown location')
            url = profile.get('profile_url', 'No URL')
            score = profile.get('coaching_fit_score', 0)
            notes = profile.get('coaching_notes', '')
            
            self.coaching_results.insert(tk.END, f"Name: {name}\n")
            self.coaching_results.insert(tk.END, f"Headline: {headline}\n")
            self.coaching_results.insert(tk.END, f"Location: {location}\n")
            self.coaching_results.insert(tk.END, f"Coaching Fit Score: {score}/100\n")
            if notes:
                self.coaching_results.insert(tk.END, f"Notes: {notes}\n")
            self.coaching_results.insert(tk.END, f"URL: {url}\n")
            self.coaching_results.insert(tk.END, "-" * 50 + "\n\n")

    def save_coaching_results(self):
        """Save coaching results to CSV."""
        messagebox.showinfo("Save", "Results are automatically saved to data/life_coaching_leads.csv")
        logger.info("Coaching results save function called")

    def clear_coaching_results(self):
        """Clear coaching results."""
        self.coaching_results.delete(1.0, tk.END)
        logger.info("Coaching results cleared")

if __name__ == "__main__":
    root = tk.Tk()
    app = LeadGenerationGUI(root)
    root.mainloop()
