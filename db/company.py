# db/company.py
import logging
from db.connection import get_db_connection

# Configuração do logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_company_by_code(code):
    """
    Busca as informações da empresa no banco de dados usando o código fornecido.
    Por padrão, busca a empresa com código '100000011'.
    """
    try:
        logger.info(f"Buscando informações da empresa com código {code} no banco de dados...")
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Log para verificar se o código está sendo passado corretamente
                logger.debug(f"Executando consulta com o código: {code}")
                
                consulta_sql = """
                    SELECT company_id, code, name, cnpj, number_state_registration, city_name, state_abbreviation, cep, address, neighborhood, address_number, ibge_city_code
                    FROM companies
                    WHERE code = %s;
                """
                cur.execute(consulta_sql, (code,))
                company_data = cur.fetchone()

                # Verificações de depuração
                if company_data is None:
                    logger.error(f"Nenhuma empresa encontrada com o código {code}.")
                    return None

                logger.debug(f"Resultado da consulta: {company_data}")

                return {
                    "company_id": company_data["company_id"],
                    "code": company_data["code"],
                    "name": company_data["name"],
                    "cnpj": company_data["cnpj"],
                    "number_state_registration": company_data["number_state_registration"],
                    "city_name": company_data["city_name"],
                    "state_abbreviation": company_data["state_abbreviation"],
                    "cep": company_data["cep"],
                    "address": company_data["address"],
                    "neighborhood": company_data["neighborhood"],
                    "address_number": company_data["address_number"],
                    "ibge_city_code": company_data["ibge_city_code"]
                }
    except Exception as e:
        logger.error(f"Erro ao buscar informações da empresa: {str(e)}")
        raise