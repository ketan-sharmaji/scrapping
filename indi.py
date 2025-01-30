import re
import requests
import time
from bs4 import BeautifulSoup
import html2text
import csv
from selenium import webdriver  # Import the webdriver module
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.edge.options import Options as EdgeOptions

# Function to scrape dynamic content using Selenium
def scrape_dynamic_content(url):
    options = EdgeOptions()

    options.add_argument("--allow-insecure-localhost")
    options.add_argument("--disable-gpu")        # Disable GPU hardware acceleration
    options.add_argument("--no-sandbox")         # Disable sandbox (security feature)
    options.add_argument("--headless")           # Run headless (without opening browser window)
    options.add_argument("--disable-dev-shm-usage")  # Avoids issues with shared memory
    options.add_argument("disable-infobars")    # Disable infobars like 'Chrome is being controlled by automated software'
    options.add_argument("--disable-extensions") # Disabling browser extensions
    options.add_argument("--disable-webgl")
    options.add_argument("--disable-notifications")
    options.add_argument("--ignore-certificate-errors")  # Ignore SSL certificate errors

    service = EdgeService(EdgeChromiumDriverManager().install())
    service.start()  # Start the service

    # Pass the service and options to the webdriver
    driver = webdriver.Edge(service=service, options=options)
    
    driver.get(url)
    driver.implicitly_wait(10)  # Wait for the page to load
    
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Wait for content to load
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    html = driver.page_source
    driver.quit()
    return html

# The URL to scrape
url = "https://www.indiamart.com/proddetail/10mm-tata-tiscon-tmt-bar-2851518476297.html"
k = scrape_dynamic_content(url)

# Parse the page content with BeautifulSoup
soup = BeautifulSoup(k, "html.parser")

# Initialize the dictionary
d = {
    "Brand": [],
    "Price": [],
    "URL": [],
    "Location": [],
    "Diameter": [],
    "Grade": []
}

# Extract values
diameter = soup.find('td', text='Diameter').find_next('td').text.strip()
grade = soup.find('td', text='Grade').find_next('td').text.strip()
brand = soup.find('td', text='Brand').find_next('td').text.strip()

# Extract price and unit
price = soup.find('span', class_='bo price-unit').text.strip().replace('₹', 'Rs')  # Replacing ₹ with Rs
unit = soup.find('span', class_='units pcl76').text.strip()

# Format price and unit
formatted_price = f"{price}({unit})"

# Assign extracted values to the dictionary
d["Brand"].append(brand)
d["Price"].append(formatted_price)
d["URL"].append(url)  # Assigning the URL to the dictionary
d["Diameter"].append(diameter)
d["Grade"].append(grade)
d["Location"].append("na")

# Print the updated dictionary
