# services/controller/cotacao_controller.py
from services.transportadoras.btu import gera_cotacao_braspress
from services.transportadoras.epc import gera_cotacao_epc
from services.transportadoras.esm import gera_cotacao_es_miguel
from services.transportadoras.rte import gera_cotacao_rte
from services.transportadoras.ssw import consultar_transportadora, TRANSPORTADORAS_SSW
from services.transportadoras.tnt import calcular_frete_tnt
from db.quotes import inserir_quote, get_next_protocolo
from db.quote_packages import inserir_quote_packages
from db.quote_responses import inserir_quote_response
from services.controller.company_controller import CompanyController
import eventlet
import logging

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CotacaoController:
    def gerar_protocolo(self):
        """Gera um número sequencial único para a cotação."""
        protocolo = get_next_protocolo()
        logger.info(f"Protocolo gerado: {protocolo}")
        return protocolo

    def obter_dados_para_cotacao(self, client_data, packages_data, invoice_value):
        """Compila dados do cliente e das embalagens para enviar às transportadoras."""
        if not client_data:
            logger.error("Dados do cliente não coletados. Não é possível prosseguir.")
            return None

        if not packages_data:
            logger.error("Dados das embalagens não coletados. Não é possível prosseguir.")
            return None

        # Instanciar CompanyController localmente
        company_controller = CompanyController()
        company_data = company_controller.get_company_data()
        if not company_data:
            logger.error("Dados da empresa não coletados. Não é possível prosseguir.")
            return None

        volume_total = round(packages_data['total_volume'], 4)

        # Gerar número único de protocolo
        protocolo = self.gerar_protocolo()

        cotacao_data = {
            "comp_name": company_data['name'],
            "comp_cnpj": company_data['cnpj'],
            "comp_number_state_registration": company_data['number_state_registration'],
            "comp_city_name": company_data['city_name'],
            "comp_state_abbreviation": company_data['state_abbreviation'],
            "comp_cep": company_data['cep'],
            "comp_ibge_city_code": company_data['ibge_city_code'],
            "protocolo": protocolo,
            "cli_cnpj": client_data['cnpj'],
            "cli_cep": client_data['cep'],
            "cli_number_state_registration": client_data.get('number_state_registration', 'ISENTO'),
            "cli_ibge_city_code": client_data['ibge_city_code'],
            "invoice_value": invoice_value,
            "pack": [
                {
                    "AmountPackages": pack['AmountPackages'],
                    "Weight": pack['Weight'],
                    "Length": pack['Length'],
                    "Height": pack['Height'],
                    "Width": pack['Width']
                } for pack in packages_data['pack']
            ],
            "total_weight": packages_data['total_weight'],
            "total_packages": packages_data['total_packages'],
            "volume_total": volume_total,
            "comp_city_id": 6609,
            "comp_contact_name": "Departamento de TI",
            "comp_contact_phone": "46988259847"
        }

        logger.debug(f"Dados da cotação: {cotacao_data}")
        return cotacao_data

    def solicitar_cotacoes(self, cotacao_data, callback):
        """Envia dados para as transportadoras solicitar cotações concorrentes."""
        if not cotacao_data:
            logger.error("Dados insuficientes para solicitar cotações.")
            return

        logger.info(f"Solicitando cotações... (Protocolo: {cotacao_data['protocolo']})")

        # Salvar a cotação no banco de dados
        quote_id = inserir_quote(cotacao_data)
        logger.info(f"Cotação salva no banco de dados com ID: {quote_id} e protocolo: {cotacao_data['protocolo']}")

        # Salvar as embalagens associadas à cotação
        inserir_quote_packages(quote_id, cotacao_data['pack'])

        # Definir funções das transportadoras
        transportadoras_funcs = [
            lambda: gera_cotacao_braspress(cotacao_data, modal="R"),
            lambda: gera_cotacao_braspress(cotacao_data, modal="A"),
            lambda: gera_cotacao_epc(cotacao_data),
            lambda: gera_cotacao_es_miguel(cotacao_data),
            lambda: gera_cotacao_rte(cotacao_data),
            lambda: calcular_frete_tnt(cotacao_data),
        ]

        # Transportadoras SSW
        for transportadora in TRANSPORTADORAS_SSW:
            def ssw_func(t=transportadora):
                return consultar_transportadora(
                    dominio=t['dominio'],
                    login=t['login'],
                    senha=t['senha'],
                    mercadoria=t['mercadoria'],
                    url=t['url'],
                    soap_action=t['soap_action'],
                    dados_usuario=cotacao_data
                )
            transportadoras_funcs.append(ssw_func)

        pool = eventlet.GreenPool()

        def handle_result(cotacao):
            if cotacao:
                inserir_quote_response(quote_id, cotacao)
                callback(cotacao)
            else:
                # Tratar cotação falhada
                logger.warning("Falha ao obter cotação de uma transportadora.")

        for func in transportadoras_funcs:
            pool.spawn_n(self.request_and_handle, func, handle_result)

        pool.waitall()

    def request_and_handle(self, func, callback):
        try:
            cotacao = func()
            callback(cotacao)
        except Exception as e:
            logger.error(f"Erro ao solicitar cotação: {e}")
            callback(None)
