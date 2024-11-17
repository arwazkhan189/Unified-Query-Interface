# config.py
class Config:
    # MySQL Configuration
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_PORT = 3306  # Default MySQL port

    # MongoDB Configuration
    MONGO_URI = 'mongodb://localhost:27017/test'  # Replace with your Mongo URI

    # Flask Configuration
    SECRET_KEY = 'your_secret_key'  # Change to a secret key
    DEBUG = True