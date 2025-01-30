
from load_file import *
from bs4 import BeautifulSoup
import requests
import pandas as pd
import os

def main():
    # URL of the website
    url = "https://www.klgecolite.in/tmt-bars.html"

    # Send a GET request to the website
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content of the webpage
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Data storage lists corresponding to the dictionary structure
        brands = []
        prices = []
        urls = []
        locations = []
        diameters = []
        grades = []
        
        # Assuming products are contained in divs with a specific class, adjust if necessary
        products = soup.find_all('div', class_='w16 ds3 vr2 bx2 bg1 bx3 ps2 prd2 txt2 p17')  # Adjust this if needed
        
        for product in products:
            # Extracting details from each product
            brand = None
            price = None
            diameter = None
            grade = None

            # Find the table that contains the product details
            table = product.find('table')
            
            if table:
                rows = table.find_all('tr')
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) == 2:
                        key = cells[0].text.strip()
                        value = cells[1].text.strip()

                        # Match keys to corresponding values
                        if key == "Brand":
                            brand = value
                        elif key == "Diameter":
                            diameter = value
                        elif key == "Grade":
                            grade = value

            # Extracting price - adjust class if needed
            price_span = product.find('span', class_='fnt18 clr16')  # Adjust if needed
            if price_span:
                price = price_span.text.strip()

            # Append the data to the lists
            brands.append(brand if brand else "N/A")
            prices.append(price if price else "N/A")
            diameters.append(diameter if diameter else "N/A")
            grades.append(grade if grade else "N/A")
            urls.append("https://www.klgecolite.in/tmt-bars.html")
            locations.append("Kolkata")

        # Create the dictionary as per the provided structure
        data = {
            "Brand": brands,
            "Price": prices,
            "URL": urls,
            "Location": locations,
            "Diameter": diameters,
            "Grade": grades
        }

        # Create a DataFrame
        df = pd.DataFrame(data)

        # Check if the file exists
        if os.path.exists(stored_file_path):
            # Append the data to the existing file
            df.to_csv(stored_file_path, mode='a', index=False, header=False)
        else:
            # Create a new file with a header
            df.to_csv(stored_file_path, index=False)
    else:
        print(f"Failed to fetch data. HTTP Status Code: {response.status_code}")

# Ensure this script runs only when executed directly
if __name__ == "__main__":
    main()
