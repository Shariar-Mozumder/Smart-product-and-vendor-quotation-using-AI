# from phi.app import App
from phi.agent import Agent
# from phi.task import Task
from requests import get
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
from dotenv import load_dotenv
import os
# from test_selenium import fetch_dynamic_content

# Define the Phidata App
# app = App(name="smart_quotation_app", description="Smart Quotation using Phidata agents")


    # location: str
# Define Agents
load_dotenv()

Ollama_Model_Name=os.getenv("Ollama_Model_Name")
base_url=os.getenv("base_url")
class SearchAgent(Agent):
    def run(self, query: str, num_results=10):
        """Search for product links on DuckDuckGo."""
        print(f"SearchAgent: Searching for '{query}'")
        base_url = "https://duckduckgo.com/html/"
        headers = {"User-Agent": "Mozilla/5.0"}
        params = {"q": query}
        links = []
        trusted_domains = [
            "amazon",
            "ebay",
            "flipkart",
            "alibaba",
            "aliexpress",
            "etsy",
            "ozon",
            "rakuten",
            "samsung",
            "walmart",
            "cisco",
            "wildberries",
            "shopify",
            "nike",
            "apple",
            "asos",
            
        ]

        response = get(base_url, params=params, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        for a in soup.find_all("a", href=True, class_="result__a"):
            full_url = urljoin(base_url, a["href"])
            # if any(domain in full_url for domain in trusted_domains):
            links.append(full_url)
            if len(links) >= num_results:
                break

        print(f"SearchAgent: Found {len(links)} links")
        return links


from app.agents import web_search,data_analyst_agent
class ScraperAgent:
    def run(self, links: list):
        product_details=[]

        for link in links:
            try:
                print(f"Scraping: {link}")
                # html_content = fetch_dynamic_content(link)
                # soup = BeautifulSoup(html_content, "html.parser")


                results=web_search(link)
                product_details.append(results)
               

            except Exception as e:
                print(f"ScraperAgent: Error scraping {link}: {e}")

        # print(f"ScraperAgent: Scraped prices for {len(prices)} links")
        return product_details

    def parse_amazon_price(self, soup):
        """Parse price from Amazon HTML."""
        try:
            price_div = soup.find(id="desktop_unifiedPrice") or soup.find(id="unifiedPrice_feature_div")
            if price_div:
                price_text = price_div.get_text(strip=True)
                return re.search(r"₹\d[\d,]*(\.\d+)?|\$\d[\d,]*(\.\d+)?", price_text).group()
        except Exception as e:
            print(f"Error parsing Amazon price: {e}")
        return None

    def parse_ebay_price(self, soup):
        """Parse price from eBay HTML."""
        try:
            price_div = soup.find("div", class_="x-price-primary")
            shipping_div = soup.find("div", class_="x-shipping-cost")
            if price_div:
                price = price_div.get_text(strip=True)
                shipping = shipping_div.get_text(strip=True) if shipping_div else ""
                return f"{price} {shipping}".strip()
        except Exception as e:
            print(f"Error parsing eBay price: {e}")
        return None

    def parse_flipkart_price(self, soup):
        """Parse price from Flipkart HTML."""
        try:
            price_div = soup.find("div", class_="Nx9bqj")
            discount_div = soup.find("div", class_="UkUFwK")
            if price_div:
                price = price_div.get_text(strip=True)
                discount = discount_div.get_text(strip=True) if discount_div else ""
                return f"{price} {discount}".strip()
        except Exception as e:
            print(f"Error parsing Flipkart price: {e}")
        return None
    
    
# class WebSearchAgent:
#     def __init__(self):
#         self.extractor = PhiDataExtractor()  # Assuming PhiData provides an extractor class

#     def run(self, links: list):
#         """Extract prices and details using PhiData."""
#         print("WebSearchAgent: Extracting prices...")
#         results = {}

#         for link in links:
#             try:
#                 print(f"Processing: {link}")
#                 # Use PhiData to extract structured information
#                 data = self.extractor.extract(link)
#                 if data:
#                     results[link] = {
#                         "price": data.get("price"),
#                         "shipping": data.get("shipping"),
#                         "discount": data.get("discount"),
#                     }
#                 else:
#                     print(f"No data found for {link}")
#             except Exception as e:
#                 print(f"WebSearchAgent: Error processing {link}: {e}")

#         print(f"WebSearchAgent: Extracted data for {len(results)} links")
#         return results

class AnalysisAgent(Agent):
    def run(self, prices: dict):
        """Analyze market data and rank vendors."""
        print("AnalysisAgent: Analyzing market data...")
        parsed_prices = {}
        for link, price in prices.items():
            try:
                numeric_price = float(re.sub(r"[^\d.]", "", price))
                parsed_prices[link] = numeric_price
            except ValueError:
                continue

        # Sort prices
        sorted_prices = sorted(parsed_prices.items(), key=lambda x: x[1])
        print("AnalysisAgent: Analysis complete")
        return sorted_prices


class ReportAgent(Agent):
    def run(self, product_details):
        """Generate a detailed report using a free LLM."""
        from transformers import pipeline

        # Use a free LLM like Mistral or LLaMA
        print("ReportAgent: Generating report...")
        report=data_analyst_agent(product_details)
        # summarizer = pipeline("text-generation", model="mistralai/Mistral-Instruct-v1-7B")

        # context = f"Product: {product_name}\n\nVendor Prices:\n"
        # for link, price in sorted_prices:
        #     context += f"{price} - {link}\n"

        # context += "\nProvide a detailed analysis of the above data."
        # report = summarizer(context, max_length=300)[0]["generated_text"]

        # print("ReportAgent: Report generated")
        return report


# Main Agent to orchestrate tasks
class SmartQuotationAgent(Agent):
    def run(self, product_name: str):
        """Orchestrate all tasks to produce the smart quotation."""
        print("SmartQuotationAgent: Starting the workflow...")

        # Step 1: Search for product links
        search_agent = SearchAgent()
        links = search_agent.run(product_name)

        if not links:
            return "No product links found."

        # Step 2: Scrape prices
        scraper_agent = ScraperAgent()
        product_details = scraper_agent.run(links)

        if not product_details:
            return "No Product details found."
        print(product_details)

        # Step 3: Analyze market data
        # analysis_agent = AnalysisAgent()
        # sorted_prices = analysis_agent.run(product_details)

        # Step 4: Generate the report
        report_agent = ReportAgent()
        report = report_agent.run(str(product_details))
        output={
            "Links":links,
            "Product_Details":product_details,
            "Vendor Report":report
        }
        return output


# Register the main agent with the app
# app.add_agent(SmartQuotationAgent(name="smart_quotation"))


