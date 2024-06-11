import requests
from bs4 import BeautifulSoup
from multiprocessing import Pool
import asyncio
import aiohttp

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://www.google.com',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Connection': 'keep-alive'
}

def fetch_content(url):
    with requests.Session() as session:
        response = session.get(url, headers=headers)
        response.raise_for_status()
        return response.text

def parse_content(html):
    soup = BeautifulSoup(html, 'html.parser')
    products = []

    for product in soup.find_all('div', class_='product-box'):
        book_name_element = product.find('h3', itemprop='name')
        book_name = book_name_element.text.strip() if book_name_element else 'N/A'

        book_url_element = product.find('a', class_='product-img')
        book_url = book_url_element['href'] if book_url_element else '#'

        image_element = product.find('img')
        image_url = image_element['src'] if image_element else 'N/A'

        author_element = product.find('div', class_='prod-author').find('a')
        author = author_element.text.strip() if author_element else 'N/A'

        price_element = product.find('div', class_='prod-price-standard')
        price_text = price_element.text.strip().replace('\xa0', ' ') if price_element else 'N/A'
        
        # Конвертация цены в числовой формат для корректной сортировки
        try:
            price = float(price_text.replace('zł', '').replace(',', '.'))
        except ValueError:
            price = 0.0

        products.append({
            'book_name': book_name,
            'book_url': book_url,
            'image_url': image_url,
            'author': author,
            'price': price,
            'price_text': price_text  # Оригинальный текст цены для отображения
        })
    
    return products
    

def scrape_data(url):
    html = fetch_content(url)
    data = parse_content(html)
    return data

async def async_fetch_content(url, session):
    async with session.get(url, headers=headers) as response:
        response.raise_for_status()
        return await response.text()

async def async_scrape_data(urls):
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = [async_fetch_content(url, session) for url in urls]
        html_contents = await asyncio.gather(*tasks)
        results = []
        for html in html_contents:
            results.extend(parse_content(html))
        return results

def multi_process_scrape(urls):
    with Pool() as pool:
        html_contents = pool.map(fetch_content, urls)
        results = []
        for html in html_contents:
            results.extend(parse_content(html))
        return results
