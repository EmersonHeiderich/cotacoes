# services/transportadoras/esm.py

import requests
from datetime import datetime
import time
import logging

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constantes
URL_ES_MIGUEL = "https://wsintegcli01.expressosaomiguel.com.br:40504/wsservernet/rest/frete/buscar/portal-cliente"
HEADERS_ES_MIGUEL = {
    "access_key": "E0D625BFCD0B49E0B1D0E05EA1130A0C",
    "customer": "10424098000168",
    "version": "2"
}
FATOR_CUBAGEM_ES_MIGUEL = 300

def calcular_peso_cubado(dados):
    """Calcula o peso cubado total e retorna o peso final a ser usado na cotação."""
    peso_cubado_total = 0
    for pack in dados['pack']:
        comprimento_cm = pack['Length']
        altura_cm = pack['Height']
        largura_cm = pack['Width']
        
        volume_m3 = (comprimento_cm * altura_cm * largura_cm) / 1_000_000  # Convertendo cm³ para m³
        peso_cubado = volume_m3 * FATOR_CUBAGEM_ES_MIGUEL
        peso_cubado_total += peso_cubado * pack['AmountPackages']
    
    return max(peso_cubado_total, dados['total_weight'])

def construir_payload_es_miguel(dados, peso_final):
    """Constrói o payload para a requisição de cotação da Expresso São Miguel."""
    return {
        "tipoPagoPagar": "P",
        "codigoCidadeDestino": dados['cli_ibge_city_code'],  
        "quantidadeMercadoria": dados['total_packages'],
        "pesoMercadoria": peso_final,  # Utilizando o peso final (cubado ou real)
        "valorMercadoria": dados['invoice_value'],
        "tipoPeso": "P",
        "clienteDestino": dados['cli_cnpj'],
        "dataEmbarque": datetime.now().strftime("%d/%m/%Y"),
        "tipoPessoaDestino": "J"
    }

def obter_previsao_entrega(data):
    """Calcula o prazo de entrega em dias com base na resposta da API."""
    if not data.get('previsaoEmbarque') or not data.get('previsaoEntrega'):
        return None
    try:
        previsao_embarque = datetime.strptime(data.get('previsaoEmbarque'), "%d/%m/%Y")
        previsao_entrega = datetime.strptime(data.get('previsaoEntrega'), "%d/%m/%Y %H:%M")
        return (previsao_entrega - previsao_embarque).days
    except Exception as e:
        logger.error(f"Erro ao calcular prazo de entrega: {e}")
        return None

def solicitar_cotacao_es_miguel(payload):
    """Envia a solicitação de cotação e retorna a resposta."""
    start_time = time.time()  # Captura o tempo antes da chamada
    try:
        response = requests.post(URL_ES_MIGUEL, json=payload, headers=HEADERS_ES_MIGUEL)
        response.raise_for_status()  # Lança uma exceção para códigos de status HTTP 4xx/5xx
        elapsed_time = time.time() - start_time  # Calcula o tempo decorrido

        # Log do response da API e do tempo decorrido
        logger.debug(f"Resposta da API Expresso São Miguel: {response.text}")
        logger.info(f"Tempo de resposta da API Expresso São Miguel: {elapsed_time:.2f} segundos")

        return response.json()
    except requests.exceptions.RequestException as e:
        elapsed_time = time.time() - start_time  # Mesmo em caso de erro, calcular o tempo
        logger.error(f"Erro ao gerar cotação Expresso São Miguel: {e}")
        logger.error(f"Tempo até o erro: {elapsed_time:.2f} segundos")
        return None

def gera_cotacao_es_miguel(dados):
    """Gera cotação com a Expresso São Miguel utilizando os dados coletados."""
    peso_final = calcular_peso_cubado(dados)
    payload = construir_payload_es_miguel(dados, peso_final)
    
    # Log do payload completo da requisição
    logger.debug(f"Payload da requisição Expresso São Miguel: {payload}")
    
    data = solicitar_cotacao_es_miguel(payload)
    
    if not data or data.get("status") != "ok":
        erro_msg = data.get("mensagem") if data else 'Sem resposta'
        
        # Substituir mensagem específica por uma mais amigável
        mensagem_especifica = "Nenhuma Unidade de NegÃ³cio atende a localidade do cliente de destino"
        if erro_msg == mensagem_especifica:
            erro_msg = "Destino não atendido"
        
        logger.error(f"Erro na resposta Expresso São Miguel: {erro_msg}")
        return {
            "Transportadora": "ESM",
            "frete": None,
            "prazo": None,
            "cotacao": None,
            "modal": "Rodoviário",
            "message": erro_msg
        }
    
    valor_frete = data.get('valorFrete')
    prazo_entrega = obter_previsao_entrega(data)
    cotacao_protocolo = data.get('cotacaoProtocolo', '-')
    
    return {
        "Transportadora": "ESM",
        "frete": valor_frete,
        "prazo": prazo_entrega,
        "cotacao": cotacao_protocolo,
        "modal": "Rodoviário",
        "message": None  # Sem mensagem de erro
    }
