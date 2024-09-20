import requests
import xml.etree.ElementTree as ET
import time
import logging

# Configuração do logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def calcular_frete_tnt(dados_usuario):
    url = 'https://ws.tntbrasil.com.br:443/tntws/CalculoFrete'
    headers = {'Content-Type': 'text/xml; charset=utf-8'}
    timeout_duration = 25  # Timeout de 25 segundos

    def calcular_peso_cubado(dados_usuario):
        """Calcula o peso cubado total e retorna o peso final para a cotação."""
        fator_cubagem_tnt = 150
        peso_cubado_total = 0
        for pack in dados_usuario['pack']:
            comprimento_cm = pack['Length']
            altura_cm = pack['Height']
            largura_cm = pack['Width']
            
            volume_m3 = (comprimento_cm * altura_cm * largura_cm) / 1_000_000  # Convertendo cm³ para m³
            peso_cubado = volume_m3 * fator_cubagem_tnt
            peso_cubado_total += peso_cubado * pack['AmountPackages']
        return max(peso_cubado_total, dados_usuario['total_weight'])

    def tentar_calculo_frete(dados_usuario, tp_situacao_tributaria_destinatario, peso_final):
        """Tenta calcular o frete utilizando a situação tributária especificada."""
        body = f'''<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ser="http://service.calculoFrete.mercurio.com" xmlns:mod="http://model.vendas.lms.mercurio.com">
            <soapenv:Header/>
            <soapenv:Body>
                <ser:calculaFrete>
                    <ser:in0>
                        <mod:login>pedidos@kdu.com.br</mod:login>
                        <mod:senha>Kdufat2019@@</mod:senha>
                        <mod:nrIdentifClienteRem>{dados_usuario['comp_cnpj']}</mod:nrIdentifClienteRem>
                        <mod:nrIdentifClienteDest>{dados_usuario['cli_cnpj']}</mod:nrIdentifClienteDest>
                        <mod:tpFrete>C</mod:tpFrete>
                        <mod:tpServico>RNC</mod:tpServico>
                        <mod:cepOrigem>{dados_usuario['comp_cep']}</mod:cepOrigem>
                        <mod:cepDestino>{dados_usuario['cli_cep']}</mod:cepDestino>
                        <mod:vlMercadoria>{dados_usuario['invoice_value']}</mod:vlMercadoria>
                        <mod:psReal>{peso_final}</mod:psReal>
                        <mod:nrInscricaoEstadualRemetente>{dados_usuario['comp_number_state_registration']}</mod:nrInscricaoEstadualRemetente>
                        <mod:nrInscricaoEstadualDestinatario>{dados_usuario['cli_number_state_registration']}</mod:nrInscricaoEstadualDestinatario>
                        <mod:tpSituacaoTributariaRemetente>CO</mod:tpSituacaoTributariaRemetente>
                        <mod:tpSituacaoTributariaDestinatario>{tp_situacao_tributaria_destinatario}</mod:tpSituacaoTributariaDestinatario>
                        <mod:cdDivisaoCliente>3</mod:cdDivisaoCliente>
                        <mod:tpPessoaRemetente>J</mod:tpPessoaRemetente>
                        <mod:tpPessoaDestinatario>J</mod:tpPessoaDestinatario>
                    </ser:in0>
                </ser:calculaFrete>
            </soapenv:Body>
        </soapenv:Envelope>'''

        # Logando o payload da requisição para debug
        logger.debug(f"Payload da requisição TNT:\n{body}")

        start_time = time.time()  # Captura o tempo antes da requisição

        try:
            response = requests.post(url, headers=headers, data=body, timeout=timeout_duration)
            elapsed_time = time.time() - start_time  # Calcula o tempo decorrido após a resposta
            logger.info(f"Tempo de resposta da API TNT: {elapsed_time:.2f} segundos")

            if response.status_code != 200:
                logger.error(f"Erro na requisição: Código {response.status_code}, Mensagem: {response.reason}")
                return {
                    "Transportadora": "TNT",
                    "frete": None,
                    "prazo": None,
                    "cotacao": None,
                    "modal": "Rodoviário",
                    "message": f"Erro na requisição: {response.status_code} - {response.reason}"
                }

            try:
                root = ET.fromstring(response.text)
                namespaces = {
                    'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
                    'ser': 'http://service.calculoFrete.mercurio.com'
                }

                out = root.find('.//ser:out', namespaces)
                if out is None:
                    logger.error("Elemento 'out' não encontrado na resposta.")
                    return {
                        "Transportadora": "TNT",
                        "frete": None,
                        "prazo": None,
                        "cotacao": None,
                        "modal": "Rodoviário",
                        "message": "Elemento 'out' não encontrado na resposta"
                    }
                
                # Verifica se há uma lista de erros
                error_list = out.findtext('.//errorList')
                if error_list:
                    logger.warning(f"Erro retornado pela API TNT: {error_list}")
                    return {
                        "Transportadora": "TNT",
                        "frete": None,
                        "prazo": None,
                        "cotacao": None,
                        "modal": "Rodoviário",
                        "message": error_list
                    }

                vl_total_frete = out.findtext('.//vlTotalFrete')
                prazo_entrega = out.findtext('.//prazoEntrega')

                if vl_total_frete and float(vl_total_frete) > 0 and prazo_entrega and int(prazo_entrega) > 0:
                    logger.debug(f"Cotação bem-sucedida: Frete={vl_total_frete}, Prazo={prazo_entrega} dias")
                    return {
                        "Transportadora": "TNT",
                        "frete": float(vl_total_frete),
                        "prazo": int(prazo_entrega),
                        "cotacao": None,  # Adicione um número de cotação se disponível
                        "modal": "Rodoviário",
                        "message": None
                    }
                else:
                    logger.error("Frete não calculado corretamente. Verifique os dados fornecidos.")
                    return {
                        "Transportadora": "TNT",
                        "frete": None,
                        "prazo": None,
                        "cotacao": None,
                        "modal": "Rodoviário",
                        "message": "Frete não calculado corretamente"
                    }

            except ET.ParseError as e:
                logger.error(f"Erro ao analisar o XML da resposta: {e}")
                return {
                    "Transportadora": "TNT",
                    "frete": None,
                    "prazo": None,
                    "cotacao": None,
                    "modal": "Rodoviário",
                    "message": f"Erro ao analisar o XML da resposta: {e}"
                }

        except requests.exceptions.Timeout:
            logger.error("Tempo de espera da API TNT excedido (25 segundos).")
            return {
                "Transportadora": "TNT",
                "frete": None,
                "prazo": None,
                "cotacao": None,
                "modal": "Rodoviário",
                "message": "Tempo de espera da API TNT excedido (25 segundos)"
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao fazer a requisição: {e}")
            return {
                "Transportadora": "TNT",
                "frete": None,
                "prazo": None,
                "cotacao": None,
                "modal": "Rodoviário",
                "message": f"Erro ao fazer a requisição: {e}"
            }

    # Calcula o peso cubado ou usa o peso real, o que for maior
    peso_final = calcular_peso_cubado(dados_usuario)

    # Tentativa 1: Se receiver_ie estiver ausente, nulo ou for 'ISENTO', tenta com situação 'NC'
    if not dados_usuario['cli_number_state_registration'] or dados_usuario['cli_number_state_registration'].upper() == "ISENTO":
        dados_usuario['cli_number_state_registration'] = "ISENTO"
        resultado = tentar_calculo_frete(dados_usuario, 'NC', peso_final)
        if resultado and resultado.get('message') is None:
            return resultado

    # Tentativa 2: Com situação tributária 'CO'
    resultado = tentar_calculo_frete(dados_usuario, 'CO', peso_final)
    if resultado and resultado.get('message') is None:
        return resultado

    # Verifica se o erro retornado foi "Situação tributária do destinatário não confere com o cadastro."
    mensagem_erro = resultado.get('message', '')
    if "Situação tributaria do destinatario não confere com o cadastro." in mensagem_erro:
        # Tentativa 3: Com situação tributária 'ME'
        resultado = tentar_calculo_frete(dados_usuario, 'ME', peso_final)
        if resultado and resultado.get('message') is None:
            return resultado
    else:
        logger.warning("Tentativa 3 não será executada, pois a mensagem de erro não é sobre a situação tributária.")

    # Caso todas as tentativas falhem
    logger.error(f"Tentativa de cotação falhou em todas as tentativas. Erro: {resultado.get('message', 'Erro desconhecido')}")
    return {
        "Transportadora": "TNT",
        "frete": None,
        "prazo": None,
        "cotacao": None,
        "modal": "Rodoviário",
        "message": resultado.get('message', 'Tentativa de cotação falhou em todas as tentativas')
    }
