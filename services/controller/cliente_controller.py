# services/controller/cliente_controller.py
from services.totvs.person import get_legal_entity_data
from db.clientes import verificar_cliente_existente, atualizar_cliente, inserir_cliente
import logging

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClienteController:
    def coletar_dados_cliente(self, identifier, invoice_value):
        """Coleta dados do cliente usando o código ou CNPJ fornecido."""
        client_data = get_legal_entity_data(identifier)

        if client_data:
            # Verificar se o cliente já existe no banco de dados
            cliente_existente = verificar_cliente_existente(
                client_data['cnpj'], client_data['code']
            )

            if cliente_existente:
                logger.info("Cliente já existe no banco de dados. Verificando atualizações...")

                # Comparar dados existentes com os retornados pela API
                if not self._dados_sao_iguais(cliente_existente, client_data):
                    logger.info("Informações do cliente alteradas. Atualizando...")
                    atualizar_cliente(client_data)
                else:
                    logger.info("Informações do cliente estão atualizadas. Nenhuma ação necessária.")
            else:
                logger.info("Cliente não encontrado no banco de dados. Inserindo novo cliente...")
                inserir_cliente(client_data)

            invoice_val = float(invoice_value)
            logger.info("Dados do cliente coletados e processados com sucesso.")
            return client_data, invoice_val

        else:
            logger.error("Nenhum dado encontrado para o identificador fornecido.")
            return None, None

    def _dados_sao_iguais(self, cliente_existente, cliente_atual):
        """Compara dados do cliente no banco de dados com os retornados pela API."""
        campos_para_comparar = [
            'name', 'number_state_registration', 'city_name',
            'state_abbreviation', 'cep', 'address', 'neighborhood',
            'address_number', 'ibge_city_code'
        ]

        for campo in campos_para_comparar:
            valor_banco = cliente_existente.get(campo)
            valor_atual = cliente_atual.get(self._mapear_campo_para_api(campo))

            if str(valor_banco) != str(valor_atual):  # Comparar valores como strings
                return False

        return True

    def _mapear_campo_para_api(self, campo_banco):
        """Mapeia campos do banco para os retornados pela API."""
        mapa = {
            'name': 'name',
            'number_state_registration': 'number_state_registration',
            'city_name': 'city_name',
            'state_abbreviation': 'state_abbreviation',
            'cep': 'cep',
            'address': 'address',
            'neighborhood': 'neighborhood',
            'address_number': 'address_number',
            'ibge_city_code': 'ibge_city_code'
        }
        return mapa.get(campo_banco)
