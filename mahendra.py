
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from load_file import stored_file_path
import os

# List of target brands
list1 = ["JSW NEO STEEL", "Rathi"]

# Data storage list
data = []

# Function to extract data from a table row
def extract_data(soup, label):
    tag = soup.find('td', string=re.compile(label, re.IGNORECASE))
    return tag.find_next('td').text.strip() if tag else None

# Function to extract price
def extract_price(soup):
    price_tags = soup.find_all('span', class_='fnt18 clr16')
    for tag in price_tags:
        price_text = tag.text.strip()
        # Remove unwanted characters
        return price_text.replace('\xa0', '').replace('Rs', '').strip()
    return None

# Main scraping function
def scrape(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        products = soup.find_all('div', class_="w16 ds3 vr2 bx2 bg1 bx3 ps2 prd2 txt2 p17")
        
        for div in products:
            brand = extract_data(div, "Brand")
            if brand in list1:
                product_data = {
                    "Brand": brand,
                    "Diameter": extract_data(div, "Diameter"),
                    "Grade": extract_data(div, "Grade"),
                    "Price": extract_price(div),
                    "URL": url,
                    "Location": "Delhi",
                }
                data.append(product_data)
    else:
        print(f"Failed to fetch URL: {url} (Status Code: {response.status_code})")

# Function to save data to CSV
def save_data_to_csv(data):
    if data:
        df = pd.DataFrame(data)
        if os.path.exists(stored_file_path):
            df.to_csv(stored_file_path, mode='a', index=False, header=False)
        else:
            df.to_csv(stored_file_path, index=False)
        print(f"Data successfully saved to {stored_file_path}")
    else:
        print("No data extracted to save.")

# Main function
def main():
    urls = [
        "https://www.mahendrasteels.com/tmt-bar.html",
        # Add more URLs if needed
    ]
    
    for url in urls:
        print(f"Scraping: {url}")
        scrape(url)
    
    # Save the data to a CSV file
    save_data_to_csv(data)

# Entry point
if __name__ == "__main__":
    main()
