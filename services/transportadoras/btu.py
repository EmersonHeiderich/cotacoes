import requests
import base64
import time
import logging

# Configuração do logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_auth_header(username, password):
    """Gera o cabeçalho de autenticação básica codificado em Base64."""
    auth_str = f"{username}:{password}"
    auth_encoded = base64.b64encode(auth_str.encode()).decode()
    return {
        'Authorization': f'Basic {auth_encoded}',
        'Content-Type': 'application/json;charset=UTF-8',
        'Accept': '*/*',
        'User-Agent': 'PostmanRuntime/7.41.2',
        'Connection': 'keep-alive'
    }

def build_payload(dados, modal):
    """Constrói o payload da requisição com base nos dados fornecidos e no modal."""
    return {
        "cnpjRemetente": dados['comp_cnpj'],
        "cnpjDestinatario": dados['cli_cnpj'],
        "modal": modal,
        "tipoFrete": "1",
        "cepOrigem": dados['comp_cep'],
        "cepDestino": dados['cli_cep'],
        "vlrMercadoria": dados['invoice_value'],
        "peso": dados['total_weight'],
        "volumes": dados['total_packages'],
        "cubagem": [
            {
                "altura": pack['Height'] / 100,  # Converte em metros
                "largura": pack['Width'] / 100,  # Converte em metros
                "comprimento": pack['Length'] / 100,  # Converte em metros
                "volumes": pack['AmountPackages']
            } for pack in dados['pack']  # Itera sobre todos os pacotes
        ]
    }

def gera_cotacao_braspress(dados, modal):
    """Gera cotação com a Braspress utilizando os dados coletados e o modal especificado."""
    url = "https://api.braspress.com/v1/cotacao/calcular/json"
    username = "10424098000168_PRD"
    password = "XA3r26Wg3S3U3bqF"

    # Obter o cabeçalho de autenticação
    headers = get_auth_header(username, password)

    # Construir o payload da requisição com o modal especificado
    payload = build_payload(dados, modal)

    # Log do payload completo da requisição
    logger.debug(f"Payload da requisição Braspress (Modal: {modal}): {payload}")

    try:
        # Captura o tempo antes da requisição
        start_time = time.time()

        # Enviar a requisição POST para a API da Braspress
        response = requests.post(url, json=payload, headers=headers)
        elapsed_time = time.time() - start_time

        # Log do tempo de resposta
        logger.info(f"Tempo de resposta da API Braspress (Modal: {modal}): {elapsed_time:.2f} segundos")

        # Verifica se houve erro na resposta
        if response.status_code != 200:
            try:
                # Tenta extrair a mensagem de erro da resposta JSON
                error_data = response.json()
                error_message = error_data.get("message", "Erro desconhecido")
                error_list = error_data.get("errorList", [])
                detailed_error = "; ".join(error_list) if error_list else "Sem detalhes adicionais"
                full_message = f"{error_message}: {detailed_error}"
            except ValueError:
                # Se a resposta não for JSON, apenas registra o erro genérico
                full_message = f"{response.status_code} {response.reason}"
            
            logger.error(f"Erro na resposta da API Braspress (Modal: {modal}): {full_message}")
            return {
                "Transportadora": "BTU",
                "frete": None,
                "prazo": None,
                "cotacao": None,
                "modal": "Rodoviário" if modal == "R" else "Aéreo",
                "message": full_message
            }

        # Log da resposta completa
        logger.debug(f"Resposta completa da API Braspress (Modal: {modal}): {response.text}")

        # Analisar a resposta JSON e retornar os valores relevantes
        data = response.json()
        return {
            "Transportadora": "BTU",
            "frete": data.get('totalFrete'),
            "prazo": data.get('prazo'),
            "cotacao": data.get('id'),
            "modal": "Rodoviário" if modal == "R" else "Aéreo",
            "message": None
        }

    except requests.exceptions.RequestException as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Erro ao gerar cotação Braspress (Modal: {modal}): {e}")
        logger.error(f"Tempo até o erro: {elapsed_time:.2f} segundos")
        return {
            "Transportadora": "BTU",
            "frete": None,
            "prazo": None,
            "cotacao": None,
            "modal": "Rodoviário" if modal == "R" else "Aéreo",
            "message": str(e)
        }