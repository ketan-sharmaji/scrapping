from inputs import *
from load_file import *
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import requests
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.edge.options import Options as EdgeOptions

class JSWPriceScraper:
    def __init__(self, url='https://www.jswneosteel.in/build/know-existing-prices.aspx'):
        """
        Initialize the web scraper with Chrome WebDriver
        """
        
        # Setup Chrome options

        options = EdgeOptions()
        options.add_argument("--disable-gpu")        # Disable GPU hardware acceleration
        options.add_argument("--no-sandbox")         # Disable sandbox (security feature)
        options.add_argument("--headless")           # Run headless (without opening browser window)
        options.add_argument("--disable-dev-shm-usage")  # Avoids issues with shared memory
        options.add_argument("start-maximized")     # Start with maximized window
        options.add_argument("disable-infobars")    # Disable infobars like 'Chrome is being controlled by automated software'
        options.add_argument("--disable-extensions") # Dis
        options.add_argument("--disable-webgl")
        options.add_argument("--disable-notifications")
        options.add_argument("--ignore-certificate-errors")  # Ignore SSL certificate errors
        



        service = EdgeService(EdgeChromiumDriverManager().install())
        self.driver = webdriver.Edge(service=service, options=options)

        # Initialize WebDriver
        
        self.url = url
        self.wait = WebDriverWait(self.driver, 10)

    def get_states(self):
        """
        Extract list of states from dropdown
        """
        self.driver.get(self.url)
        state_dropdown = Select(self.driver.find_element(By.ID, 'ContentPlaceHolder1_ddlstate'))
        
        states = [
            {'id': option.get_attribute('value'), 'name': option.text} 
            for option in state_dropdown.options 
            if option.get_attribute('value') and option.text != '- Select State -'
        ]
        return states

    def get_districts(self, state_id):
        """
        Get districts for a specific state
        """
        state_dropdown = Select(self.driver.find_element(By.ID, 'ContentPlaceHolder1_ddlstate'))
        state_dropdown.select_by_value(state_id)
        
        # Wait for district dropdown to populate
        time.sleep(2)
        
        district_dropdown = Select(self.driver.find_element(By.ID, 'ContentPlaceHolder1_ddldistrict'))
        
        districts = [
            {'id': option.get_attribute('value'), 'name': option.text} 
            for option in district_dropdown.options 
            if option.get_attribute('value') and option.text != 'Select District'
        ]
        return districts

    def get_prices(self, state_id, district_id, state_name, district_name):
        """
        Scrape prices for a specific state and district
        """
        try:
            # Select state
            state_dropdown = Select(self.driver.find_element(By.ID, 'ContentPlaceHolder1_ddlstate'))
            state_dropdown.select_by_value(state_id)
            time.sleep(1)

            # Select district
            district_dropdown = Select(self.driver.find_element(By.ID, 'ContentPlaceHolder1_ddldistrict'))
            district_dropdown.select_by_value(district_id)
            time.sleep(1)

            # Click submit
            submit_button = self.driver.find_element(By.ID, 'ContentPlaceHolder1_btnsubmit')
            submit_button.click()
            time.sleep(2)

            # Extract price table
            price_table = self.driver.find_element(By.CLASS_NAME, 'col-3-tble')
            rows = price_table.find_elements(By.TAG_NAME, 'tr')[1:]  # Skip header

            prices = []
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, 'td')
                if len(cells) == 2:
                    section = cells[0].text.strip()  # Diameter section
                    price = cells[1].text.strip()  # Price

                    # Append '/piece' to the price
                    prices.append({
                        'Brand': 'JSW Neosteel',
                        'Price': f"{price}/piece",
                        'URL': "https://www.jswneosteel.in/build/know-existing-prices.aspx",
                        'Location': district_name,
                        'Diameter': section,
                        'Grade': 'FE 550D'
                    })

            return prices

        except Exception as e:
            print(f"Error scraping prices for state {state_name}, district {district_name}: {e}")
            return []
    def scrape_all_prices(self):
        """
        Scrape prices for all states and districts
        """
        all_prices = []
        
        # Get states
        states = self.get_states()
        
        for state in states:
            try:
                # Get districts for this state
                districts = self.get_districts(state['id'])
                
                for district in districts:
                    # Get prices for this state and district
                    prices = self.get_prices(state['id'], district['id'], state['name'], district['name'])
                    all_prices.extend(prices)
                    
                    # Pause to avoid overwhelming the server
                    time.sleep(1)
            
            except Exception as e:
                print(f"Error processing state {state['name']}: {e}")
        
        return all_prices

    def save_to_csv(self, filename):
        """
        Save scraped prices to CSV (Append mode)
        """
        prices = self.scrape_all_prices()
        if prices:
            df = pd.DataFrame(prices)
            # Append data to existing file
            df.to_csv(filename, mode='a', header=not pd.io.common.file_exists(filename), index=False)
            print(f"JSW prices saved to {filename}")

    def close(self):
        """
        Close the browser
        """
        self.driver.quit()


def main():
    scraper = None
    try:
        scraper = JSWPriceScraper()
        scraper.save_to_csv(stored_file_path2)
    except Exception as e:
        print(f"Scraping failed: {e}")
    finally:
        if scraper:
            scraper.close()

if __name__ == '__main__':
    main()
