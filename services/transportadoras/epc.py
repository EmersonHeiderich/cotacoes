# services/transportadoras/epc.py

import requests
from datetime import datetime
import time
import logging

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constantes
URL_EPC = "https://3kusfy-prd-protheus.totvscloud.com.br:11586/rest_prd/TMSWS001"
AUTH_EPC = ("10424098", "#epc10424098")
FATOR_CUBAGEM_EPC = 250  # Fator de cubagem (kg/m³)

def construir_payload_epc(dados):
    """Constrói o payload para a requisição de cotação da Princesa dos Campos."""
    peso_cubado_total = 0
    for pack in dados['pack']:
        comprimento_cm = pack['Length']
        altura_cm = pack['Height']
        largura_cm = pack['Width']

        # Calcula o volume em metros cúbicos
        volume_m3 = (comprimento_cm * altura_cm * largura_cm) / 1_000_000  # Convertendo cm³ para m³
        peso_cubado = volume_m3 * FATOR_CUBAGEM_EPC  # Calcula o peso cubado
        peso_cubado_total += peso_cubado * pack['AmountPackages']  # Acumula o peso cubado para todos os pacotes

    # Arredonda o peso cubado total para 4 casas decimais, se necessário
    peso_cubado_total = round(peso_cubado_total, 4)

    return {
        "cnpjPagador": dados['comp_cnpj'],  # Valor fixo
        "cepOrigem": dados['comp_cep'],  # Valor fixo
        "cnpjDestinatario": dados['cli_cnpj'],
        "cepDestino": dados['cli_cep'],
        "embalagem": "CX",  # Valor fixo
        "valorNF": dados['invoice_value'],
        "quantidade": dados['total_packages'],
        "peso": dados['total_weight'],  # Enviando o peso real
        "volume": peso_cubado_total  # Enviando o peso cubado como volume
    }

def solicitar_cotacao_epc(payload):
    """Envia a solicitação de cotação e retorna a resposta."""
    start_time = time.time()  # Captura o tempo antes da requisição
    try:
        response = requests.post(URL_EPC, json=payload, auth=AUTH_EPC, timeout=25)
        elapsed_time = time.time() - start_time  # Calcula o tempo decorrido após a resposta
        logger.info(f"Tempo de resposta da API EPC: {elapsed_time:.2f} segundos")

        if response.status_code != 200:
            logger.error(f"Erro ao gerar cotação Princesa dos Campos: {response.status_code} {response.reason}")
            logger.error(f"Detalhes do erro: {response.text}")  # Adiciona detalhes do erro
            try:
                error_data = response.json()
                return {
                    "Transportadora": "EPC",
                    "frete": None,
                    "prazo": None,
                    "cotacao": None,
                    "modal": "Rodoviário",
                    "message": error_data.get('erro', f"Erro desconhecido: {response.status_code}")
                }
            except ValueError:
                return {
                    "Transportadora": "EPC",
                    "frete": None,
                    "prazo": None,
                    "cotacao": None,
                    "modal": "Rodoviário",
                    "message": f"Erro desconhecido: {response.status_code}"
                }

        logger.debug(f"Resposta da API Princesa dos Campos: {response.text}")

        return response.json()
    except requests.exceptions.Timeout:
        elapsed_time = time.time() - start_time
        logger.error(f"Erro: Timeout de 25 segundos atingido.")
        logger.error(f"Tempo até o erro: {elapsed_time:.2f} segundos")
        return {
            "Transportadora": "EPC",
            "frete": None,
            "prazo": None,
            "cotacao": None,
            "modal": "Rodoviário",
            "message": "Timeout de 25 segundos atingido"
        }
    except requests.exceptions.RequestException as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Erro ao gerar cotação Princesa dos Campos: {e}")
        logger.error(f"Tempo até o erro: {elapsed_time:.2f} segundos")
        return {
            "Transportadora": "EPC",
            "frete": None,
            "prazo": None,
            "cotacao": None,
            "modal": "Rodoviário",
            "message": f"Erro na solicitação ao servidor: {e}"
        }

def gera_cotacao_epc(dados):
    """Gera cotação com a Princesa dos Campos utilizando os dados coletados."""
    payload = construir_payload_epc(dados)
    
    # Log do payload completo da requisição
    logger.debug(f"Payload da requisição Princesa dos Campos: {payload}")
    
    data = solicitar_cotacao_epc(payload)

    logger.debug(f"Response da requisição Princesa dos Campos: {data}")
    
    # Se o retorno já contém uma mensagem de erro, não tentar processar
    if "message" in data and data["message"]:
        # Substituir a mensagem específica por uma mais amigável
        mensagem_especifica = "Regiao de origem e destino nao atendida.."
        if data["message"] == mensagem_especifica:
            data["message"] = "Destino não atendido"
        
        logger.error(f"Erro na resposta Princesa dos Campos: {data['message']}")
        return data
    
    try:
        valor_frete = float(data.get("totalfrete", "0").replace('.', '').replace(',', '.'))
        data_prazo_str = data.get("prazo")
        if not data_prazo_str:
            prazo_entrega = None
        else:
            data_prazo = datetime.strptime(data_prazo_str, "%d/%m/%Y").date()
            data_atual = datetime.now().date()
            prazo_entrega = (data_prazo - data_atual).days
        
        cotacao_numero = data.get("numero", "-")  # Captura o número da cotação
        
        logger.debug(f"Valor do frete calculado: {valor_frete}, Prazo de entrega: {prazo_entrega} dias, Número da Cotação: {cotacao_numero}")

        return {
            "Transportadora": "EPC",
            "frete": valor_frete,
            "prazo": prazo_entrega,
            "cotacao": cotacao_numero,
            "modal": "Rodoviário",
            "message": None
        }

    except Exception as e:
        logger.error(f"Erro ao processar a resposta: {e}")
        return {
            "Transportadora": "EPC",
            "frete": None,
            "prazo": None,
            "cotacao": None,
            "modal": "Rodoviário",
            "message": f"Erro ao processar a resposta: {e}"
        }
