# db/quotes.py
import logging
from db.connection import get_db_connection
from decimal import Decimal

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_next_protocolo():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT MAX(protocolo) FROM quotes;")
                result = cur.fetchone()
                last_protocolo = result['max'] if result['max'] is not None else 0
                next_protocolo = last_protocolo + 1
                logger.debug(f"Último protocolo no banco: {last_protocolo}. Próximo protocolo: {next_protocolo}")
                return next_protocolo
    except Exception as e:
        logger.error(f"Erro ao obter o próximo protocolo: {str(e)}")
        raise

def inserir_quote(quote_data):
    """Insere uma nova cotação na tabela quotes e retorna o quote_id gerado."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Obter client_id usando cli_cnpj
                cur.execute("""
                    SELECT client_id FROM clients WHERE cnpj = %s;
                """, (quote_data['cli_cnpj'],))
                client = cur.fetchone()
                if not client:
                    raise Exception(f"Cliente com CNPJ {quote_data['cli_cnpj']} não encontrado.")
                client_id = client['client_id']

                # Obter origin_company_id usando comp_cnpj
                cur.execute("""
                    SELECT company_id FROM companies WHERE cnpj = %s;
                """, (quote_data['comp_cnpj'],))
                company = cur.fetchone()
                if not company:
                    raise Exception(f"Empresa com CNPJ {quote_data['comp_cnpj']} não encontrada.")
                company_id = company['company_id']

               # Verificar se o protocolo está presente
                protocolo = quote_data.get('protocolo')
                if protocolo is None:
                    raise Exception("Protocolo não definido no quote_data.")

                # Inserir cotação
                cur.execute("""
                    INSERT INTO quotes (
                        protocolo, origin_company_id, client_id, invoice_value,
                        total_weight, total_packages, total_volume
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING quote_id;
                """, (
                    protocolo,
                    company_id,
                    client_id,
                    quote_data['invoice_value'],
                    quote_data['total_weight'],
                    quote_data['total_packages'],
                    quote_data['volume_total']
                ))
                quote_id = cur.fetchone()['quote_id']
                conn.commit()
                logger.info(f"Cotação inserida com sucesso. ID: {quote_id}, Protocolo: {protocolo}")
                return quote_id
    except Exception as e:
        logger.error(f"Erro ao inserir cotação: {str(e)}")
        raise

def decimal_to_float(obj):
    """
    Recursively convert Decimal objects to float.
    """
    if isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj

def get_last_quotations(limit=15):
    """Recupera as últimas cotações realizadas."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT q.quote_id, q.protocolo, c.code, c.name, c.cnpj,
                           q.invoice_value, q.total_packages, q.total_volume, q.quote_date
                    FROM quotes q
                    JOIN clients c ON q.client_id = c.client_id
                    ORDER BY q.quote_date DESC
                    LIMIT %s;
                """, (limit,))
                result = cur.fetchall()
                logger.info(f"Recuperadas {len(result)} últimas cotações.")
                # Converter Decimal para float
                result = decimal_to_float(result)
                return result
    except Exception as e:
        logger.error(f"Erro ao recuperar últimas cotações: {str(e)}")
        raise

def filter_quotations(filters):
    """
    Filtra as cotações com base nos critérios fornecidos.
    filters: dict com possíveis chaves 'code', 'cnpj', 'name', 'date'
    """
    try:
        query = """
            SELECT q.quote_id, q.protocolo, c.code, c.name, c.cnpj,
                   q.invoice_value, q.total_packages, q.total_volume, q.quote_date
            FROM quotes q
            JOIN clients c ON q.client_id = c.client_id
            WHERE 1=1
        """
        params = []
        
        if 'code' in filters and filters['code']:
            query += " AND c.code = %s"
            params.append(filters['code'])
        
        if 'cnpj' in filters and filters['cnpj']:
            query += " AND c.cnpj = %s"
            params.append(filters['cnpj'])
        
        if 'name' in filters and filters['name']:
            query += " AND c.name ILIKE %s"
            params.append(f"%{filters['name']}%")
        
        if 'date' in filters and filters['date']:
            query += " AND DATE(q.quote_date) = %s"
            params.append(filters['date'])
        
        query += " ORDER BY q.quote_date DESC LIMIT 100;"  # Limitar a 100 resultados para performance
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                result = cur.fetchall()
                logger.info(f"Recuperadas {len(result)} cotações com os filtros aplicados.")
                # Converter Decimal para float
                result = decimal_to_float(result)
                return result
    except Exception as e:
        logger.error(f"Erro ao filtrar cotações: {str(e)}")
        raise

def get_quote_details(quote_id):
    """Recupera todos os detalhes de uma cotação específica."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Recuperar dados da cotação
                cur.execute("""
                    SELECT q.quote_id, q.protocolo, q.invoice_value, q.total_weight,
                           q.total_packages, q.total_volume, q.quote_date,
                           c.code, c.name, c.cnpj, c.city_name, c.state_abbreviation,
                           c.address, c.address_number, c.neighborhood, c.cep, c.ibge_city_code
                    FROM quotes q
                    JOIN clients c ON q.client_id = c.client_id
                    WHERE q.quote_id = %s;
                """, (quote_id,))
                quote = cur.fetchone()
                if not quote:
                    logger.error(f"Nenhuma cotação encontrada com ID {quote_id}.")
                    return None
                
                # Recuperar pacotes da cotação
                cur.execute("""
                    SELECT qp.amount_packages, qp.weight, qp.length, qp.height, qp.width
                    FROM quote_packages qp
                    WHERE qp.quote_id = %s;
                """, (quote_id,))
                packages = cur.fetchall()
                
                # Recuperar respostas das transportadoras, ordenando pelo shipping_value
                cur.execute("""
                    SELECT qr.response_id, qr.carrier_id, t.trade_name, qr.modal,
                           qr.shipping_value, qr.deadline_days, qr.quote_carrier, qr.message
                    FROM quote_responses qr
                    JOIN carriers t ON qr.carrier_id = t.carrier_id
                    WHERE qr.quote_id = %s
                    ORDER BY CASE 
                        WHEN qr.shipping_value IS NULL THEN 1
                        ELSE 0
                    END, qr.shipping_value ASC;
                """, (quote_id,))
                responses = cur.fetchall()
                
                # Calcular o total de shipping_value para calcular % do frete
                total_shipping = sum(float(resp["shipping_value"]) for resp in responses if resp["shipping_value"] is not None)
                
                # Evitar divisão por zero
                if total_shipping == 0:
                    total_shipping = 1.0
                
                # Estruturar os dados
                quote_details = {
                    "quote_id": quote["quote_id"],
                    "protocolo": quote["protocolo"],
                    "invoice_value": float(quote["invoice_value"]),
                    "total_weight": float(quote["total_weight"]),
                    "total_packages": quote["total_packages"],
                    "total_volume": float(quote["total_volume"]),
                    "quote_date": quote["quote_date"].strftime('%d/%m/%Y %H:%M:%S'),
                    "client": {
                        "code": quote["code"],
                        "name": quote["name"],
                        "cnpj": quote["cnpj"],
                        "city_name": quote["city_name"],
                        "state_abbreviation": quote["state_abbreviation"],
                        "address": quote["address"],
                        "address_number": quote["address_number"],
                        "neighborhood": quote["neighborhood"],
                        "cep": quote["cep"],
                        "ibge_city_code": quote["ibge_city_code"]
                    },
                    "packages": [
                        {
                            "AmountPackages": pkg["amount_packages"],
                            "Weight": float(pkg["weight"]),
                            "Length": float(pkg["length"]),
                            "Height": float(pkg["height"]),
                            "Width": float(pkg["width"]),
                            "volume_unitario": float(pkg["length"]) / 100 * float(pkg["height"]) / 100 * float(pkg["width"]) / 100
                        } for pkg in packages
                    ],
                    "responses": [
                        {
                            "response_id": resp["response_id"],
                            "carrier_id": resp["carrier_id"],
                            "carrier_trade_name": resp["trade_name"],
                            "modal": resp["modal"],
                            "shipping_value": float(resp["shipping_value"]) if resp["shipping_value"] else None,
                            "deadline_days": resp["deadline_days"],
                            "quote_carrier": resp["quote_carrier"],
                            "message": resp["message"],
                            "frete_percent": (float(resp["shipping_value"]) / total_shipping * 100) if resp["shipping_value"] else 0
                        } for resp in responses
                    ]
                }
                
                logger.info(f"Detalhes da cotação {quote_id} recuperados com sucesso.")
                return quote_details
    except Exception as e:
        logger.error(f"Erro ao obter detalhes da cotação {quote_id}: {str(e)}")
        raise