import requests
from bs4 import BeautifulSoup

def fetch_data(url):
    """
    Fetches the URL and extracts readable text from the HTML, 
    ignoring scripts, styles, and other non-content tags.
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script, style, and typically non-content elements
            for element in soup(['script', 'style', 'header', 'footer', 'nav', 'noscript']):
                element.decompose()
                
            # Get text
            text = soup.get_text(separator=' ')
            
            # Clean up empty lines and excess whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return clean_text
        else:
            print(f"Failed to retrieve data from {url}. Status code: {response.status_code}")
            return ""
    except Exception as e:
        print(f"Error fetching data from {url}: {e}")
        return ""

def fetch_multiple_urls(urls):
    """
    Fetches multiple URLs and concatenates the results.
    """
    combined_text = ""
    for url in set(urls):
        print(f"Scraping {url}...")
        text = fetch_data(url)
        if text:
            combined_text += f"\n\n--- Content from {url} ---\n\n{text}"
    return combined_text