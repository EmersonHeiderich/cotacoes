# db/quote_responses.py
import logging
from db.connection import get_db_connection

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_carrier_id(carrier_identifier):
    """Obtém o carrier_id pelo short_name."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Tenta obter o carrier_id pelo short_name
                cur.execute("""
                    SELECT carrier_id FROM carriers WHERE short_name = %s;
                """, (carrier_identifier,))
                carrier = cur.fetchone()
                if carrier:
                    return carrier['carrier_id']
                else:
                    # Log de erro caso não encontre a transportadora
                    logger.error(f"Transportadora com short_name '{carrier_identifier}' não encontrada.")
                    return None
    except Exception as e:
        logger.error(f"Erro ao obter carrier_id: {str(e)}")
        raise

def inserir_quote_response(quote_id, response_data):
    """Insere a resposta da cotação na tabela quote_responses."""
    try:
        carrier_identifier = response_data['Transportadora']
        carrier_id = get_carrier_id(carrier_identifier)
        if not carrier_id:
            logger.error(f"Transportadora '{carrier_identifier}' não encontrada no banco de dados. Resposta não será inserida.")
            return  # Não insere a resposta se a transportadora não for encontrada
        
        modal = response_data.get('modal', 'Rodoviário')  # Padrão 'Rodoviário' se não especificado
        shipping_value = response_data.get('frete')
        deadline_days = response_data.get('prazo')
        quote_carrier = response_data.get('cotacao')
        message = response_data.get('message')

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO quote_responses (
                        quote_id, carrier_id, modal, shipping_value, deadline_days,
                        quote_carrier, message
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s);
                """, (
                    quote_id,
                    carrier_id,
                    modal,
                    shipping_value if shipping_value is not None else 0,
                    deadline_days if deadline_days is not None else 0,
                    str(quote_carrier) if quote_carrier else '',
                    message
                ))
                conn.commit()
                logger.info(f"Resposta da transportadora '{carrier_identifier}' inserida para a cotação ID: {quote_id}")
    except Exception as e:
        logger.error(f"Erro ao inserir resposta da cotação: {str(e)}")
        raise
