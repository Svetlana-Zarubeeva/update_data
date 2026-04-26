"""!
@brief Модуль с настройками сервиса
"""

import os
import logging
from dotenv import load_dotenv
from enum import Enum
from urllib.parse import quote_plus

load_dotenv()


class Database(str, Enum):
    data = "data"


db_database_data = os.getenv('DB_DATABASE')
db_user_data = os.getenv('DB_USERNAME')
db_password_data = os.getenv('DB_PASSWORD')
db_port_data = int(os.getenv('DB_PORT', '5432'))
db_host_data = os.getenv('DB_HOST', 'postgres')

db_conf_data = {
    'dbname': db_database_data,
    'user': db_user_data,
    'port': db_port_data,
    'password': db_password_data,
    'host': db_host_data
}

DATABASE_TO_CONF = {
    Database.data: db_conf_data,
}

db_url = f"postgresql+psycopg2://{db_conf_data['user']}:{quote_plus(db_conf_data['password'])}@{db_conf_data['host']}:{db_conf_data['port']}/{db_conf_data['dbname']}"

OKVED_DOWNLOAD_URL = "https://rosstat.gov.ru/storage/mediabank/OKPD2.rar"

storage_path = os.path.join(os.path.dirname(__file__), "storage")
os.makedirs(storage_path, exist_ok=True)

log_level = getattr(logging, os.getenv('LOG_LEVEL', 'INFO'))

POSTGRES_BATCH_SIZE = 20_000

OKVED_IT_CODES_TABLE = "okved_it_codes"