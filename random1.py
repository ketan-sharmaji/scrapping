import os
import re
import pandas as pd
import requests
from bs4 import BeautifulSoup
import html2text
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time


from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.edge.options import Options as EdgeOptions

# Predefined list of brands
BRANDS = ["Jindal", "JSW", "TATA", "Vizag", "RINL", "SAIL","Steel India of Authority"]

def extract_information(chunk, url):
    """
    Extract diameter (or size), price, brand, grade, and other relevant attributes from the text chunk.
    """
    # Initialize variables
    diameter = None
    price = None
    quantity = None
    brand = None
    grade = None
    
    # Extract diameter/size
    diameter_pattern = r"(diameter|size)\s*[:|=|-]?\s*([\d.]+)\s*(mm|cm|m|inch)?"
    diameter_match = re.search(diameter_pattern, chunk, re.IGNORECASE)
    if not diameter_match:
        diameter_pattern = r"\b(\d{1,3}(\.\d{1,2})?)\s*(mm|cm|m|inch)\b"
        diameter_match = re.search(diameter_pattern, chunk, re.IGNORECASE)
    if diameter_match:
        diameter = f"{diameter_match.group(2)} {diameter_match.group(3) or ''}".strip()

    # Extract grade (e.g., Fe 500D)
    grade_pattern = r"Grade\s*[:|=|-]?\s*([A-Za-z0-9]+[\s]*[A-Za-z0-9]*)"
    grade_match = re.search(grade_pattern, chunk, re.IGNORECASE)
    if grade_match:
        grade = grade_match.group(1).strip()

    # Extract price
    price_pattern = r"₹\s*([\d,]+(\.\d{1,2})?)\s*/?\s*([A-Za-z]*)|Rs\s*([\d,]+(\.\d{1,2})?)\s*/\s*([A-Za-z]*)"
    price_match = re.search(price_pattern, chunk)

    if price_match:
        # Handle ₹ format (previous format)
        if price_match.group(1):
            price = price_match.group(1).replace(',', '')
            quantity = price_match.group(3) or "tonne"
        # Handle Rs format (new format)
        elif price_match.group(4):
            price = price_match.group(4).replace(',', '')
            quantity = price_match.group(6) or "tonne"
        
        # Format price as "price /unit"
        if price and quantity:
            price = f"{price} /{quantity.lower()}"

    # Extract brand
    for b in BRANDS:
        if re.search(rf"\b{b}\b", chunk, re.IGNORECASE):
            brand = b
            break

    # Check if grade, price, and brand are available
    if grade and price and brand:
        return {
            "diameter": diameter or "N/A",
            "price": price,
            "brand": brand,
            "grade": grade,
            "url": url,
            "location": "N/a"
        }

    # Skip the chunk if grade, price, or brand is missing
    return None

def scrape_dynamic_content(url):
    options = EdgeOptions()
    options.add_argument("--disable-gpu")        # Disable GPU hardware acceleration
    options.add_argument("--no-sandbox")         # Disable sandbox (security feature)
    options.add_argument("--headless")           # Run headless (without opening browser window)
    options.add_argument("--disable-dev-shm-usage")  # Avoids issues with shared memory
    options.add_argument("disable-infobars")    # Disable infobars like 'Chrome is being controlled by automated software'
    options.add_argument("--disable-extensions") # Dis
    options.add_argument("--disable-webgl")
    options.add_argument("--disable-notifications")
    options.add_argument("--ignore-certificate-errors")  # Ignore SSL certificate errors



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

def extract_all_text(url):
   
    try:
        html_content = scrape_dynamic_content(url)  # Get dynamic content using Selenium
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove unnecessary elements
        for script in soup(['script', 'style', 'header', 'footer', 'nav', 'img']):
            script.decompose()

        # Convert to plain text using html2text
        html_content = str(soup)
        h = html2text.HTML2Text()
        h.ignore_links = True
        markdown_content = h.handle(html_content)
        return markdown_content

    except Exception as e:
        return str(e)

def extract_entities_with_context(text, keywords, context_size=40):
   
    entities_with_context = []
    for keyword in keywords:
        matches = re.finditer(r'\b{}\b'.format(re.escape(keyword)), text, re.IGNORECASE)
        for match in matches:
            start = max(match.start() - context_size - 150, 0)
            end = min(match.end() + context_size + 150, len(text))
            context = text[start:end]
            entities_with_context.append({
                'match': match.group(),
                'context': context.strip()
            })
    return entities_with_context

def save_to_csv(data, stored_file_path):
    # Create a DataFrame
    df = pd.DataFrame(data)

    # Capitalize only the first letter of each column name, with special case for 'URL'
    df.columns = [col.upper() if col == 'url' else col.capitalize() for col in df.columns]

    # Define the desired column order
    column_order = ['Brand', 'Price', 'URL','Location', 'Diameter', 'Grade']

    # Check if all expected columns are present in the DataFrame
    missing_columns = [col for col in column_order if col not in df.columns]
    if missing_columns:
        print(f"Warning: Missing columns {missing_columns}. Please check the data.")
        return  # Exit the function if any required columns are missing

    # Reorder the columns to the desired order
    df = df[column_order]

    # Check if the file exists
    if os.path.exists(stored_file_path):
        # Append the data to the existing file without writing the header
        df.to_csv(stored_file_path, mode='a', index=False, header=False)
    else:
        # Create a new file with a header
        df.to_csv(stored_file_path, index=False)

def main(url, stored_file_path):
    print("Fetching content from URL...")
    markdown_content = extract_all_text(url)
    print("Content fetched successfully.")

    keywords = ['Grade', 'Diameter', 'Size', 'Brand', 'Price','diameter','brand']
    entities = extract_entities_with_context(markdown_content, keywords)
    
    extracted_data = []
    for entity in entities:
        details = extract_information(entity['context'], url)
        if details:
            extracted_data.append(details)
            print(details)

    # Save the extracted data to CSV
    if extracted_data:
        save_to_csv(extracted_data, stored_file_path)
        
        
    

if __name__ == "__main__":
    main()
