

import os
import pandas as pd
from load_file import stored_file_path
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup
import re
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.edge.options import Options as EdgeOptions




# Global dictionary to store data
d = {
    "Brand": [],
    "Price": [],
    "URL": [],
    "Location": [],
    "Diameter": [],
    "Grade": [],
}


def scrape_dynamic_content(url):
    """Use Selenium to load dynamic content."""
    options = EdgeOptions()
    options.add_argument("--disable-gpu")        # Disable GPU hardware acceleration
    options.add_argument("--no-sandbox")         # Disable sandbox (security feature)
    options.add_argument("--headless")           # Run headless (without opening browser window)
    options.add_argument("--disable-dev-shm-usage")  # Avoids issues with shared memory
    options.add_argument("disable-infobars")    # Disable infobars like 'Chrome is being controlled by automated software'
    options.add_argument("--disable-extensions") # Dis
    options.add_argument("--ignore-certificate-errors")  # Ignore SSL certificate errors

    options.add_argument("--disable-webgl")
    options.add_argument("--disable-notifications")


    service = EdgeService(EdgeChromiumDriverManager().install())
    service.start()  # Start the service

    # Pass the service and options to the webdriver
    driver = webdriver.Edge(service=service, options=options)
    driver.get(url)
    driver.implicitly_wait(10)  # Wait for the page to load

    # Scroll to the bottom of the page to load dynamic content
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Wait for content to load
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # Get the page source once everything is loaded
    html = driver.page_source
    driver.quit()
    return html

import re
from bs4 import BeautifulSoup

def price(soup):
    """Extract price from the given soup object."""
    price_tag = soup.find('span', class_='price mr-1')
    if not price_tag:
        return None  # Return None if no price is found
    
    # Extract the price and remove any unwanted characters (like commas, spaces)
    price = price_tag.get_text(strip=True).replace('₹', '').replace(',', '').strip()

    # Add "Rs" prefix to the price
    price = f"Rs {price}"

    # Extract the quantity (next to "incl. Tax" or similar)
    quantity_tag = soup.find('span', class_='per-pices')
    quantity = None
    if quantity_tag:
        quantity_text = quantity_tag.get_text(strip=True)
        # Capture numbers and units (e.g., "3000 kgs", "per piece")
        quantity_match = re.search(r'(\d+(\.\d{1,2})?\s*(kgs|tonne|piece|pcs|per piece))', quantity_text, re.IGNORECASE)
        if quantity_match:
            quantity = quantity_match.group(1)
    
    # Combine price and quantity into one string with "/"
    if quantity:
        return f"{price}/{quantity}"
    else:
        return f"{price}/per piece"  # Default to "per piece" if no quantity found





def extract_description(soup):
    h4_element = soup.find('h4')

    # Extract and return the text from the <h4> element
    return h4_element.text.strip() if h4_element else None

def extract_grad(description):
   
    # Regular expression to match grades like 'FE 500', 'FE 550', 'FE 500D', 'FE 550D'
    grade_match = re.search(r'FE \d{3}(D)?', description)
    
    if grade_match:
        # Return the matched grade
        return grade_match.group(0)
    else:
        # Return None if no grade found
        return None
def extract_grade(text):
    """
    Extracts the grade (e.g., 550SD, Fe-500, Fe-550) from the product description text.
    """
    grade_pattern = r'\b(Fe[-]?\d{3}[A-Za-z]?)\b|\b(\d{3}SD)\b'
    grade_match = re.search(grade_pattern, text)
    if grade_match:
        return grade_match.group(0)
    elif extract_grad(text):
        return extract_grad(text)
    else:
        return 'Fe 500 & Fe 550'  # Default to this if no grade found


def diameter(soup):
    """Extract the product diameter."""
    a_tags = soup.find_all('a', href="javascript:void(0)")
    for a_tag in a_tags:
        if 'Diameter' in a_tag.get_text():
            diameter_text = a_tag.get_text(strip=True).replace('Diameter: ', '')
            return diameter_text
    return None


def scrape_url(url, feature):
    """Scrape individual page data and store results in the dictionary."""
    html_content = scrape_dynamic_content(url)  # Get dynamic content using Selenium
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract product details from the page
    products = soup.find_all('div', class_='col-lg-3 col-md-3 p-0 mb-3')

    for product in products:
        price_value = price(product)
        title_value = extract_description(product)


        if price_value and title_value:
            
            d["Price"].append(price_value)
            d["Grade"].append(extract_grade(title_value))
            d["Diameter"].append(diameter(product) or 'NA')
            d["Location"].append('Noida')
            d["URL"].append(url)
            d["Brand"].append(feature)


def save_data_to_csv(data):
    """Save the collected data to a CSV file."""
    df = pd.DataFrame(data)
    if not df.empty:
        if os.path.exists(stored_file_path):
            df.to_csv(stored_file_path, mode='a', index=False, header=False)
        else:
            df.to_csv(stored_file_path, index=False)
        print(f"Data successfully saved to {stored_file_path}")
    else:
        print("No data to save.")


def main():
    """Main function to execute the scraping workflow."""
    start_urls = [
        "https://mccoymart.com/buy/tmt-bars/?mfp=2%5B57%2C61234%5D%2C4%5B613%5D",
        "https://mccoymart.com/buy/tmt-bars/?mfp=2%5B57%2C61234%5D%2C4%5B546%5D",
        "https://mccoymart.com/buy/tmt-bars/?mfp=2%5B57%2C61234%5D%2C4%5B601%5D",
        "https://mccoymart.com/buy/tmt-bars/?mfp=2%5B57%2C61234%5D%2C4%5B652%5D",
        "https://mccoymart.com/buy/tmt-bars/?mfp=2%5B57%2C61234%5D%2C4%5B614%5D"
    ]
    features = ['Tata Steel', 'SAIL', 'JSW Neo', 'JSW Neo', 'Jindal Panther']

    # Scrape each URL
    for url, feature in zip(start_urls, features):
        print(f"Scraping {url} for {feature}...")
        scrape_url(url, feature)

    # Save data to CSV
    save_data_to_csv(d)


if __name__ == "__main__":
    main()





# import os
# import pandas as pd
# from load_file import stored_file_path
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# import time
# from bs4 import BeautifulSoup
# import re


# # Global dictionary to store data
# d = {
#     "Brand": [],
#     "Price": [],
#     "URL": [],
#     "Location": [],
#     "Diameter": [],
#     "Grade": [],
# }


# def scrape_dynamic_content(url):
#     """Use Selenium to load dynamic content."""
#     options = webdriver.ChromeOptions()
#     options.add_argument("--disable-gpu")
#     options.add_argument("--no-sandbox")
#     options.add_argument("--headless")
#     driver = webdriver.Chrome(options=options)
#     driver.get(url)
#     driver.implicitly_wait(10)  # Wait for the page to load

#     # Scroll to the bottom of the page to load dynamic content
#     last_height = driver.execute_script("return document.body.scrollHeight")
#     while True:
#         driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#         time.sleep(2)  # Wait for content to load
#         new_height = driver.execute_script("return document.body.scrollHeight")
#         if new_height == last_height:
#             break
#         last_height = new_height

#     # Get the page source once everything is loaded
#     html = driver.page_source
#     driver.quit()
#     return html

# import re
# from bs4 import BeautifulSoup

# def price(soup):
#     """Extract price from the given soup object."""
#     price_tag = soup.find('span', class_='price mr-1')
#     if not price_tag:
#         return None  # Return None if no price is found
    
#     # Extract the price and remove any unwanted characters (like commas, spaces)
#     price = price_tag.get_text(strip=True).replace('₹', '').replace(',', '').strip()

#     # Add "Rs" prefix to the price
#     price = f"Rs {price}"

#     # Extract the quantity (next to "incl. Tax" or similar)
#     quantity_tag = soup.find('span', class_='per-pices')
#     quantity = None
#     if quantity_tag:
#         quantity_text = quantity_tag.get_text(strip=True)
#         # Capture numbers and units (e.g., "3000 kgs", "per piece")
#         quantity_match = re.search(r'(\d+(\.\d{1,2})?\s*(kgs|tonne|piece|pcs|per piece))', quantity_text, re.IGNORECASE)
#         if quantity_match:
#             quantity = quantity_match.group(1)
    
#     # Combine price and quantity into one string with "/"
#     if quantity:
#         return f"{price}/{quantity}"
#     else:
#         return f"{price}/per piece"  # Default to "per piece" if no quantity found





# def extract_description(soup):
#     h4_element = soup.find('h4')

#     # Extract and return the text from the <h4> element
#     return h4_element.text.strip() if h4_element else None

# def extract_grad(description):
   
#     # Regular expression to match grades like 'FE 500', 'FE 550', 'FE 500D', 'FE 550D'
#     grade_match = re.search(r'FE \d{3}(D)?', description)
    
#     if grade_match:
#         # Return the matched grade
#         return grade_match.group(0)
#     else:
#         # Return None if no grade found
#         return None
# def extract_grade(text):
#     """
#     Extracts the grade (e.g., 550SD, Fe-500, Fe-550) from the product description text.
#     """
#     grade_pattern = r'\b(Fe[-]?\d{3}[A-Za-z]?)\b|\b(\d{3}SD)\b'
#     grade_match = re.search(grade_pattern, text)
#     if grade_match:
#         return grade_match.group(0)
#     elif extract_grad(text):
#         return extract_grad(text)
#     else:
#         return 'Fe 500 & Fe 550'  # Default to this if no grade found


# def diameter(soup):
#     """Extract the product diameter."""
#     a_tags = soup.find_all('a', href="javascript:void(0)")
#     for a_tag in a_tags:
#         if 'Diameter' in a_tag.get_text():
#             diameter_text = a_tag.get_text(strip=True).replace('Diameter: ', '')
#             return diameter_text
#     return None


# def scrape_url(url, feature):
#     """Scrape individual page data and store results in the dictionary."""
#     html_content = scrape_dynamic_content(url)  # Get dynamic content using Selenium
#     soup = BeautifulSoup(html_content, 'html.parser')

#     # Extract product details from the page
#     products = soup.find_all('div', class_='col-lg-3 col-md-3 p-0 mb-3')

#     for product in products:
#         price_value = price(product)
#         title_value = extract_description(product)


#         if price_value and title_value:
            
#             d["Price"].append(price_value)
#             d["Grade"].append(extract_grade(title_value))
#             d["Diameter"].append(diameter(product) or 'NA')
#             d["Location"].append('Noida')
#             d["URL"].append(url)
#             d["Brand"].append(feature)


# def save_data_to_csv(data):
#     """Save the collected data to a CSV file."""
#     df = pd.DataFrame(data)
#     if not df.empty:
#         if os.path.exists(stored_file_path):
#             df.to_csv(stored_file_path, mode='a', index=False, header=False)
#         else:
#             df.to_csv(stored_file_path, index=False)
#         print(f"Data successfully saved to {stored_file_path}")
#     else:
#         print("No data to save.")


# def main():
#     """Main function to execute the scraping workflow."""
#     start_urls = [
#         "https://mccoymart.com/buy/tmt-bars/?mfp=2%5B57%2C61234%5D%2C4%5B613%5D",
#         "https://mccoymart.com/buy/tmt-bars/?mfp=2%5B57%2C61234%5D%2C4%5B546%5D",
#         "https://mccoymart.com/buy/tmt-bars/?mfp=2%5B57%2C61234%5D%2C4%5B601%5D",
#         "https://mccoymart.com/buy/tmt-bars/?mfp=2%5B57%2C61234%5D%2C4%5B652%5D",
#         "https://mccoymart.com/buy/tmt-bars/?mfp=2%5B57%2C61234%5D%2C4%5B614%5D"
#     ]
#     features = ['Tata Steel', 'SAIL', 'JSW Neo', 'JSW Neo', 'Jindal Panther']

#     # Scrape each URL
#     for url, feature in zip(start_urls, features):
#         print(f"Scraping {url} for {feature}...")
#         scrape_url(url, feature)

#     # Save data to CSV
#     save_data_to_csv(d)


# if __name__ == "__main__":
#     main()
