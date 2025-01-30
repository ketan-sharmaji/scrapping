import requests
from bs4 import BeautifulSoup
import re
import time
import pandas as pd
import os
from load_file import *
# Dictionary to store product data
d = {
    "Brand": [],
    "Price": [],
    "URL": [],
    "Location": [],
    "Diameter": [],
    "Grade": []
}


# Retry mechanism for requests
def fetch_url_with_retry(url, retries=3, timeout=10):
    for i in range(retries):
        try:
            response = requests.get(url, timeout=timeout)
            return response
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            time.sleep(5)  # Wait before retrying
    print(f"Failed to fetch {url} after {retries} attempts.")
    return None

# Scrape a single page for product details
def scrape(url, grade):
    response = fetch_url_with_retry(url)
    if response is None:
        return  # Skip this page if request fails
    
    location = "Hyderabad"
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all product divs
        product_name_divs = soup.find_all('div', class_='item-inner compare-item')

        # Extract product details
        for div in product_name_divs:
            product_seller_name = seller(div)
            if product_seller_name in list1:
                d['Brand'].append(product_seller_name)
                d["Location"].append(location)
                urlll = urll(div)
                d["URL"].append(urlll)
                d["Grade"].append(grade)
    else:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")

# Function to extract seller's name
def seller(div):
    product_seller_tag = div.find('div', class_='product-seller')
    if product_seller_tag:
        seller_name = product_seller_tag.find('span').text.strip()
        return seller_name
    return None

# Extract URL from the product div
def urll(div):
    link = div.find('a', class_='compareproductname')
    if link and link.get('href'):
        return link['href']
    link = div.find('a', title=True)
    if link and link.get('href'):
        return link['href']
    return 'NA'



# Extract price of the product

def extract_price(soup):
    # Extract special price (if available)
    special_price = soup.find('p', class_='special-price')
    if special_price:
        # Get the price text
        special_price_text = special_price.find('span', class_='price').get_text(strip=True)
        # Remove the first period after "Rs"
        special_price_text = re.sub(r'(Rs)\.(\d)', r'\1 \2', special_price_text)
        
        # Extract quantity information (if available)
        quantity_info = special_price.find('span', class_='pricelabletag')
        quantity_text = quantity_info.get_text(strip=True) if quantity_info else ''
        
        # Combine price and quantity text
        return f"{special_price_text} {quantity_text}".strip()
    
    # Extract regular price (if available)
    regular_price = soup.find('span', class_='regular-price')
    if regular_price:
        # Get the price text
        regular_price_text = regular_price.find('span', class_='price').get_text(strip=True)
        # Remove the first period after "Rs"
        regular_price_text = re.sub(r'(Rs)\.(\d)', r'\1 \2', regular_price_text)
        
        # Extract quantity information (if available)
        quantity_info = regular_price.find('span', class_='pricelabletag')
        quantity_text = quantity_info.get_text(strip=True) if quantity_info else ''
        
        # Combine price and quantity text
        return f"{regular_price_text} {quantity_text}".strip()
    
    return None

def size(url):
    pattern = r"(\d+)mm"
    match = re.search(pattern, url)
    if match:
        return match.group(1)  
    return "NA"



# Extract brand information from the product page
def brand(soup):
    brand_row = soup.find('tr', string=lambda text: text and 'Brand / Manufacturer' in text)
    if brand_row:
        brand_value = brand_row.find_all('td')[-1].get_text(strip=True)
        return brand_value
    return "Brand not found"

def extract_all_text(url):
    response = fetch_url_with_retry(url, retries=2)
    if response is None:
        return  # Skip if the request failed
    soup = BeautifulSoup(response.text, 'html.parser')

    d['Price'].append(extract_price(soup))
    d['Diameter'].append(size(url))

# Function to scrape all pages
def scrape_all_pages(base_url, grade):
    current_page_url = base_url
    while True:
        print(f"Scraping {current_page_url}")
        scrape(current_page_url, grade)

        response = fetch_url_with_retry(current_page_url)
        if not response:
            break  # Exit if request fails

        soup = BeautifulSoup(response.content, 'html.parser')
        next_page_link = soup.find('a', class_='next i-next')
        
        if next_page_link:
            current_page_url = next_page_link['href']
        else:
            print("No more pages to scrape.")
            break

# Example usage for scraping different grades
def main():
    try:

        base_url_500 = 'https://www.buildersmart.in/tmt-steel/fe-500-grade-tmt-bars'
        scrape_all_pages(base_url_500, '500')

        base_url_550 = "https://www.buildersmart.in/tmt-steel/fe-550-grade-tmt-bars"
        scrape_all_pages(base_url_550, '550')

        # Now extract additional information (price and diameter)
        for url in d['URL']:
            extract_all_text(url)

        # Save data to CSV
        df = pd.DataFrame(d)
        if os.path.exists(stored_file_path):
            df.to_csv(stored_file_path, mode='a', index=False, header=False)
        else:
            df.to_csv(stored_file_path, index=False)

        print(f"Data saved to {stored_file_path}")

    except Exception as e:
        print(f"Error occurred: {e}")
        # Save data collected up to this point
        df = pd.DataFrame(d)
        df.to_csv(stored_file_path, mode='a', index=False, header=False)
        print(f"Partial data saved to {stored_file_path}")

# Define list of sellers you're interested in
list1 = ["JSW-TMT", "Jindal-TMT", "Tata-TMT", "Steel Authority of In...", "Vizag-TMT"]

# Start the scraping process
if __name__ == "__main__":
    main()

