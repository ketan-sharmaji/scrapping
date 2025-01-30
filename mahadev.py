

import requests
from bs4 import BeautifulSoup
import pandas as pd
from load_file import stored_file_path
import os

def mahadev():
    # URL of the website
    url = "https://www.mahadevironsteel.com/tmt-bar.html"

    # Send a GET request to the website
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch data. HTTP Status Code: {response.status_code}")
        return

    # Parse the HTML content of the webpage
    soup = BeautifulSoup(response.text, 'html.parser')

    # Data storage lists
    min_order_qty = []
    diameters = []
    brand_names = []
    prices = []
    grades = []
    location = []

    # Locate the specific section containing TMT steel data
    products = soup.find_all('div', class_='cont9 bx2 w1 ds2 ps2')  # Adjust selector if needed
    print(f"Found {len(products)} products.")

    for product in products:
        # Initialize temporary variables for each product
        loc, min_qty, diameter, grade, price, brand = None, None, None, None, None, None

        # Find the table inside the current product
        table = product.find('table')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) == 2:
                    key = cells[0].text.strip()
                    value = cells[1].text.strip()

                    # Match the required fields
                    if key == "Minimum Order Quantity":
                        min_qty = value
                    elif key == "Diameter":
                        diameter = value
                    elif key == "Grade":
                        grade = value
                    elif key == "Country of Origin":
                        loc = value

        # Extract price
        price_span = product.find('span', class_='fnt18 clr16')
        if price_span:
            price = price_span.text.strip()

        # Extract brand
        brand_span = product.find('h2', class_='clr13 fnt7 fnt17 bo1 videoclass')
        if brand_span:
            brand = brand_span.text.strip()

        # Standardize location
        if loc == "Made in India":
            loc = "India"

        # Append the data to lists (use placeholders for missing data)
        min_order_qty.append(min_qty if min_qty else "N/A")
        diameters.append(diameter if diameter else "N/A")
        grades.append(grade if grade else "N/A")
        brand_names.append(brand if brand else "N/A")
        prices.append(price if price else "N/A")
        location.append(loc if loc else "N/A")

    # Create a DataFrame
    data = {
        "Brand": brand_names,
        "Price": prices,
        "URL": [url] * len(brand_names),
        "Location": location,
        "Diameter": diameters,
        "Grade": grades,
    }
    df = pd.DataFrame(data)
    
    print(df)

    # Save the DataFrame to CSV
    if os.path.exists(stored_file_path):
        # Append the data to the existing file
        df.to_csv(stored_file_path, mode='a', index=False, header=False)
    else:
        # Create a new file with a header
        df.to_csv(stored_file_path, index=False)

if __name__ == "__main__":
    mahadev()


