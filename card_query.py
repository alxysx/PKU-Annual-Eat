import requests
from datetime import datetime, timedelta
import json
import argparse
import time
from typing import List, Dict

def get_card_transactions(session_id: str, hall_ticket: str, start_date: datetime, 
                         account: str = "122579", page: int = 1, rows: int = 50, 
                         delay: float = 1.0, max_retries: int = 3) -> dict:
    """
    Fetch card transactions with retry logic
    """
    # Add delay before making request (except for first page)
    if page > 1:
        time.sleep(delay)
    
    # Define the URL
    url = "https://card.pku.edu.cn/Report/GetPersonTrjn"
    
    # Set up the request parameters
    params = {
        'sdate': start_date.strftime('%Y-%m-%d'),
        'edate': datetime.now().strftime('%Y-%m-%d'),
        'account': account,
        'page': str(page),
        'rows': str(rows)
    }
    
    # Set up the cookies
    cookies = {
        "ASP.NETSessionId": session_id,
        "hallticket": hall_ticket
    }
    
    for attempt in range(max_retries):
        try:
            # Make the POST request with parameters
            response = requests.post(url, cookies=cookies, data=params)
            
            # Print detailed debug information if status code is not 200
            if response.status_code != 200:
                print(f"\nRequest failed with status code: {response.status_code} (Attempt {attempt + 1}/{max_retries})")
                print("\nResponse Headers:")
                for header, value in response.headers.items():
                    print(f"{header}: {value}")
                print("\nResponse Content:")
                print(response.text[:500])  # Print first 500 chars of response
                
                if attempt < max_retries - 1:  # If not the last attempt
                    retry_delay = delay * (attempt + 2)  # Exponential backoff
                    print(f"Retrying in {retry_delay:.1f} seconds...")
                    time.sleep(retry_delay)
                    continue
            
            response.raise_for_status()
            
            try:
                return response.json()
            except json.JSONDecodeError as je:
                print(f"\nFailed to parse JSON response for page {page} (Attempt {attempt + 1}/{max_retries})")
                print(f"JSON Error: {str(je)}")
                print("\nResponse Content (first 500 chars):")
                print(response.text[:500])
                print("\nResponse Headers:")
                for header, value in response.headers.items():
                    print(f"{header}: {value}")
                
                if attempt < max_retries - 1:  # If not the last attempt
                    retry_delay = delay * (attempt + 2)  # Exponential backoff
                    print(f"Retrying in {retry_delay:.1f} seconds...")
                    time.sleep(retry_delay)
                    continue
                return None
        
        except requests.exceptions.RequestException as e:
            print(f"\nError occurred while fetching page {page} (Attempt {attempt + 1}/{max_retries}):")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            print("\nRequest details:")
            print(f"URL: {url}")
            print("Parameters:", json.dumps(params, indent=2))
            print("Cookies:", json.dumps(cookies, indent=2))
            
            if hasattr(e, 'response') and e.response is not None:
                print("\nResponse status code:", e.response.status_code)
                print("\nResponse Headers:")
                for header, value in e.response.headers.items():
                    print(f"{header}: {value}")
                print("\nResponse Content (first 500 chars):")
                print(e.response.text[:500])
            
            if attempt < max_retries - 1:  # If not the last attempt
                retry_delay = delay * (attempt + 2)  # Exponential backoff
                print(f"Retrying in {retry_delay:.1f} seconds...")
                time.sleep(retry_delay)
                continue
            return None
    
    return None  # All retries failed

def get_all_transactions(session_id: str, hall_ticket: str, start_date: datetime, 
                        account: str = "122579", delay: float = 1.0) -> List[Dict]:
    # Get first page to determine total records
    first_page = get_card_transactions(session_id, hall_ticket, start_date, account)
    
    if not first_page:
        print("\nFailed to fetch initial data. Please check your session credentials.")
        print("Make sure your ASP.NETSessionId and hallticket are valid and not expired.")
        return []
    
    if 'total' not in first_page:
        print("\nUnexpected response format:")
        print(json.dumps(first_page, indent=2, ensure_ascii=False)[:500])
        return []
    
    # Extract total number of records
    total_records = first_page.get('total', 0)
    rows_per_page = 50  # Increased from 15 to 50
    total_pages = (total_records + rows_per_page - 1) // rows_per_page
    
    print(f"Found {total_records} transactions across {total_pages} pages ({rows_per_page} items per page)")
    
    # Store all transactions
    all_transactions = first_page.get('rows', [])
    
    # Fetch remaining pages
    for page in range(2, total_pages + 1):
        print(f"Fetching page {page}/{total_pages}... (waiting {delay}s)")
        page_data = get_card_transactions(session_id, hall_ticket, start_date, account, page, delay=delay)
        
        if page_data and 'rows' in page_data:
            all_transactions.extend(page_data['rows'])
        else:
            print(f"\nFailed to fetch page {page} after all retries")
            print("Stopping pagination due to error")
            break
    
    return all_transactions

def parse_date(date_str: str) -> datetime:
    """Parse date string in YYYY-MM-DD format"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")

def main():
    parser = argparse.ArgumentParser(description='Fetch PKU card transactions')
    parser.add_argument('account', type=str,
                       help='Account number to query')
    parser.add_argument('--start-date', type=parse_date, 
                       default=(datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'),
                       help='Start date in YYYY-MM-DD format (default: 60 days ago)')
    parser.add_argument('--delay', type=float, default=1.0,
                       help='Delay between requests in seconds (default: 1.0)')
    args = parser.parse_args()
    
    # Get user input for cookie values
    session_id = input("Please enter your ASP.NETSessionId: ").strip()
    hall_ticket = input("Please enter your hallticket: ").strip()
    
    if not session_id or not hall_ticket:
        print("\nError: Both ASP.NETSessionId and hallticket are required!")
        return
    
    print(f"\nFetching transactions from {args.start_date.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}")
    print(f"Using account: {args.account}")
    print(f"Using {args.delay}s delay between requests...")
    
    # Get all transaction data
    transactions = get_all_transactions(session_id, hall_ticket, args.start_date, 
                                      account=args.account, delay=args.delay)
    
    if transactions:
        # Save to file
        filename = f"card_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(transactions, f, ensure_ascii=False, indent=2)
        print(f"\nTransactions saved to {filename}")
        print(f"Total transactions fetched: {len(transactions)}")
    else:
        print("\nNo transactions were retrieved. Please check the error messages above.")

if __name__ == "__main__":
    main() 