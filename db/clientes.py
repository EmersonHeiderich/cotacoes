# /db/clientes.py
import logging
from db.connection import get_db_connection

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verificar_cliente_existente(cnpj, code):
    try:
        logger.info(f"Verificando se o cliente com CNPJ {cnpj} ou código {code} existe no banco de dados...")
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM clients WHERE cnpj = %s OR code = %s;
                """, (cnpj, str(code)))  # Convertendo code para string
                result = cur.fetchone()
                logger.debug(f"Resultado da verificação para CNPJ {cnpj} ou código {code}: {result}")
                return result
    except Exception as e:
        logger.error(f"Erro ao verificar cliente existente: {str(e)}")
        raise

def atualizar_cliente(cliente_dados):
    try:
        logger.info(f"Atualizando cliente com código {cliente_dados['code']} no banco de dados...")
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE clients SET
                        name = %s,
                        number_state_registration = %s,
                        city_name = %s,
                        state_abbreviation = %s,
                        cep = %s,
                        address = %s,
                        neighborhood = %s,
                        address_number = %s,
                        ibge_city_code = %s,
                        date_update = NOW()
                    WHERE code = %s;
                """, (
                    cliente_dados['name'],
                    cliente_dados['number_state_registration'],
                    cliente_dados['city_name'],
                    cliente_dados['state_abbreviation'],
                    cliente_dados['cep'],
                    cliente_dados['address'],
                    cliente_dados['neighborhood'],
                    cliente_dados['address_number'],
                    cliente_dados['ibge_city_code'],
                    str(cliente_dados['code'])  # Certifique-se de que o código é uma string
                ))
                conn.commit()
                logger.info(f"Cliente {cliente_dados['code']} atualizado com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao atualizar cliente: {str(e)}")
        raise

def inserir_cliente(cliente_dados):
    try:
        logger.info(f"Inserindo novo cliente com código {cliente_dados['code']} no banco de dados...")
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO clients (code, name, cnpj, number_state_registration, city_name, state_abbreviation, cep, address, neighborhood, address_number, ibge_city_code)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, (
                    cliente_dados['code'],
                    cliente_dados['name'],
                    cliente_dados['cnpj'],
                    cliente_dados['number_state_registration'],
                    cliente_dados['city_name'],
                    cliente_dados['state_abbreviation'],
                    cliente_dados['cep'],
                    cliente_dados['address'],
                    cliente_dados['neighborhood'],
                    cliente_dados['address_number'],
                    cliente_dados['ibge_city_code']
                ))
                conn.commit()
                logger.info(f"Cliente {cliente_dados['code']} inserido com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao inserir cliente: {str(e)}")
        raise
