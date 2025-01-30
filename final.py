import os
import argparse
import pandas as pd
import random1
import re
from load_file import *
from inputs import *
import indiamart
from func import *

def calculate_weight_per_piece(diameter_mm):
    length_meters = 12  # Standard length
    diameter_meters = float(diameter_mm) / 1000
    density = 7850  # kg/m³ for steel
    weight_kg = (3.14159 * (diameter_meters/2)**2 * length_meters * density)
    return weight_kg

def extract_diameter_from_description(description):
    diameter_pattern = r'(\d+)\s*mm'
    match = re.search(diameter_pattern, str(description).lower())
    if match:
        return float(match.group(1))
    return None

def clean_price(price, description):
    if pd.isna(price):
        return price

    price = str(price).strip().lower()
    
    # Check if price already contains 'kg' or 'ton'
    if 'kg' in price or 'ton' in price:
        price = price.replace("₹", "Rs ")
        price = re.sub(r'(\d+)/\s*tonnget', r'Rs \1/ ton', price)
        price = re.sub(r'\s*get$', ' kg', price)
        price = re.sub(r'get\s*/\s*', 'kg/', price)
        return price
    
    # Extract numeric value from price
    numeric_value = re.search(r'[\d,.]+', price)
    if not numeric_value:
        return price
    
    price_value = float(numeric_value.group().replace(',', ''))
    
    # Check if price is per piece
    if 'piece' in price or 'pc' in price or 'pcs' in price:
        diameter = extract_diameter_from_description(description)
        if diameter:
            weight = calculate_weight_per_piece(diameter)
            price_per_kg = price_value / weight
            return f"Rs {price_per_kg:.2f}/kg"
    
    # If no unit specified, add 'Rs ' prefix
    if price.isdigit():
        return f"Rs {price}"
    
    price = price.replace("₹", "Rs ")
    
    return price

def main():
    # Argument parsing
    parser = argparse.ArgumentParser(description="Process the input Excel file and output the results")
    parser.add_argument('test_file_path', type=str, help="Path to the input Excel file")
    parser.add_argument('output_directory', type=str, help="Directory to save the output file")

    args = parser.parse_args()

    test_file_path = args.test_file_path
    output_directory = args.output_directory

    test_file_path = test_file_path.replace("\\", "/")  # Replace backslashes with forward slashes
    output_directory = output_directory.replace("\\", "/")  # Ensure output directory uses forward slashes as well

    # Extract the base name from the Excel file (assuming 'Name' column is present)
    data = pd.read_excel(test_file_path)
    name = data['Name'].iloc[0]  # Fetch the first item from the Name column

    # Generate the output file name dynamically
    output_file_name = f"{name}_final.csv"
    output_file_path = os.path.join(output_directory, output_file_name)  # Combine directory and file name

    # Predefined stored file paths
    # stored_file_path = "scrapped_data.csv"
    # stored_file_path2 = "jsw.csv"

    # Extract data from the provided Excel file
    Description = data['Description'].tolist()
    locationnn = data['Location'].iloc[0]  # Fetch the first item from the Location column
    
    # Pass locationnn to indiamart.main()
    indiamart.main(locationnn)  # Now locationnn will be passed to indiamart.py

    final_data = []  # Initialize list for final data
    new_urls_set = set()  # Initialize an empty set for URLs
    for i in Description:
        search_query = f"{i} {locationnn}"
        top_urls = get_top_google_results(search_query, num_results=10)  # Fetch top Google results for the current description
        new_urls = compare(urls, top_urls)
        
        # Add each new URL to the set to avoid duplicates
        new_urls_set.update(new_urls)

    # Now, new_urls_set contains all unique URLs
    for new_urls in new_urls_set:

        
        

        random1.main(new_urls, 'random.csv')

    # Continue processing...
    for i in Description:
        grade = extract_grade(i)  # Extract the grade from the description
        Diameter = extract_diameter(i)  # Extract the diameter from the description

        output = display_data_saved2(Diameter, grade, stored_file_path)  
        output1 = display_data_jsw(locationnn, Diameter, grade, stored_file_path2)  # Get data from JSW
        output2 = display_data_saved2(Diameter, grade, 'indiamartt.csv')  

        if os.path.exists('random.csv'):
            output3 = display_data_saved2(Diameter, grade, 'random.csv')
        # Combine outputs
        if os.path.exists('random.csv'):
            combined_output = pd.concat([output1, output2, output, output3], axis=0, ignore_index=True)
        else:
            combined_output = pd.concat([output1, output2, output], axis=0, ignore_index=True)

        
        # Add Description as a column
        combined_output.insert(0, 'Description', i)

        # Select desired columns
        selected_columns = combined_output[['Description', 'Brand', 'Price', 'URL']]
        selected_columns['Price'] = selected_columns.apply(
            lambda row: clean_price(row['Price'], row['Description']), 
            axis=1
        )

        final_data.append(selected_columns)
    # Concatenate final output
    final_output = pd.concat(final_data, axis=0, ignore_index=True).drop_duplicates(ignore_index=True)
    if os.path.exists('random.csv'):
        os.remove('random.csv')    

    # Save to CSV in the user-provided directory
    final_output.to_csv(output_file_path, index=False, encoding='utf-8')

    print(f"Output file saved as: {output_file_path}")

if __name__ == "__main__":
    main()


