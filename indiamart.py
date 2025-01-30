from inputs import *
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import requests
from bs4 import BeautifulSoup
import re
from load_file import * 
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.edge.options import Options as EdgeOptions


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
    driver.implicitly_wait(10)
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    html = driver.page_source
    driver.quit()
    return html

# (Other functions remain unchanged)

def extract_location(soup):
    # Try to find the short location (e.g., "Strand Road, Kolkata")
    short_location_tag = soup.find('span', class_='elps elps1')
    if short_location_tag:
        short_location = short_location_tag.text.strip()
    else:
        short_location = None  # If no short location is found

    return short_location

def extract_price(soup):
    # Find the <p> tag with class 'price'
    price_tag = soup.find('p', class_='price')
    
    if price_tag:
        # Extract the price value (e.g., ₹62,500)
        price_value = price_tag.text.strip().split(' ')[0].replace('₹', '').strip()
        
        # Extract the unit (e.g., tonne)
        unit_tag = price_tag.find('span', class_='unit')
        if unit_tag:
            unit_value = unit_tag.text.strip()  # This will return '/Tonne'
            
            # Return the price along with its unit (per tonne)
            return f"₹{price_value} {unit_value}"
        
    return None  # If no price or unit is found

# Function to extract the diameter or size/dimension
def extract_dia(soup):
    diameter_keywords = ['Diameter', 'Size', 'Dimension']
    for row in soup.find_all('tr'):
        # Get the column labels (first <td> in each row)
        label = row.find('td', class_='tdwdt')
        if label:
            label_text = label.text.strip()
            # If the label matches any diameter-related keywords, extract the corresponding value
            if any(keyword.lower() in label_text.lower() for keyword in diameter_keywords):
                value = row.find('td', class_='tdwdt1')
                if value:
                    diameter_value = value.text.strip()
                    return diameter_value
    return 'N/a'  # Return 'N/a' if no diameter is found

def extract_g(soup):
    for row in soup.find_all('tr'):
        label = row.find('td', class_='tdwdt')
        if label:
            label_text = label.text.strip()
            if 'Grade' in label_text:
                value = row.find('td', class_='tdwdt1')
                if value:
                    grade_value = value.text.strip()
                    return grade_value
    return 'N/a'  # Return 'N/a' if no grade is found


def extract_grad(description, soup):
    pattern = r'Fe[-\s]?(\d{3,4})(D?)'
    match = re.search(pattern, description, re.IGNORECASE)
    
    if match:
        grade = f"Fe-{match.group(1)}{match.group(2).upper()}" if match.group(2) else f"Fe-{match.group(1)}"
        return grade
    
    if soup:
        return extract_g(soup)
    return 'N/a'


def extract_link(soup):
   
    link_tag = soup.find('div', class_='producttitle').find('a', class_='cardlinks') if soup.find('div', class_='producttitle') else None
    
    # Check if the link tag is found and if it contains the 'href' attribute
    if link_tag and 'href' in link_tag.attrs:
        return link_tag['href']
    else:
        return None

def extract_product_name(soup):
    # Try to find the <div> tag with class 'producttitle'
    product_title_tag = soup.find('div', class_='producttitle')
    
    if product_title_tag:
        # Find the <a> tag inside the <div> with class 'producttitle'
        product_link = product_title_tag.find('a', class_='cardlinks')
        if product_link:
            # Extract the text of the product name, removing the <b> tags
            product_name = product_link.text.strip()
            return product_name
    return None  # Return None if no product name is found


def link_c(source):
    link_tag = source.find('a', class_='fs18 ptitle')
    if link_tag and 'href' in link_tag.attrs:
        return link_tag['href']
    else: 
        return 'Na'   

def title_c(source):
    h3_tag = source.find('h3')
    if h3_tag:
        name = h3_tag.text.strip()
        return name
    else:
        return 'NA'

def extract_grade(description, soup):
    pattern = r'Fe[-\s]?(\d{3,4})(D?)'
    match = re.search(pattern, description, re.IGNORECASE)
    
    if match:
        grade = f"Fe-{match.group(1)}{match.group(2).upper()}" if match.group(2) else f"Fe-{match.group(1)}"
        return grade
    
    if soup:
        return grade_c(soup)
    return 'N/a'




def grade_c(source):
    rows = source.find_all('tr')
    for row in rows:
        label = row.find('td').get_text(strip=True)
        value = row.find_all('td')[1].get_text(strip=True)
        if label.lower() == "grade":
            return value
    return 'N/a'




def extract_diameter(description, soup):
    diameter_pattern = r'(\d+)\s?mm'
    match = re.search(diameter_pattern, description, re.IGNORECASE)
    
    if soup:
        return diameter_c(soup)
    if match:
        return match.group(0)
    return 'N/a'




def diameter_c(source):
    rows = source.find_all('tr')
    for row in rows:
        label = row.find('td').get_text(strip=True)
        value = row.find_all('td')[1].get_text(strip=True)
        if label in ["Diameter", "Diameter.", "Size", "Size.", "Dimension"]:
            return value
    return 'N/a'


def price_c(source):
    # Find the price tag with the class 'prc cur'
    price_tag = source.find('span', class_='prc cur')
    
    if price_tag:
        # Extract the price (e.g., ₹ 64)
        price_text = price_tag.get_text(strip=True)
        
        # Check if '₹' is present in the text
        if '₹' in price_text:
            # Extract the price amount (after the ₹ symbol)
            price_amount = price_text.split('₹')[1].split('/')[0].strip()
            
            # Extract the quantity (unit), e.g., 'Kg'
            unit_tag = price_tag.find('span', class_='quan')
            if unit_tag:
                unit_value = unit_tag.get_text(strip=True)
                return f"₹{price_amount} per {unit_value}"
            else:
                return 'Unit not found'
        else:
            return 'N/A'  # In case there's no ₹ symbol in the price text
    else:
        return 'N/A'  # If price tag is not found





def location_c(source):
    loc = source.find('p', class_='sm clg')
    if loc:
        return loc.text.strip()
    else:
        return 'N/A'



def main(locationnn):

    url = f"https://dir.indiamart.com/{locationnn.lower()}/tata-tmt-bars.html"
    url2 = f"https://dir.indiamart.com/{locationnn.lower()}/jindal-tmt-bars.html"
    url3 = f"https://dir.indiamart.com/{locationnn.lower()}/sail-tmt-bars.html"
    url4 = f"https://dir.indiamart.com/{locationnn.lower()}/jsw-trusteel-tmt-bars.html"
    url5 = f"https://dir.indiamart.com/{locationnn.lower()}/jsw-neosteel.html"
    url6 = f"https://dir.indiamart.com/search.mp?ss=rinl+tmt+bar&cq={locationnn.lower()}&v=4&mcatid=2475&catid=795&cq_src=city-search_2&tags=res:RC5|ktp:N0|stype:attr=1-br|mtp:G|wc:3|cq:hyderabad|qr_nm:gd|cs:9530|com-cf:nl|ptrs:na|mc:2475|cat:795|qry_typ:P|lang:en|rtn:0-0-0-0-1-9-0"
    

    list1 = [url, url2, url3, url4, url5, url6]
    list2 = ["Tata Steel", "Jindal Steel", "SAIL Steel", "JWS", "JWS", "RINL Steel"]


    d = {
        "Brand": [],
        "Price": [],
        "URL": [],
        "Location": [],
        "Diameter": [],
        "Grade": []
    }


    for url, company in zip(list1, list2):

        if url == list1[-1]:
            link=[]
            html_content = scrape_dynamic_content(url)  # Use the scrape function from the second script
            soup = BeautifulSoup(html_content, 'html.parser')

            product_titles = soup.find_all('div', class_='cardbody')

            for title in product_titles:
                location = extract_location(title)
                d["Location"].append(location)

                
                price = extract_price(title)
                d["Price"].append(price)

                url = extract_link(title)
                link.append(url)

                d['Brand'].append(company)


            for i in link:
                
                if i != None:
                    response= requests.get(i)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    description= extract_product_name(title)
                    d['Diameter'].append(extract_dia(soup))
                    d['Grade'].append(extract_grad(description,soup))
                    d['URL'].append(i)


                else:
                    d['Diameter'].append(None)
                    d['Grade'].append(None)
                    d['URL'].append(None)


        else:
            html_content = scrape_dynamic_content(url)
            soup = BeautifulSoup(html_content, 'html.parser')

            product_titles = soup.find_all(class_='rht pnt flx')

            for title in product_titles:
                link = link_c(title)
                price = price_c(title)
                description = title_c(title)
                grade = extract_grade(description, title)
                diameter = extract_diameter(description, title)

                if price != 'N/a' and diameter != 'N/a':
                    d['URL'].append(link)
                    d['Price'].append(price)
                    d['Grade'].append(grade)
                    d['Diameter'].append(diameter)
                    d['Brand'].append(company)
                    k = soup.find(class_='r-cl b-gry')
                    location = location_c(k)
                    d['Location'].append(location)

    df = pd.DataFrame(d)
    df = df[df['Price'] != 'N/a']
    df = df[df['Diameter'] != 'N/a']
    df.to_csv('indiamartt.csv', index=False)



if __name__ == "__main__":
    main()



