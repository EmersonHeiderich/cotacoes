import requests
import time
import logging

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URLs para obtenção de tokens e cotações da RTE
URL_TOKEN_COTACAO = "https://quotation-apigateway.rte.com.br/token"
URL_TOKEN_BUSCA_CIDADE = "https://01wapi.rte.com.br/token"
URL_CITY_ID_BY_ZIP_CODE = "https://01wapi.rte.com.br/api/v1/busca-por-cep"
URL_COTACAO_RTE = "https://quotation-apigateway.rte.com.br/api/v1/gera-cotacao"

# Armazenamento dos tokens e tempos de expiração
token_cotacao = None
token_cotacao_expiration = 0
token_busca_cidade = None
token_busca_cidade_expiration = 0

def obter_token(url):
    """Obtém o token de acesso para a RTE."""
    payload = {
        "auth_type": "DEV",
        "grant_type": "password",
        "username": "INDUSTRIAKDU",
        "password": "F2BE4RH5"
    }
    headers = {"content-type": "application/x-www-form-urlencoded"}
    
    response = requests.post(url, data=payload, headers=headers)
    
    if response.status_code == 200:
        token_data = response.json()
        expiration_time = time.time() + int(token_data.get('expires_in', 3600)) - 60
        logger.debug(f"Token obtido com sucesso: {token_data}")
        return token_data.get('access_token'), expiration_time
    else:
        logger.error(f"Erro ao obter token: {response.status_code} {response.text}")
        raise Exception(f"Erro ao obter token: {response.text}")

def obter_token_cotacao():
    global token_cotacao, token_cotacao_expiration
    if token_cotacao is None or time.time() > token_cotacao_expiration:
        token_cotacao, token_cotacao_expiration = obter_token(URL_TOKEN_COTACAO)
        logger.debug(f"Token de cotação obtido: {token_cotacao}")
        logger.debug(f"Expiração do token de cotação: {time.ctime(token_cotacao_expiration)}")
    else:
        logger.debug(f"Reutilizando token de cotação: {token_cotacao}")
        logger.debug(f"Expiração do token de cotação: {time.ctime(token_cotacao_expiration)}")
    return token_cotacao

def obter_token_busca_cidade():
    global token_busca_cidade, token_busca_cidade_expiration
    if token_busca_cidade is None or time.time() > token_busca_cidade_expiration:
        token_busca_cidade, token_busca_cidade_expiration = obter_token(URL_TOKEN_BUSCA_CIDADE)
        logger.debug(f"Token de busca de cidade obtido: {token_busca_cidade}")
        logger.debug(f"Expiração do token de busca de cidade: {time.ctime(token_busca_cidade_expiration)}")
    else:
        logger.debug(f"Reutilizando token de busca de cidade: {token_busca_cidade}")
        logger.debug(f"Expiração do token de busca de cidade: {time.ctime(token_busca_cidade_expiration)}")
    return token_busca_cidade

def obter_city_id(zip_code):
    """Consulta o CityId correspondente ao CEP usando o token de acesso específico."""
    token_busca_cidade = obter_token_busca_cidade()
    url = f"{URL_CITY_ID_BY_ZIP_CODE}?zipCode={zip_code}"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {token_busca_cidade}"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and "Message" in data[0]:
            logger.error(f"Erro ao obter CityId: {data[0]['Message']}")
            raise Exception(data[0]['Message'])  # Lança exceção com apenas a mensagem da RTE
        logger.debug(f"CityId obtido com sucesso para o CEP {zip_code}: {data.get('CityId')}")
        return data.get('CityId')
    else:
        try:
            error_data = response.json()
            if isinstance(error_data, list) and "Message" in error_data[0]:
                logger.error(f"Erro ao obter CityId: {error_data[0]['Message']}")
                raise Exception(error_data[0]['Message'])  # Lança exceção com apenas a mensagem da RTE
        except (ValueError, KeyError):
            logger.error(f"Erro ao obter CityId: {response.status_code} {response.text}")
            raise Exception(f"Erro ao obter CityId: {response.text}")

def gera_cotacao_rte(dados):
    """Gera cotação com a transportadora RTE utilizando o token e os dados coletados."""
    try:
        destination_city_id = obter_city_id(dados['cli_cep'])
    except Exception as e:
        logger.error(f"Erro ao obter CityId para o CEP {dados['cli_cep']}: {str(e)}")
        return {
            "Transportadora": "RTE",
            "frete": None,
            "prazo": None,
            "cotacao": None,
            "message": f"{str(e)}"
        }

    try:
        token_cotacao = obter_token_cotacao()
    except Exception as e:
        logger.error(f"Erro ao obter token de cotação: {str(e)}")
        return {
            "Transportadora": "RTE",
            "frete": None,
            "prazo": None,
            "cotacao": None,
            "modal": "Rodoviário",
            "message": f"Erro ao obter token de cotação: {str(e)}"
        }

    packs_rte = [
        {
            "AmountPackages": pack['AmountPackages'],
            "Weight": pack['Weight'],
            "Length": int(pack['Length']),
            "Height": int(pack['Height']),
            "Width": int(pack['Width'])
        }
        for pack in dados['pack']
    ]

    payload = {
        "OriginZipCode": dados['comp_cep'],
        "OriginCityId": dados['comp_city_id'],
        "DestinationZipCode": dados['cli_cep'],
        "DestinationCityId": destination_city_id,
        "TotalWeight": dados['total_weight'],
        "EletronicInvoiceValue": dados['invoice_value'],
        "CustomerTaxIdRegistration": dados['comp_cnpj'],
        "ReceiverCpfcnp": dados['cli_cnpj'],
        "Packs": packs_rte,
        "ContactName": dados['comp_contact_name'],
        "ContactPhoneNumber": dados['comp_contact_phone'],
        "TotalPackages": dados['total_packages']
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/*+json",
        "Authorization": f"Bearer {token_cotacao}"
    }

    try:
        start_time = time.time()
        response = requests.post(URL_COTACAO_RTE, json=payload, headers=headers)
        response.raise_for_status()  # Levanta uma exceção para códigos de status HTTP 4xx/5xx
        elapsed_time = time.time() - start_time

        logger.info(f"Tempo de resposta da API RTE: {elapsed_time:.2f} segundos")
        logger.debug(f"Resposta completa da API RTE: {response.text}")

        data = response.json()
        if "Message" in data and data["Message"]:
            logger.error(f"Erro na resposta da RTE: {data['Message']}")
            return {
                "Transportadora": "RTE",
                "frete": None,
                "prazo": None,
                "cotacao": None,
                "modal": "Rodoviário",
                "message": data["Message"]
            }

        value = data.get('Value')
        delivery_time = data.get('DeliveryTime')
        protocol_number = data.get('ProtocolNumber')

        if value is not None and delivery_time is not None:
            logger.debug(f"Cotação gerada com sucesso: Valor {value}, Prazo {delivery_time} dias, Protocolo {protocol_number}")
            return {
                "Transportadora": "RTE",
                "frete": value,
                "prazo": delivery_time,
                "cotacao": protocol_number,
                "modal": "Rodoviário",
                "message": None
            }
        else:
            logger.error("Erro: Resposta da RTE não contém os campos esperados.")
            return {
                "Transportadora": "RTE",
                "frete": None,
                "prazo": None,
                "cotacao": None,
                "modal": "Rodoviário",
                "message": "Erro: Resposta da RTE não contém os campos esperados."
            }
    except requests.exceptions.HTTPError as http_err:
        try:
            error_data = response.json()
            error_message = error_data.get("Message", f"Erro HTTP {response.status_code}: {response.text}")
            logger.error(f"Erro HTTP ao gerar cotação: {error_message}")
            return {
                "Transportadora": "RTE",
                "frete": None,
                "prazo": None,
                "cotacao": None,
                "modal": "Rodoviário",
                "message": error_message
            }
        except ValueError:
            logger.error(f"Erro HTTP {response.status_code}: {http_err}")
            return {
                "Transportadora": "RTE",
                "frete": None,
                "prazo": None,
                "cotacao": None,
                "modal": "Rodoviário",
                "message": f"Erro HTTP {response.status_code}: {http_err}"
            }
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na solicitação ao servidor RTE: {str(e)}")
        return {
            "Transportadora": "RTE",
            "frete": None,
            "prazo": None,
            "cotacao": None,
            "modal": "Rodoviário",
            "message": f"Erro na solicitação ao servidor RTE: {str(e)}"
        }
    except ValueError:
        logger.error("Erro ao processar a resposta da RTE: Resposta não está no formato JSON esperado.")
        return {
            "Transportadora": "RTE",
            "frete": None,
            "prazo": None,
            "cotacao": None,
            "modal": "Rodoviário",
            "message": "Erro ao processar a resposta da RTE: Resposta não está no formato JSON esperado."
        }