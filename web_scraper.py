# Import required libraries for web scraping, file handling, and delays
import requests
from bs4 import BeautifulSoup
import json
import csv
import time
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

# This class handles all scraping operations such as fetching pages,
# extracting headlines, filtering results, and saving data

class HeadlineScraper:
    def __init__(self):
        # Set request headers and create an empty list to store results
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        self.results = []
# Check whether scraping is allowed according to the website's robots.txt file
    def is_allowed_by_robots(self, url):
        try:
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            return rp.can_fetch("*", url)
        except Exception:
            return True
# Send request to the website and return page HTML content
    def fetch_page(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
# Extract headlines, links, and time information from heading tags
    def extract_headlines_generic(self, html, base_url):
        soup = BeautifulSoup(html, "html.parser")
        headlines = []

        for tag in soup.find_all(["h1", "h2", "h3"]):
            title = tag.get_text(strip=True)

            if not title or len(title) < 8:
                continue

            link_tag = tag.find("a")
            if not link_tag:
                parent_link = tag.find_parent("a")
                link_tag = parent_link

            if link_tag and link_tag.get("href"):
                full_url = urljoin(base_url, link_tag["href"])
            else:
                full_url = base_url

            time_value = "Not Available"

            time_tag = tag.find_next("time")
            if time_tag:
                if time_tag.get("datetime"):
                    time_value = time_tag["datetime"]
                else:
                    time_value = time_tag.get_text(strip=True)

            headlines.append({
                "title": title,
                "url": full_url,
                "time": time_value,
                "source": base_url
            })

        unique_headlines = []
        seen = set()

        for item in headlines:
            key = (item["title"], item["url"])
            if key not in seen:
                seen.add(key)
                unique_headlines.append(item)

        return unique_headlines
# Filter headlines based on user-entered keyword
    def filter_by_keyword(self, headlines, keyword):
        if not keyword:
            return headlines

        keyword = keyword.lower()
        filtered = []

        for item in headlines:
            if keyword in item["title"].lower():
                filtered.append(item)

        return filtered
# Scrape a single website after checking robots.txt and adding delay
    def scrape_site(self, url, keyword=None, delay=2):
        print(f"\nChecking robots.txt for {url}...")

        if not self.is_allowed_by_robots(url):
            print(f"Scraping not allowed by robots.txt: {url}")
            return []

        print(f"Fetching headlines from {url}...")
        html = self.fetch_page(url)

        if not html:
            return []

        headlines = self.extract_headlines_generic(html, url)
        headlines = self.filter_by_keyword(headlines, keyword)

        print(f"Found {len(headlines)} headlines from {url}")
        time.sleep(delay)

        return headlines
# Scrape multiple websites one by one and combine all results
    def scrape_multiple_sites(self, urls, keyword=None, delay=2):
        self.results = []

        for url in urls:
            site_headlines = self.scrape_site(url, keyword=keyword, delay=delay)
            self.results.extend(site_headlines)

        return self.results
# Display all scraped headlines in a readable format
    def display_headlines(self):
        if not self.results:
            print("\nNo headlines found.")
            return

        print("\nScraped Headlines:\n")
        for index, item in enumerate(self.results, start=1):
            print(f"{index}. Title : {item['title']}")
            print(f"   URL   : {item['url']}")
            print(f"   Time  : {item['time']}")
            print(f"   Source: {item['source']}")
            print("-" * 70)
# Save results to a JSON file
    def save_to_json(self, filename="headlines.json"):
        try:
            with open(filename, "w", encoding="utf-8") as file:
                json.dump(self.results, file, indent=4, ensure_ascii=False)
            print(f"\nResults saved to {filename}")
        except Exception as e:
            print(f"Error saving JSON file: {e}")
# Save results to a CSV file
    def save_to_csv(self, filename="headlines.csv"):
        try:
            with open(filename, "w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=["title", "url", "time", "source"])
                writer.writeheader()
                writer.writerows(self.results)
            print(f"\nResults saved to {filename}")
        except Exception as e:
            print(f"Error saving CSV file: {e}")

# Main function to take input from user and run the scraper
def main():
    scraper = HeadlineScraper()

    print("Web Scraper for Headlines")
    print("-" * 30)

    num_sites_input = input("How many websites do you want to scrape? ").strip()

    if not num_sites_input.isdigit() or int(num_sites_input) <= 0:
        print("Invalid number of websites.")
        return

    num_sites = int(num_sites_input)
    urls = []

    for i in range(num_sites):
        url = input(f"Enter website URL {i + 1}: ").strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        urls.append(url)

    keyword = input("Enter keyword to filter headlines (or press Enter to skip): ").strip()
    delay_input = input("Enter delay between requests in seconds (default 2): ").strip()

    if delay_input.isdigit():
        delay = int(delay_input)
    else:
        delay = 2

    scraper.scrape_multiple_sites(urls, keyword=keyword if keyword else None, delay=delay)
    scraper.display_headlines()

    if scraper.results:
        save_choice = input("\nDo you want to save results? (yes/no): ").strip().lower()

        if save_choice == "yes":
            format_choice = input("Save as JSON or CSV? ").strip().lower()

            if format_choice == "json":
                scraper.save_to_json()
            elif format_choice == "csv":
                scraper.save_to_csv()
            else:
                print("Invalid format choice.")

# Start the program only when this file is run directly
if __name__ == "__main__":
    main()