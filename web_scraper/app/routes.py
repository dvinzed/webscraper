import logging
import asyncio
from flask import Blueprint, render_template, request, jsonify
from bson import ObjectId
from .scraper import scrape_data, async_scrape_data
from . import mongo

main = Blueprint('main', __name__)

# Конфигурация логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@main.route('/')
def index():
    return render_template('index.html')

def convert_object_ids(data):
    if isinstance(data, list):
        return [convert_object_ids(item) for item in data]
    elif isinstance(data, dict):
        return {key: convert_object_ids(value) for key, value in data.items()}
    elif isinstance(data, ObjectId):
        return str(data)
    else:
        return data

@main.route('/scrape', methods=['POST'])
def scrape():
    try:
        urls = request.json.get('urls', [])
        sort_by = request.json.get('sort_by', 'book_name')
        sort_order = request.json.get('sort_order', 'asc')
        filter_by = request.json.get('filter_by', '').strip().lower()

        logger.debug(f"Scraping URLs: {urls}")
        data = asyncio.run(async_scrape_data(urls))
        logger.debug(f"Scraped Data: {data}")

        if not data or not any(data):  # Проверка, пусты ли данные
            return jsonify({'status': 'error', 'message': 'No data scraped'}), 400

        # Фильтрация данных
        if filter_by:
            data = [item for item in data if filter_by in item['book_name'].lower() or filter_by in item['author'].lower()]

        # Проверка формата данных перед вставкой
        if not isinstance(data, list):
            logger.error("Data is not a list")
            return jsonify({'status': 'error', 'message': 'Data format is incorrect'}), 400

        # Вставка данных в MongoDB
        try:
            inserted_ids = []
            for item in data:
                if not mongo.db.web_scraper_db.find_one({'book_name': item['book_name']}):
                    result = mongo.db.web_scraper_db.insert_one(item)
                    inserted_ids.append(str(result.inserted_id))
            logger.debug(f"Inserted IDs: {inserted_ids}")
        except Exception as e:
            logger.error(f"Failed to insert data into MongoDB: {e}")
            return jsonify({'status': 'error', 'message': 'Failed to insert data into MongoDB'}), 500

        # Сортировка данных
        if sort_by in ['book_name', 'author', 'price']:
            reverse = (sort_order == 'desc')
            data.sort(key=lambda x: x[sort_by], reverse=reverse)

        # Конвертируем данные и вставленные ID для JSON-ответа
        formatted_data = convert_object_ids(data)

        return jsonify({'status': 'success', 'data': formatted_data, 'inserted_ids': inserted_ids})
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
