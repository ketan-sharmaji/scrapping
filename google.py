from googlesearch import search
from thefuzz import fuzz


# List to store URLs for comparison
urls = ["https://dir.indiamart.com","https://mccoymart.com/","https://www.jindalpanther.com","https://www.jswneosteel.in","https://www.klgecolite.in","https://www.buildersmart.in","https://www.mahadevironsteel.com","https://www.mahendrasteels.com",""]



# Function to get the top Google search results for a given query
def get_top_google_results(query, num_results=10):
    try:
        # Get the list of top URLs from Google search
        result_urls = list(search(query, num_results=num_results))
        return result_urls
    except Exception as e:
        print(f"Error during Google search: {e}")
        return []  # Return empty list if an error occurs


def compare(urls, top_urls, threshold=85):
    new = []  # List to store new URLs that do not match with any existing URL
    for url in top_urls:
        matched = False
        for existing_url in urls:
            score = fuzz.partial_ratio(url, existing_url)  # Compare URL using fuzzy partial ratio
            if score > threshold:  # If the score is above the threshold, consider it matched
                matched = True
                break
        if not matched:  # If no match was found, append the URL to the new list
            new.append(url)
    return new
