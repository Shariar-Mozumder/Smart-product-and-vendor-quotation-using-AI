import requests
from bs4 import BeautifulSoup

from urllib.parse import urljoin

from phi.agent import Agent
from phi.model.groq import Groq
from phi.tools.duckduckgo import DuckDuckGo
from phi.tools.googlesearch import GoogleSearch
from phi.model.huggingface import HuggingFaceChat
from phi.agent.duckdb import DuckDbAgent
from phi.model.ollama import Ollama
from pydantic import Field,BaseModel
from typing import List
from dotenv import load_dotenv
import json
import os
load_dotenv() 

Ollama_Model_Name=os.getenv("Ollama_Model_Name")
ollama_base_url=os.getenv("base_url")

def duckduckgo_search(query, num_results=5):
    """
    Search DuckDuckGo and return a list of full URLs.
    
    Args:
        query (str): Search query.
        num_results (int): Number of top results to return.
        
    Returns:
        list: List of complete URLs.
    """
    base_url = "https://duckduckgo.com/html/"
    params = {"q": query}
    headers = {"User-Agent": "Mozilla/5.0"}
    
    response = requests.get(base_url, params=params, headers=headers)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, "html.parser")
    links = []
    
    print(soup.prettify()[:1000])  # Print first 1000 characters of the HTML
    
    
    # Update the selector to find all result links
    for result in soup.find_all("a", href=True):
        # Filter and resolve relative links
        full_url = urljoin(base_url, result["href"])
        if full_url.startswith("http"):  # Ensure it's a valid link
            links.append(full_url)
        if len(links) >= num_results:
            break

    return links


    


class ProductQuotation(BaseModel):
    product: str = Field(description="Product Name")
    price: str = Field(description="Product Price")
    source: str= Field(description="Links of the source")
    features: str= Field(description="Given features of the product.")
    
def web_search(link):
    web_agent = Agent(
    name="Web Agent",
    # model=HuggingFaceChat(id="Qwen/Qwen2.5-3B-Instruct"),
    model = Ollama(
            id=Ollama_Model_Name,  # Replace with your model ID
            host=ollama_base_url,  # Replace with your Ollama server URL
            # timeout=30  # Optional: Set a timeout for requests
        ),
    tools=[DuckDuckGo()],
    description="You are a web-scraper specializing in fetching product prices and features from reliable e-commerce websites based on the given link.",
    instructions=[
        "You are a product price agent specializing in finding products and their prices from reliable e-commerce websites based on the given link.",
        "Always respond in JSON format.",
        "Ensure each product has the following fields: product (name), price, source (with hyperlink), and features.",
        "Price is mandatory; do not fetch or include products without prices. If the price is unknown or not available, ignore the products.",
        "Search for products only on trusted platforms such as Google Shopping, Amazon, Flipkart, Myntra, Meesho, Nike, and other reputable websites.",
        "Verify that each product is in stock and available for purchase.",
        "Do not include counterfeit or unverified products.",
        "Prioritize finding products that satisfy as many user requirements as possible, but ensure a minimum match of 50%.",
        "Clearly mention the key attributes of each product (e.g., price, brand, features) in the response.",
        "Format the response neatly in JSON format as shown in this example:",
        '''
        [
            {
                "product": "<string>",
                "price": "<string>",
                "source": "<string>",
                "features": "<string>"
            }
        ]
        '''
    ],
    # show_tool_calls=True,
    markdown=True,
    output_model=ProductQuotation,
    structured_outputs=True,
    parse_response=True
    )

    
    result=web_agent.run(link)
    return result.content

class VendorRanking(BaseModel):
    vendor_Name: str=Field(description="Name of the vendor")
    product: str=Field(description="Name of the product")
    price: str=Field(description="Price of the product")
    ranking: int=Field(description="Ranking position of the vendor")
    overall_score: float=Field(description="over all score given for the Ranking of the vendor out of 100")
    quality: float=Field(description="Quality score given out of 5 for the Ranking of the vendor")
    feature_score: float=Field(description="Feature score given out of 5 for the Ranking of the vendor")
    source: str=Field(description="Source of the product")

class VendorList(BaseModel):
    VendorRankingList: List[VendorRanking]

def data_analyst_agent(product_details):
    data_analyst_agent = Agent(
    # model=HuggingFaceChat(id="Qwen/Qwen2.5-3B-Instruct"),
    # model=Groq(id="llama3-8b-8192"),
    model = Ollama(
            id=Ollama_Model_Name,  # Replace with your model ID
            host=ollama_base_url,  # Replace with your Ollama server URL
            # timeout=30  # Optional: Set a timeout for requests
        ),
    description="You are a Research, Report and Analysis Agent Who can do price research, vendor ranking, market analysis and giving report list from the given product details list.",
    instructions=[
        "You are here to research, analysis and report the vendor ranking for market analysis",
        "You will be given a list of product quotes with vendor names, product names, prices, scores, sources, and features. You need to analyze the data and rank the vendors based on the quality, price, and features of the products they offer.",
        "Data you are given may or may not be structured, please adjust and keep the lists data of Vendor Name,Ranks, Product , Price, Score, source and features accordingly to product price, features and quality for every product.", 
        "Show me list of research data of vendor Rankings, use tool if needed. ",
        "Give the scores like over all and feature score on the basis of the quality, price and features of the product.",
        "Give the ranking list on the basis of the score, quality and feature score.",
        "If price is not available, ignore the product and make list for every product with price.",
        "Show me the result as a only in JSON list Format no title, no noting, I want to see it in JSON.",
        "Format the response neatly in list format as shown in this example:",
        '''
        "VendorRankingList":
            [
                {
                    "vendor_Name": "<string>",
                    "product": "<string>",
                    "price": "<string>",
                    "ranking": "<int>",
                    "overall_score": "<float>",
                    "quality": "<float>"
                    "feature_score": "<float>"
                    "source": "<string>",
                }
            ]
        '''
        ],
    # show_tool_calls=True,
    markdown=True,
    output_model=VendorList,
    structured_outputs=True,
    parse_response=True
    )
    # product_details = json.dumps(product_details, indent=4)
    
    result=data_analyst_agent.run(product_details)
    # Step 1: Replace '\n' with spaces
    # cleaned_text = result.content.replace("\\n", " ")
    return result.content


def fetch_product_data_from_html(html_content):
    """Uses an LLM to process pre-extracted product data."""
    web_agent = Agent(
        name="Web Agent",
        # model=Groq(id="llama3-8b-8192"),
        model=Ollama(id="qwen2.5:3b"),
        tools=[DuckDuckGo(), GoogleSearch()],
        description="You are a product price agent specializing in finding products and their prices from user-provided HTML content.",
        instructions=[
            "Extract and summarize product information including name, price, features, and shipping costs from provided structured data.",
            "Always include sources for each product if available.",
            "Respond in a clear and concise manner with proper formatting."
        ],
        show_tool_calls=True,
        markdown=True,
    )


    # Run the LLM agent with the context
    result = web_agent.run(f"Summarize the product information from the following html content:\n\n{html_content}")
    return result

structured_data=[
    {
        "product": "Lenovo Smart True Wireless Earbuds",
        "price": "$99.99",
        "source": "https://www.amazon.com/Lenovo-Smart-Wireless-Earbuds-Built/dp/B09LRJM42X",
        "features": "- Dynamically adjusts noise cancellation intensity in relation to your environment with smart adaptive noise cancelling, which can reduce up to 36 dB of ambient noise ... - Ljusmicker for AirPods Pro Case Cover with Cleaner Kit, Soft Silicone Protective Case for Apple AirPod Pro 2nd/1st Generation Case for Women Men ..."
    },
    {
        "product": "Lenovo True Wireless Earbuds Bluetooth 5.0 IPX5 Waterproof",
        "price": "$29.99",
        "source": "https://www.amazon.com/Lenovo-Wireless-Bluetooth-Waterproof-Microphone/dp/B08F9CDKPX",
        "features": "- USB Type-C Quick Charge: This Lenovo Wireless earphone gets 4 hours' playtime from a single charge (only 1 hour charge time), and 10 hours total with the charging case. - Bluetooth 5.0 Technology: It supports HSP, HFP, A2DP and AVRCP, providing in-call stereo sound and 2x faster transmission speed + more stable connect."
    }
]

def data_analyst_agent1(product_details):
    data_analyst_agent = DuckDbAgent(
        model=Groq(id="llama3-8b-8192"),
        description="You are a Research, Report and Analysis Agent Who can do price research, vendor ranking, market analysis and giving report from the given product details list.",
        instructions=[
            "You are here to research, analyze and report the Smart Quotations: price research, vendor ranking, market analysis.",
            "Data you are given may be unstructured; please adjust and keep the lists of product, price, source, and features.",
            "Show me a histogram/Tabular research data of Rankings.",
            "Choose an appropriate Reporting Template with proper and necessary data.",
            "Show me the result as a pretty diagram.",
        ],
        show_tool_calls=True,
        markdown=True,
    )

    # Convert product_details to a string
    product_details_str = "\n".join(
        [
            f"Product: {item['product']}, Price: {item['price']}, Source: {item['source']}, Features: {item['features']}"
            for item in product_details
        ]
    )

    result = data_analyst_agent.run(product_details_str)
    # Step 1: Replace '\n' with spaces
    cleaned_text = result.content.replace("\\n", " ")
    return cleaned_text
