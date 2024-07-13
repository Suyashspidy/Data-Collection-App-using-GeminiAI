import os
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# Configure Google Generative AI with API Key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-pro-latest")

# Function to get Gemini response
def get_gemini_response(question):
    response = model.generate_content(question)
    return response

# Function to create directory structure
def create_directories(stock_symbols, years, quarters):
    base_dir = './qReports'
    if not os.path.exists(base_dir):
        os.mkdir(base_dir)
    
    for symbol in stock_symbols:
        symbol_dir = os.path.join(base_dir, symbol)
        if not os.path.exists(symbol_dir):
            os.mkdir(symbol_dir)
        
        for year in years:
            year_dir = os.path.join(symbol_dir, str(year))
            if not os.path.exists(year_dir):
                os.mkdir(year_dir)
            
            for quarter in quarters:
                quarter_dir = os.path.join(year_dir, quarter)
                if not os.path.exists(quarter_dir):
                    os.mkdir(quarter_dir)

# Function to scrape quarterly PDF URLs from base URL
def scrape_quarterly_urls(base_url):
    response = requests.get(base_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    quarterly_urls = {}
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.endswith('.pdf') and any(q in href for q in ['Q1', 'Q2', 'Q3', 'Q4']):
            quarter = href.split('/')[-1].split('.')[0].split('_')[-1]
            quarterly_urls[quarter] = href
    
    return quarterly_urls

# Function to download reports
def download_reports(data, years, quarters):
    for _, row in data.iterrows():
        symbol = row['Stock Symbol']
        for year in years:
            try:
                base_url = row[str(year)]  # Access using str(year)
            except KeyError:
                st.write(f"Data for year {year} not found for company {symbol}. Skipping...")
                continue
            
            quarterly_urls = scrape_quarterly_urls(base_url)
            
            for quarter, url in quarterly_urls.items():
                file_path = f'./qReports/{symbol}/{year}/{quarter}/report.pdf'
                st.write(f"Accessing quarterly reports for {year} {quarter} and company {symbol}...")
                try:
                    response = requests.get(url)
                    response.raise_for_status()  # Ensure we raise an exception for bad responses
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    st.write("Download successful")
                except Exception as e:
                    st.write(f"Failed to download {url}: {e}")

# Streamlit app
st.title('Stock Report Downloader with Gemini AI and Web Scraping')

uploaded_file = st.file_uploader("Upload an XLSX file with stock symbols and base URLs for each year", type="xlsx")

if uploaded_file:
    data = pd.read_excel(uploaded_file)
    stock_symbols = data['Stock Symbol'].unique()
    years = range(2019, 2024)
    quarters = ['Q1', 'Q2', 'Q3', 'Q4']
    
    create_directories(stock_symbols, years, quarters)
    download_reports(data, years, quarters)
    
    st.success(f"{len(stock_symbols)} companies, {len(years)} years, {len(quarters)} quarterly reports collected and placed in the dataset.")
    
    # Use Gemini AI to generate a summary
    question = "Summarize the results of the stock report download process."
    summary = get_gemini_response(question)
    st.write("Gemini AI Summary:")
    st.write(summary)

# Example XLSX format:
# Stock Symbol,2019,2020,2021,2022,2023
# AAPL,https://example.com/reports/AAPL/2019.html,https://example.com/reports/AAPL/2020.html,https://example.com/reports/AAPL/2021.html,https://example.com/reports/AAPL/2022.html,https://example.com/reports/AAPL/2023.html
# MSFT,https://example.com/reports/MSFT/2019.html,https://example.com/reports/MSFT/2020.html,https://example.com/reports/MSFT/2021.html,https://example.com/reports/MSFT/2022.html,https://example.com/reports/MSFT/2023.html