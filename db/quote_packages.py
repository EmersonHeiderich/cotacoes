# db/quote_packages.py
import logging
from db.connection import get_db_connection

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def inserir_quote_packages(quote_id, packages):
    """Insere os pacotes associados a uma cotação na tabela quote_packages."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                for package in packages:
                    cur.execute("""
                        INSERT INTO quote_packages (
                            quote_id, amount_packages, weight, length, height, width
                        ) VALUES (%s, %s, %s, %s, %s, %s);
                    """, (
                        quote_id,
                        package['AmountPackages'],
                        package['Weight'],
                        package['Length'],
                        package['Height'],
                        package['Width']
                    ))
                conn.commit()
                logger.info(f"Pacotes inseridos para a cotação ID: {quote_id}")
    except Exception as e:
        logger.error(f"Erro ao inserir pacotes da cotação: {str(e)}")
        raise
