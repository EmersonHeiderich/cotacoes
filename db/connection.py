# /db/connection.py
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    try:
        connection = psycopg2.connect(
            host="10.1.1.15",
            port="5432",
            database="cotacoes",
            user="postgres",
            password="20Kdu21@@ti",
            cursor_factory=RealDictCursor,
            options="-c client_encoding=UTF8"
        )
        return connection
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco de dados: {str(e)}")
        raise
