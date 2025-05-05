#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import argparse
import time
from urllib.parse import urlencode, quote_plus
import os
import datetime
import re
import csv


class TCGCollectorScraper:
    def __init__(self):
        self.base_url = "https://www.tcgcollector.com/cards"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
    def scrape_page(self, params, page_num, base_url):
        """Scrape a single page of the TCG Collector website."""
        # Create a copy of params to avoid modifying the original
        page_params = params.copy()
        
        # Only add page parameter if it's not page 1
        # (since TCG Collector omits page=1 from URL)
        if page_num > 1:
            page_params['page'] = page_num
        
        # Construct the URL with parameters
        try:
            # Use quote_plus directly for the card search to ensure proper encoding
            if 'cardSearch' in page_params:
                search_term = page_params.pop('cardSearch')  # Remove from params
                # Manually replace apostrophes in the search term
                search_term = search_term.replace("'", "'")
                
                query_parts = [f"{k}={quote_plus(str(v))}" for k, v in page_params.items()]
                # Add the properly encoded search term
                query_parts.append(f"cardSearch={quote_plus(search_term)}")
                query_string = "&".join(query_parts)
            else:
                query_string = urlencode(page_params)
                
            url = f"{base_url}?{query_string}"
            
            # Direct string replacement in the final URL - force apostrophes to be correctly encoded
            url = url.replace("%E2%80%99", "%27")  # Replace encoded fancy apostrophe with standard one
        except Exception as e:
            print(f"Error encoding URL parameters: {e}")
            # Fallback to standard encoding
            query_string = urlencode(page_params)
            url = f"{base_url}?{query_string}"
            # Even in fallback, fix the apostrophes
            url = url.replace("%E2%80%99", "%27")
        
        print(f"Scraping page {page_num}: {url}")
        
        # Make the request
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code}")
            return []
        
        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all image elements with the specific class
        image_elements = soup.find_all("img", class_="card-image-grid-item-image")
        
        # Extract the image URLs from the src attribute
        image_urls = [img.get('src') for img in image_elements if img.get('src')]
        
        print(f"Found {len(image_urls)} images on page {page_num}")
        
        return image_urls
    
    def get_max_pages(self, params, base_url):
        """Get the maximum number of pages available for the search."""
        # Create a copy of params to avoid modifying the original
        page_params = params.copy()
        
        # Ensure we don't have a page parameter for the first request
        if 'page' in page_params:
            del page_params['page']
            
        query_string = urlencode(page_params)
        url = f"{base_url}?{query_string}"
        
        print(f"Checking max pages at: {url}")
        
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code}")
            return 1
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try to find the pagination element by ID first
        pagination_container = soup.find("ul", id="card-search-result-pagination")
        
        if pagination_container:
            # Look for the last page indicator
            last_page_item = pagination_container.find("li", class_="pagination-item-last")
            if last_page_item:
                page_link = last_page_item.find("a")
                if page_link and page_link.text.strip().isdigit():
                    max_page = int(page_link.text.strip())
                    print(f"Detected {max_page} total pages from last page indicator")
                    return max_page
            
            # If no last page indicator, check all pagination items
            pagination_items = pagination_container.find_all("li", class_="pagination-item")
            max_page = 1
            
            for item in pagination_items:
                # Skip items with additional classes like 'pagination-item-gap'
                if 'pagination-item-gap' in item.get('class', []):
                    continue
                    
                page_link = item.find("a")
                if page_link and page_link.text.strip().isdigit():
                    page_num = int(page_link.text.strip())
                    max_page = max(max_page, page_num)
            
            if max_page > 1:
                print(f"Detected {max_page} total pages from pagination items")
                return max_page
        
        # Fallback method: Try to find standard pagination
        pagination = soup.find_all("li", class_="page-item")
        
        # If no pagination is found, try to estimate from total items
        if not pagination and not pagination_container:
            # Look for item count text
            item_count_div = soup.find("div", class_="results-count")
            if item_count_div and item_count_div.text:
                # Try to extract number like "Showing 1-60 of 157 items"
                count_text = item_count_div.text.strip()
                parts = count_text.split(" of ")
                if len(parts) > 1:
                    try:
                        total_items = int(parts[1].split(" ")[0])
                        cards_per_page = params.get('cardsPerPage', 60)
                        max_pages = (total_items + cards_per_page - 1) // cards_per_page
                        print(f"Estimated {max_pages} pages from {total_items} total items")
                        return max_pages
                    except (ValueError, IndexError):
                        pass
            
            print("No pagination found, assuming only one page is available")
            return 1
        
        # Process standard pagination if found
        max_page = 1
        for page_item in pagination:
            page_link = page_item.find("a", class_="page-link")
            if page_link and page_link.text.strip().isdigit():
                page_num = int(page_link.text.strip())
                max_page = max(max_page, page_num)
        
        print(f"Detected {max_page} total pages")
        return max_page
    
    def generate_output_filename(self, search_term, jp):
        """Generate a filename based on search term and current date/time."""
        # Format current date and time: YYYY-MM-DD_HH-MM-SS
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        
        # Default name if no search term
        if not search_term:
            prefix = "all-cards"
        else:
            # Clean up search term for use in filename
            # Replace spaces and special characters with underscore
            prefix = re.sub(r'[^a-zA-Z0-9]', '_', search_term).lower()
            # Remove consecutive underscores
            prefix = re.sub(r'_+', '_', prefix)
            # Remove leading/trailing underscores
            prefix = prefix.strip('_')
        
        # Add jp indicator if Japanese cards
        if jp:
            prefix = f"{prefix}_jp"
        
        return f"{prefix}_{timestamp}.txt"
    
    def scrape(self, release_date_order=None, cards_per_page=60, 
               card_search=None, start_page=1, end_page=None, output_file=None, 
               jp=False, sort_by=None, force_end_page=False):
        """
        Scrape TCG Collector images with the given parameters.
        
        Args:
            release_date_order: 'oldToNew' or 'newToOld'
            cards_per_page: 30, 60, or 120
            card_search: Search term
            start_page: First page to scrape (default: 1)
            end_page: Last page to scrape (if None, will be determined automatically)
            output_file: File to save the image URLs (if None, will be generated automatically)
            jp: Whether to scrape Japanese cards
            sort_by: Sort by rarity ('rarityDesc' or 'rarityAsc')
            force_end_page: If True, will ignore the initially detected page limit
        """
        # Generate output filename if not provided
        if output_file is None:
            output_file = self.generate_output_filename(card_search, jp)
            print(f"Generated output filename: {output_file}")
            
        # Set the base URL based on the jp parameter
        base_url = f"{self.base_url}/jp" if jp else self.base_url
        
        # Set up the parameters
        params = {
            'displayAs': 'images',
            'cardsPerPage': cards_per_page
        }
        
        if release_date_order:
            params['releaseDateOrder'] = release_date_order
            
        if card_search:
            params['cardSearch'] = card_search
            
        if sort_by:
            params['sortBy'] = sort_by
        
        # Determine the max available pages
        max_available_pages = self.get_max_pages(params, base_url)
        
        # If end_page is not specified, use the max available pages
        if end_page is None:
            end_page = max_available_pages
        # If force_end_page is True, use the specified end_page (but don't exceed 100 for safety)
        elif force_end_page:
            end_page = min(end_page, 100)  # Safety limit
            print(f"Force mode enabled: Will try up to page {end_page} but will stop if no more images are found")
        # Otherwise, don't exceed the max available pages
        else:
            end_page = min(end_page, max_available_pages)
        
        print(f"Scraping pages {start_page} to {end_page}")
        
        # Scrape each page
        all_image_urls = []
        for page_num in range(start_page, end_page + 1):
            image_urls = self.scrape_page(params, page_num, base_url)
            all_image_urls.extend(image_urls)
            
            # If we didn't find any images on this page, we're past the available content
            # Stop even if force_end_page is True
            if not image_urls:
                print(f"No images found on page {page_num}, stopping")
                break
                
            # Be nice to the server
            if page_num < end_page:
                time.sleep(1)
        
        # Save the image URLs to a file
        with open(output_file, 'w') as f:
            for url in all_image_urls:
                f.write(f"{url};\n")
        
        print(f"Scraped {len(all_image_urls)} image URLs and saved to {output_file}")
        return all_image_urls
    
    def scrape_csv(self, csv_filename, jp=False, output_file=None):
        """
        Scrape cards from TCG Collector based on a CSV file.
        
        Args:
            csv_filename: Name of the CSV file in the 'datas' folder
            jp: Whether to scrape Japanese cards
            output_file: File to save the image URLs (if None, will be generated automatically)
        """
        # Construct the full path to the CSV file
        csv_path = os.path.join('datas', csv_filename)
        
        if not os.path.exists(csv_path):
            print(f"Error: CSV file '{csv_path}' not found")
            return []
        
        try:
            # Read the CSV file with standard csv module
            with open(csv_path, 'r', encoding='utf-8') as f:
                # Skip the "sep=" line if it exists
                first_line = f.readline()
                if not first_line.startswith('"sep='):
                    # If it's not a separator line, we need to go back to the beginning
                    f.seek(0)
                
                # Read the rest as CSV
                reader = csv.DictReader(f)
                
                # Generate output filename if not provided
                if output_file is None:
                    now = datetime.datetime.now()
                    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
                    output_file = f"csv_scrape_{timestamp}.txt"
                    print(f"Generated output filename: {output_file}")
                
                # Set the base URL based on the jp parameter
                base_url = f"{self.base_url}/jp" if jp else self.base_url
                
                # Prepare for scraping
                all_image_urls = []
                failed_cards = []
                success_count = 0
                fail_count = 0
                
                # Process each row in the CSV
                for index, row in enumerate(reader):
                    try:
                        # Normalize the card name by replacing fancy apostrophes with standard ones
                        card_name = row['Card Name']
                        # Direct replacement of common problematic characters
                        card_name = card_name.replace(''', "'").replace(''', "'").replace('"', '"').replace('"', '"')
                        
                        # Get only the part before slash or space in card number
                        full_card_number = row['Card Number'].strip()
                        
                        # Step 1: Split by space or / and take the first part
                        card_number_temp = re.split(r'[ /]', full_card_number)[0].strip()
                        
                        # Step 2: Extract only digits at the beginning 
                        # (matches 123 from 123metal but leaves 123 as 123)
                        match = re.match(r'^(\d+)', card_number_temp)
                        if match:
                            card_number = match.group(1)
                        else:
                            # If no digits found, use the original value
                            card_number = card_number_temp
                        
                        # Check if the card number was truncated
                        was_truncated = card_number != full_card_number
                        
                        # Combine card name and number for search
                        search_term = f"{card_name} {card_number}"
                        
                        # Log with or without "Full: " depending on whether the number was truncated
                        if was_truncated:
                            print(f"Searching for: {search_term} (Full: {card_name} {full_card_number})")
                        else:
                            print(f"Searching for: {search_term}")
                        
                        # Set up the parameters
                        params = {
                            'displayAs': 'images',
                            'cardsPerPage': 60,
                            'cardSearch': search_term,
                            'releaseDateOrder': 'newToOld'  # Add this to improve search results
                        }
                        
                        # Scrape just the first page
                        image_urls = self.scrape_page(params, 1, base_url)
                        
                        if image_urls:
                            # Take only the first image
                            first_image = image_urls[0]
                            all_image_urls.append(first_image)
                            print(f"Found image for {search_term}")
                            success_count += 1
                        else:
                            print(f"Error: No image found for {search_term}")
                            failed_card = {
                                'index': index + 1,  # +1 to account for 0-based indexing
                                'card_name': card_name,
                                'card_number': card_number,
                                'search_term': search_term
                            }
                            
                            # Only add full card number if it was truncated
                            if was_truncated:
                                failed_card['full_card_number'] = full_card_number
                                
                            failed_cards.append(failed_card)
                            fail_count += 1
                        
                        # Be nice to the server
                        time.sleep(1)
                        
                    except Exception as e:
                        print(f"Error processing row {index}: {e}")
                        failed_cards.append({
                            'index': index + 1,  # +1 to account for 0-based indexing
                            'card_name': row.get('Card Name', 'Unknown'),
                            'card_number': row.get('Card Number', 'Unknown'),
                            'error': str(e)
                        })
                        fail_count += 1
                
                # Save the image URLs to a file
                with open(output_file, 'w') as f:
                    for url in all_image_urls:
                        f.write(f"{url};\n")
                
                # Print summary
                print("\n" + "="*50)
                print("SCRAPING SUMMARY")
                print("="*50)
                print(f"Total cards processed: {success_count + fail_count}")
                print(f"Successfully scraped: {success_count}")
                print(f"Failed to scrape: {fail_count}")
                
                if failed_cards:
                    print("\nDetails of failed cards:")
                    for card in failed_cards:
                        if 'error' in card:
                            print(f"  Row {card['index']}: {card['card_name']} {card['card_number']} - Error: {card['error']}")
                        elif 'full_card_number' in card:
                            print(f"  Row {card['index']}: {card['card_name']} {card['card_number']} (Full: {card['full_card_number']}) - No image found")
                        else:
                            print(f"  Row {card['index']}: {card['search_term']} - No image found")
                
                print(f"\nAll image URLs saved to {output_file}")
                
                return all_image_urls
                
        except Exception as e:
            print(f"Error processing CSV file: {e}")
            return []


def parse_args():
    parser = argparse.ArgumentParser(description='Scrape images from TCG Collector')
    
    parser.add_argument('--order', choices=['oldToNew', 'newToOld'], 
                        help='Release date order (oldToNew or newToOld)')
    
    parser.add_argument('--per-page', type=int, choices=[30, 60, 120], default=60,
                        help='Cards per page (30, 60, or 120)')
    
    parser.add_argument('--search', type=str, 
                        help='Search term for cards')
    
    parser.add_argument('--start-page', type=int, default=1,
                        help='First page to scrape (default: 1)')
    
    parser.add_argument('--end-page', type=int,
                        help='Last page to scrape (if not specified, will scrape all available pages)')
    
    parser.add_argument('--output', type=str,
                        help='Output file for image URLs (if not specified, will be generated from search term and date)')
    
    parser.add_argument('--jp', action='store_true',
                        help='Scrape Japanese cards')
    
    parser.add_argument('--sort-by', choices=['rarityDesc', 'rarityAsc'],
                        help='Sort by rarity (descending or ascending)')
    
    parser.add_argument('--force', action='store_true',
                        help='Ignore the initially detected page limit and try to scrape up to end-page')
    
    parser.add_argument('--csv', type=str,
                        help='CSV file in the datas folder to read card information from')
    
    return parser.parse_args()


def main():
    args = parse_args()
    
    scraper = TCGCollectorScraper()
    
    if args.csv:
        # CSV mode - scrape cards from CSV file
        scraper.scrape_csv(
            csv_filename=args.csv,
            jp=args.jp,
            output_file=args.output
        )
    else:
        # Regular mode - scrape with search parameters
        scraper.scrape(
            release_date_order=args.order,
            cards_per_page=args.per_page,
            card_search=args.search,
            start_page=args.start_page,
            end_page=args.end_page,
            output_file=args.output,
            jp=args.jp,
            sort_by=args.sort_by,
            force_end_page=args.force
        )


if __name__ == "__main__":
    main() 