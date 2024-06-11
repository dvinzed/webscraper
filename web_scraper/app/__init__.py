import os
from flask import Flask
from flask_pymongo import PyMongo
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

mongo = PyMongo()

def create_app():
    app = Flask(__name__)
    
    # Получение URI для MongoDB из переменной окружения
    app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb+srv://aklymenko872:RMGQaaq8qKGTI0ca@cluster0.giianli.mongodb.net/web_scraper_db")
    
    try:
        mongo.init_app(app)
        logger.debug("MongoDB connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
    
    from .routes import main
    app.register_blueprint(main)

    return app
