import requests
import xml.etree.ElementTree as ET
import html
import time
import logging

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Definição da lista de transportadoras SSW
TRANSPORTADORAS_SSW = [
    {
        'nome': 'Bauer',
        'dominio': 'BAU',
        'login': 'kdu',
        'senha': 'sq2n6m1',
        'mercadoria': 3,
        'url': 'https://ssw.inf.br/ws/sswCotacao/index.php',
        'soap_action': 'urn:sswinfbr.sswCotacao#cotacao'
    },
    {
        'nome': 'Zanotelli',
        'dominio': 'PEP',
        'login': 'kduconf',
        'senha': 'kduconf',
        'mercadoria': 38,
        'url': 'https://ssw.inf.br/ws/sswCotacao/index.php',
        'soap_action': 'urn:sswinfbr.sswCotacao#cotacao'
    },
    {
        'nome': 'Eucatur',
        'dominio': 'EUC',
        'login': 'kdu',
        'senha': '10424098',
        'mercadoria': 1,
        'url': 'https://ssw.inf.br/ws/sswCotacao/index.php',
        'soap_action': 'urn:sswinfbr.sswCotacao#cotacao'
    }
]

def consultar_transportadora(dominio, login, senha, mercadoria, url, soap_action, dados_usuario):
    """Consulta a transportadora SSW com base nos dados fornecidos."""
    
    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': soap_action
    }

    peso_total = dados_usuario['total_weight']
    volume_total = dados_usuario['volume_total']

    body = f'''<soapenv:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:sswinfbr.sswCotacao">
        <soapenv:Header/>
        <soapenv:Body>
            <urn:cotar soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
                <dominio xsi:type="xsd:string">{dominio}</dominio>
                <login xsi:type="xsd:string">{login}</login>
                <senha xsi:type="xsd:string">{senha}</senha>
                <cnpjPagador xsi:type="xsd:string">{dados_usuario['comp_cnpj']}</cnpjPagador>
                <cepOrigem xsi:type="xsd:integer">{dados_usuario['comp_cep']}</cepOrigem>
                <cepDestino xsi:type="xsd:integer">{dados_usuario['cli_cep']}</cepDestino>
                <valorNF xsi:type="xsd:decimal">{dados_usuario['invoice_value']}</valorNF>
                <quantidade xsi:type="xsd:integer">{dados_usuario['total_packages']}</quantidade>
                <peso xsi:type="xsd:decimal">{peso_total}</peso>
                <volume xsi:type="xsd:decimal">{volume_total}</volume>
                <mercadoria xsi:type="xsd:integer">{mercadoria}</mercadoria>
                <cnpjDestinatario xsi:type="xsd:string">{dados_usuario['cli_cnpj']}</cnpjDestinatario>
                <coletar xsi:type="xsd:string"></coletar>
                <entDificil xsi:type="xsd:string"></entDificil>
                <destContribuinte xsi:type="xsd:string"></destContribuinte>
                <qtdePares xsi:type="xsd:integer"></qtdePares>
                <fatorMultiplicador xsi:type="xsd:integer"></fatorMultiplicador>
            </urn:cotar>
        </soapenv:Body>
    </soapenv:Envelope>'''

    # Logando o payload da requisição para debug
    logger.debug(f"Payload da requisição para {dominio}: {body}")

    start_time = time.time()  # Captura o tempo antes da requisição

    try:
        response = requests.post(url, headers=headers, data=body)
        elapsed_time = time.time() - start_time  # Calcula o tempo decorrido após a resposta
        logger.info(f"Tempo de resposta da API {dominio}: {elapsed_time:.2f} segundos")

        if response.status_code != 200:
            logger.error(f"Erro na requisição para {dominio}: {response.status_code}")
            return {
                "Transportadora": dominio,
                "frete": None,
                "prazo": None,
                "cotacao": None,
                "modal": "Rodoviário",
                "message": f"Erro na requisição: {response.status_code}"
            }

        root = ET.fromstring(response.text)
        namespaces = {
            'SOAP-ENV': 'http://schemas.xmlsoap.org/soap/envelope/',
            'ns1': 'urn:sswinfbr.sswCotacao'
        }

        cotarResponse = root.find('.//SOAP-ENV:Body/ns1:cotarResponse', namespaces)
        if cotarResponse is None:
            logger.error(f"Elemento cotarResponse não encontrado para {dominio}.")
            return {
                "Transportadora": dominio,
                "frete": None,
                "prazo": None,
                "cotacao": None,
                "modal": "Rodoviário",
                "message": "Elemento cotarResponse não encontrado"
            }

        return_xml = cotarResponse.findtext('.//return')
        if return_xml is None:
            logger.error(f"Elemento return não encontrado para {dominio}.")
            return {
                "Transportadora": dominio,
                "frete": None,
                "prazo": None,
                "cotacao": None,
                "modal": "Rodoviário",
                "message": "Elemento return não encontrado"
            }

        try:
            return_root = ET.fromstring(return_xml)
            valor_frete = return_root.findtext('.//totalFrete', '0')
            prazo = return_root.findtext('.//prazo', '0')
            mensagem_erro = return_root.findtext('.//mensagem')
            cod_erro = return_root.findtext('.//erro')

            # Decodificar entidades HTML
            if mensagem_erro:
                mensagem_erro = html.unescape(mensagem_erro)

            logger.debug(f"Resposta da API {dominio}: valorFrete={valor_frete}, prazo={prazo}, codErro={cod_erro}, mensagemErro={mensagem_erro}")

            # Se o valor do frete e prazo forem 0 ou houver uma mensagem de erro, considerar como "Destino não atendido"
            if valor_frete == '0' or prazo == '0' or cod_erro != '0':
                logger.warning(f"Destino não atendido pela transportadora {dominio}.")
                return {
                    "Transportadora": dominio,
                    "frete": None,
                    "prazo": None,
                    "cotacao": None,
                    "modal": "Rodoviário",
                    "message": "Destino não atendido"
                }
            
            # Se for a Zanotelli, ajustar o valor do frete
            if dominio == "PEP" and valor_frete != '0':
                valor_frete = float(valor_frete) / 0.88  # Ajusta o valor do frete com impostos
                valor_frete = round(valor_frete, 2)
                logger.debug(f"Valor do frete ajustado para Zanotelli: {valor_frete}")

            return {
                "Transportadora": dominio,
                "frete": float(valor_frete),
                "prazo": int(prazo),
                "cotacao": None,
                "modal": "Rodoviário",
                "message": None
            }
        except ET.ParseError as e:
            logger.error(f"Erro ao analisar XML interno para {dominio}: {e}")
            return {
                "Transportadora": dominio,
                "frete": None,
                "prazo": None,
                "cotacao": None,
                "modal": "Rodoviário",
                "message": f"Erro ao analisar XML interno: {e}"
            }

    except ET.ParseError as e:
        logger.error(f"Erro ao analisar XML de resposta para {dominio}: {e}")
        return {
            "Transportadora": dominio,
            "frete": None,
            "prazo": None,
            "cotacao": None,
            "modal": "Rodoviário",
            "message": f"Erro ao analisar XML de resposta: {e}"
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na solicitação para {dominio}: {e}")
        return {
            "Transportadora": dominio,
            "frete": None,
            "prazo": None,
            "cotacao": None,
            "modal": "Rodoviário",
            "message": f"Erro na solicitação: {e}"
        }