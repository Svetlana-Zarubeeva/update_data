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

mongo_login = os.getenv('MONGO_USERNAME')
mongo_password = os.getenv('MONGO_PASSWORD')
mongo_host = os.getenv('MONGO_HOST', 'localhost')
mongo_port = os.getenv('MONGO_PORT', '27017')

mongo_connection_url: str = os.getenv(
    'MONGO_CONNECTION_URL', f"mongodb://{mongo_login}:{mongo_password}@{mongo_host}:{mongo_port}"
)

mongo_serverSelectionTimeoutMS = 5000  # Макс. время на поиск доступного сервера в мс
mongo_socketTimeoutMS = 3600000  # Макс. время ожидания сетевой операции (чтение/запись) в мс
mongo_wtimeoutMS = 3600000  # Макс. время ожидания подтверждения записи (write concern) в мс

OKVED_DOWNLOAD_URL = "https://ofdata.ru/open-data/download/okved_2.json.zip"

OFDATA_API_URL = "https://api.ofdata.ru"
OFDATA_API_KEY = os.getenv("OFDATA_API_KEY")

DADATA_API_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party"
DADATA_API_KEY = os.getenv("DADATA_API_KEY")
DADATA_SECRET_KEY = os.getenv("DADATA_SECRET_KEY")

OFDATA_REGION = 61
OFDATA_API_TIMEOUT = 30
OFDATA_API_MAX_RETRIES = 3
OFDATA_API_RETRY_DELAY = 2
OFDATA_API_MAX_PAGE_SIZE = 100

storage_path = os.path.join(os.path.dirname(__file__), "storage")
os.makedirs(storage_path, exist_ok=True)

log_level = getattr(logging, os.getenv('LOG_LEVEL', 'INFO'))

POSTGRES_BATCH_SIZE = 20_000
MONGO_READ_BATCH_SIZE = 10_000
MONGO_WRITE_BATCH_SIZE = 1_000
MONGO_CURSOR_BATCH_SIZE = 1_000

founder_type_records = [
    {"type_code": "ФЛ", "type_name": "Физическое лицо"},
    {"type_code": "РосОрг", "type_name": "Российская организация"},
    {"type_code": "ИнОрг", "type_name": "Иностранная организация"},
    {"type_code": "ПИФ", "type_name": "Паевой инвестиционный фонд"},
    {"type_code": "РФ", "type_name": "Субъект РФ"}
]

OKVED_IT_CODES_TABLE = "okved_it_codes"
GOLD_LEGAL_ENTITIES_TABLE = "ofdata_legal_entities"
GOLD_ADDRESSES_TABLE = "ofdata_addresses"
GOLD_DIRECTORS_TABLE = "ofdata_directors"
GOLD_FOUNDERS_TABLE = "ofdata_founders"
GOLD_FOUNDER_TYPES_TABLE = "ofdata_founder_types"

OFDATA_BRONZE_DATABASE = "ofdata_bronze"
OFDATA_BRONZE_COLLECTION = "raw_data"
DADATA_BRONZE_DATABASE = "dadata_bronze"
DADATA_BRONZE_COLLECTION = "raw_data"

SILVER_SCHEMA = "silver"

SILVER_OFDATA_TABLE = "silver_ofdata_companies"
SILVER_DADATA_TABLE = "silver_dadata_companies"