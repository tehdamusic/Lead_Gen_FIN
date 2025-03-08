import os
import pickle
import logging
from typing import Any, Optional
from datetime import datetime

import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='sheets_manager.log'
)
logger = logging.getLogger('sheets_manager')

# Define scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_credentials() -> Credentials:
    """
    Get Google API credentials.
    
    Returns:
        Credentials object for Google API
    """
    credentials = None
    
    # Get credentials file path from environment variable
    creds_file = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'credentials.json')
    token_file = os.getenv('GOOGLE_SHEETS_TOKEN_FILE', 'token.pickle')
    
    # Try to load existing token
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            try:
                credentials = pickle.load(token)
            except Exception as e:
                logger.error(f"Error loading token: {str(e)}")
    
    # If there are no valid credentials, let the user log in
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
            except Exception as e:
                logger.error(f"Error refreshing credentials: {str(e)}")
                credentials = None
        
        if not credentials:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    creds_file, SCOPES)
                credentials = flow.run_local_server(port=0)
            except Exception as e:
                logger.error(f"Error getting new credentials: {str(e)}")
                raise
        
        # Save the credentials for the next run
        with open(token_file, 'wb') as token:
            pickle.dump(credentials, token)
    
    return credentials

def get_sheets_client() -> gspread.Client:
    """
    Get authenticated gspread client.
    
    Returns:
        Authenticated gspread client
    """
    try:
        credentials = get_credentials()
        client = gspread.authorize(credentials)
        logger.info("Successfully connected to Google Sheets")
        return client
    except Exception as e:
        logger.error(f"Error getting sheets client: {str(e)}")
        raise

def get_sheet(spreadsheet_name: str, worksheet_name: str) -> gspread.Worksheet:
    """
    Get a specific worksheet from a spreadsheet.
    
    Args:
        spreadsheet_name: Name of the spreadsheet
        worksheet_name: Name of the worksheet
        
    Returns:
        Worksheet object
    """
    try:
        client = get_sheets_client()
        spreadsheet = client.open(spreadsheet_name)
        worksheet = spreadsheet.worksheet(worksheet_name)
        return worksheet
    except Exception as e:
        logger.error(f"Error getting sheet {spreadsheet_name}/{worksheet_name}: {str(e)}")
        raise

def get_spreadsheet_id() -> Optional[str]:
    """
    Get the spreadsheet ID from environment variable.
    
    Returns:
        Spreadsheet ID or None if not found
    """
    return os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')

def create_sheet_if_not_exists(spreadsheet_name: str, worksheet_name: str) -> gspread.Worksheet:
    """
    Create a worksheet if it doesn't exist.
    
    Args:
        spreadsheet_name: Name of the spreadsheet
        worksheet_name: Name of the worksheet
        
    Returns:
        Worksheet object
    """
    try:
        client = get_sheets_client()
        
        # Try to open the spreadsheet, create if it doesn't exist
        try:
            spreadsheet = client.open(spreadsheet_name)
        except:
            spreadsheet = client.create(spreadsheet_name)
            logger.info(f"Created new spreadsheet: {spreadsheet_name}")
        
        # Try to get the worksheet, create if it doesn't exist
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except:
            worksheet = spreadsheet.add_worksheet(
                title=worksheet_name, rows=1000, cols=20
            )
            logger.info(f"Created new worksheet: {worksheet_name}")
        
        return worksheet
    except Exception as e:
        logger.error(f"Error creating sheet {spreadsheet_name}/{worksheet_name}: {str(e)}")
        raise

def append_rows(worksheet: gspread.Worksheet, rows: list) -> None:
    """
    Append multiple rows to a worksheet.
    
    Args:
        worksheet: Worksheet object
        rows: List of rows to append
    """
    try:
        if rows:
            worksheet.append_rows(rows)
            logger.info(f"Appended {len(rows)} rows to {worksheet.title}")
    except Exception as e:
        logger.error(f"Error appending rows to {worksheet.title}: {str(e)}")
        raise

if __name__ == "__main__":
    # Test functionality
    try:
        client = get_sheets_client()
        worksheet = create_sheet_if_not_exists('LeadGenerationData', 'TestData')
        append_rows(worksheet, [['Test', 'Data', datetime.now().strftime("%Y-%m-%d %H:%M:%S")]])
        print("Test successful!")
    except Exception as e:
        print(f"Error: {str(e)}")
