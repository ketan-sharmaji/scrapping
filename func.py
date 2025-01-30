from inputs import *
from load_file import *
from thefuzz import fuzz
import re
import pandas as pd
import re
import subprocess
from webdriver_manager.chrome import ChromeDriverManager


# to get from required file 
def extract_grade(description):
    pattern = r'(Fe-\d+)(D)?'
    match = re.search(pattern, description)
    if match:
        # Extract the first group (Fe-550) and, if present, the second group (D)
        grade = match.group(1)
        grade += match.group(2) if match.group(2) else ''
        return grade
    else:
        return None  
    
def extract_diameter(description):
    # Regular expression to capture the diameter followed by 'mm'
    pattern = r'(\d+mm)'
    # Search for the pattern in the description string
    match = re.search(pattern, description)
    if match:
        # Extract and return the diameter
        return match.group(1)
    else:
        return None  # Return None if no diameter is found
    

def normalize_diameter(diameter):
    
    # Convert to string and lowercase
    diameter = str(diameter).lower().strip()
    
    # Replace multiple spaces with single space
    diameter = re.sub(r'\s+', ' ', diameter)
    
    # If diameter is just a number without a unit, assume "mm" as the default unit
    if diameter.isdigit():
        diameter = f"{diameter} mm"
    
    # Remove space between number and unit only if it's not part of a range pattern or "mm & above"
    if not any(pattern in diameter for pattern in ['& above', 'and above']):
        diameter = re.sub(r'(\d+)\s*(mm|m)', r'\1\2', diameter)
    
    return diameter

def check_diameter(row_value, user_input):
    """
    Check if user input diameter matches the row value considering various formats
    including "X mm & above" conditions with flexible spacing.
    Handles cases like "6", "6 mm", "6-10 mm", "8 mm & above", etc.
    """
    # Normalize inputs while preserving important spaces
    user_input = normalize_diameter(user_input)
    row_value = normalize_diameter(row_value)
    
    # Handle empty user_input (if it's empty, return False)
    if not user_input:
        return False

    # Extract numeric value from user input
    try:
        user_num = float(re.sub(r'[^0-9.]', '', user_input))
    except ValueError:
        return False  # If user_input can't be converted to a number, return False
    
    # Handle special cases where row value contains "available" or "n/a"
    if any(x in row_value for x in ['available', 'n/a']):
        return True
        
    # Handle "mm & above" or similar patterns with flexible spacing
    above_pattern = re.search(r'(\d+)\s*(?:mm|m)?\s*(?:&|and)\s*above', row_value)
    if above_pattern:
        min_value = float(above_pattern.group(1))
        return user_num >= min_value
    
    # Handle ranges with hyphen (e.g., "8-32mm" or "8 - 32 mm")
    if '-' in row_value:
        try:
            range_nums = re.findall(r'\d+', row_value)
            if len(range_nums) >= 2:
                min_val = float(range_nums[0])
                max_val = float(range_nums[1])
                return min_val <= user_num <= max_val
        except ValueError:
            pass
    
    # Handle comma-separated values with flexible spacing
    values = row_value.split(',')
    for val in values:
        val = normalize_diameter(val.strip())
        try:
            # Extract numeric value for comparison
            val_num = float(re.sub(r'[^0-9.]', '', val))
            if val_num == user_num:
                return True
        except ValueError:
            continue
            
    return False

def grade_matching(name, game, df, grade):
    # Apply fuzzy matching to get matching grades for both name and game
    df.columns = df.columns.str.strip()
    df['Grade'] = df['Grade'].astype(str)
    val = []
    m = []


    # Extract numeric part from grade for comparison (without suffix)
    def extract_numeric_part(grade_str):
        # Use regex to extract the numeric part (e.g., 550 from Fe-550D or 550SD)
        match = re.search(r'(\d+)', grade_str)
        return match.group(1) if match else None
    # Loop through the 'Grade' column and compare with name and game
    for value in df['Grade']:
        score = fuzz.partial_ratio(name, value)
        if score >= 95:
            val.append(value)
        
        krok = fuzz.partial_ratio(game, value)
        if krok >= 95:
            m.append(value)
        
        dock = fuzz.partial_ratio(grade, value)
        if dock == 100:
            val.append(value)
        
        # Extract numeric part of the input grade and the value in the DataFrame
        grade_numeric = extract_numeric_part(grade)
        value_numeric = extract_numeric_part(value)

        # Compare numeric parts and allow suffix flexibility
        if grade_numeric and value_numeric:
            # If the numeric parts match, consider it a match
            if grade_numeric == value_numeric:
                val.append(value)
    
    # Remove duplicates by converting to a set and back to list
    matched_grades = list(set(val + m))

    return matched_grades

def normalize_location(location):
    # Normalize location by converting to lowercase, removing special characters and extra spaces
    location = location.lower().strip()  # Convert to lowercase and strip extra spaces
    location = re.sub(r'[^a-z0-9\s]', '', location)  # Remove non-alphanumeric characters except spaces
    return location



def location_matching(input_location, df, location_column='Location'):
    # Normalize the input location
    input_location = normalize_location(input_location)
    
    # Normalize the location values in the dataframe
    df[location_column] = df[location_column].apply(normalize_location)
    
    matched_locations = []
    
    # Loop through the dataframe's normalized location column and compare with input location
    for loc in df[location_column]:
        score = fuzz.partial_ratio(input_location, loc)
        if score >= 85:  # Threshold for fuzzy matching (can be adjusted)
            matched_locations.append(loc)
    
    # Return matched locations (without duplicates)
    return list(set(matched_locations))

# # Main function to display filtered data based on Location, Diameter, and Grade
def display_data_saved2( Diameter, Grade, stored_file_path):
    # Load data
    match = re.search(r'Fe[-]?(\d+)(d)?', Grade)
    if match:
        # Extract the numeric part (first capture group)
        grade_value = match.group(1)
        
        # Format the 'name' as 'Fe 500' or 'Fe 550'
        name = f"Fe {grade_value}"
        
        # Format the 'game' as 'FE 500' or 'FE 550'
        game = f"FE {grade_value}"

    
    # Read the stored file into a DataFrame
    df = pd.read_csv(stored_file_path)
    df.columns = df.columns.str.strip()  # Clean column names
    
    # Grade matching (assuming `grade_matching()` is defined elsewhere)
    k = grade_matching(name, game, df,Grade)

    # Normalize and clean the columns
    df['Diameter'] = df['Diameter'].astype(str)
    df['Grade'] = df['Grade'].astype(str)
    
    # Filter by Location and Grade
    filtered_df = df[
        (df['Diameter'].apply(lambda x: check_diameter(x, Diameter))) &  # Convert Diameter to float
        (df['Grade'].isin(k))  # Filter by Grade
    ]
    
    # Drop rows where 'Price' or 'Brand' columns are null (missing)
    filtered_df = filtered_df.dropna(subset=['Price','Brand'])
    
    return filtered_df



# Main function to display filtered data based on Location, Diameter, and Grade
def display_data_saved(Diameter, Grade,Location, stored_file_path):
    # Check if Grade is None or empty, if so assign default value
    if not Grade:
        Grade = 'Fe 500 and Fe 550'

    # Try to extract grade information from Grade
    match = re.search(r'Fe[-]?(\d+)(d)?', Grade)
    if match:
        # Extract the numeric part (first capture group)
        grade_value = match.group(1)
        
        # Format the 'name' as 'Fe 500' or 'Fe 550'
        name = f"Fe {grade_value}"
        
        # Format the 'game' as 'FE 500' or 'FE 550'
        game = f"FE {grade_value}"
    else:
        # If grade doesn't match the pattern, set default grade name and game
        name = "Fe 500 and Fe 550"
        game = "FE 500 and FE 550"

    # Read the stored file into a DataFrame
    df = pd.read_csv(stored_file_path)
    df.columns = df.columns.str.strip()  # Clean column names

    # Grade matching (assuming `grade_matching()` is defined elsewhere)
    k = grade_matching(name, game, df, Grade)

    # Normalize and clean the columns
    df['Diameter'] = df['Diameter'].astype(str)
    df['Grade'] = df['Grade'].astype(str)

    matched_locations = location_matching(Location, df, location_column='Location')

    
    # Filter by Location and Grade
    filtered_df = df[(
        df['Location'].isin(matched_locations)) &  # Filter by Location
        (df['Diameter'].apply(lambda x: check_diameter(x, Diameter))) &  # Filter by Diameter
        (df['Grade'].isin(k))  # Filter by Grade
    ]
    
    filtered_df = filtered_df.dropna(subset=['Price', 'Brand'])
    
    return filtered_df


def display_data_jsw(Location, Diameter, Grade, stored_file_path2):
    # Normalize the input Grade (convert to uppercase, remove hyphens and extra spaces)
    normalized_grade = str(Grade).upper().replace("-", " ").strip()

    # If the normalized grade is either "FE 550" or "FE 550D", proceed with matching
    if normalized_grade == "FE 550" or normalized_grade == "FE 550D":
        # Read the file
        df = pd.read_csv(stored_file_path2)
        df.columns = df.columns.str.strip()

        # Normalize the 'Diameter' column to ensure consistency (e.g., '8mm' becomes '8 mm')
        df['Diameter'] = df['Diameter'].astype(str).apply(lambda x: re.sub(r'(\d+)(mm|cm)', r'\1 \2', x).strip())

        # Normalize the 'Grade' column in the DataFrame
        df['Grade'] = df['Grade'].astype(str).apply(lambda x: x.upper().replace("-", " ").strip())  # Normalize Grade in df

        # Normalize the 'Location' column to remove extra spaces
        df['Location'] = df['Location'].str.strip()

        # Normalize the input 'Diameter' (e.g., '8mm' becomes '8 mm')
        normalized_diameter = re.sub(r'(\d+)(mm|cm)', r'\1 \2', str(Diameter)).strip()

        # Fuzzy matching for location
        val = []
        for value in df['Location']:
            score = fuzz.partial_ratio(Location, value)
            if score == 100:
                val.append(value)

        # Filter the DataFrame based on the location, diameter, and normalized grade
        filtered_df = df[
            (df['Location'].isin(val)) &  # Match Location
            (df['Diameter'] == normalized_diameter) &  # Match Diameter (after normalizing)
            (df['Grade'] == normalized_grade)  # Match Grade (after normalizing)
        ]

        
        return filtered_df
    
    return None  # Return None if the grade is not "FE 550" or "FE 550D"

