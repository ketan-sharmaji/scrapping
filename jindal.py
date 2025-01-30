import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from load_file import *
import csv
import logging
from urllib.parse import urlencode 
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import os



# Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0

class JindalPantherPriceScraper:
    def __init__(self):
        self.base_url = "https://www.jindalpanther.com/recommended-consumer-price.html"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def get_states(self):
        """
        Extract all available states from the dropdown
        """
        self.logger.info("Fetching states...")
        response = self.session.get(self.base_url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        state_dropdown = soup.find('select', {'name': 'state'})
        if not state_dropdown:
            self.logger.error("State dropdown not found!")
            return []

        states = [option['value'] for option in state_dropdown.find_all('option') 
                  if option['value'] and option['value'] != 'Select State']
        return states

    def get_districts(self, state):
       
        self.logger.info(f"Fetching districts for state: {state}")
        params = {'state': state}
        response = self.session.get(self.base_url, params=params, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        district_dropdown = soup.find('select', {'name': 'district'})
        if not district_dropdown:
            self.logger.error(f"District dropdown not found for state: {state}")
            return []

        districts = [option['value'] for option in district_dropdown.find_all('option')]
        return districts

    def get_price_details(self, product, state, district):
        params = {'product': product, 'state': state, 'district': district}
        self.logger.info(f"Scraping prices for {state} - {district}")
        try:
            response = self.session.get(self.base_url, params=params, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')

            price_table = soup.find('table', class_='table')
            if not price_table:
                self.logger.warning(f"No price table found for {state} - {district}")
                return None

            rows = price_table.find_all('tr')
            price_details = []
            for row in rows[1:]:  # Skipping header row
                cols = row.find_all('td')
                if len(cols) >= 2:
                    diameter = cols[0].get_text(strip=True)
                    price = cols[1].get_text(strip=True)

                    # Add "Rs" in front of the price
                    formatted_price = f"Rs {price}/piece"

                    # Create a separate row for each diameter and product
                    price_details.append({
                        'Brand': 'Jindal',
                        'Price': formatted_price,
                        'URL': "https://www.jindalpanther.com/recommended-consumer-price.html",
                        'Location': f"{district}, {state}",
                        'Diameter': diameter,
                        'Grade': 'FE 550D'
                    })

            return price_details
        except Exception as e:
            self.logger.error(f"Error fetching price for {state} - {district}: {e}")
            return None

    def scrape_state(self, product, state):
        """
        Scrape prices for all districts in a state
        """
        districts = self.get_districts(state)
        if not districts:
            return []

        all_prices = []
        with ThreadPoolExecutor(max_workers=5) as executor:  # Adjust max_workers as needed
            futures = {executor.submit(self.get_price_details, product, state, district): district for district in districts}
            
            for future in as_completed(futures):
                district = futures[future]
                try:
                    price_details = future.result()
                    if price_details:
                        all_prices.extend(price_details)
                except Exception as e:
                    self.logger.error(f"Error processing {state} - {district}: {e}")
        
        return all_prices

    def scrape_all_prices(self, product='Jindal Panther TMT Fe 550D'):
        """
        Scrape prices for all states and districts
        """
        all_prices = []
        states = self.get_states()
        if not states:
            self.logger.error("No states found. Exiting.")
            return all_prices
        
        for state in states:
            self.logger.info(f"Processing state: {state}")
            state_prices = self.scrape_state(product, state)
            all_prices.extend(state_prices)

        return all_prices

    def save_to_csv(self, prices, filename):
       
        if not prices:
            self.logger.warning("No prices to save.")
            return

        # Define columns in the required order
        columns = ['Brand', 'Price', 'URL', 'Location', 'Diameter', 'Grade']

        # Check if the file already exists
        file_exists = os.path.exists(filename)

        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)

            # If file does not exist, write the header
            if not file_exists:
                writer.writeheader()
            
            writer.writerows(prices)
        
        self.logger.info(f"Prices saved to {filename}")


def main():
    scraper = JindalPantherPriceScraper()
    prices = scraper.scrape_all_prices()
    scraper.save_to_csv(prices, stored_file_path2)
    df = pd.DataFrame(prices)

if __name__ == "__main__":
    main()
