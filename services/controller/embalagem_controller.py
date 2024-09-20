# services/controller/embalagem_controller.py
from services.packages.package_manager import PackageManager
import logging

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbalagemController:
    def coletar_dados_embalagens(self, packages_data):
        """Coleta dados das embalagens enviadas pela interface web."""
        package_manager = PackageManager()
        for package_info in packages_data:
            if package_info['type'] == 'predefined':
                package_id = int(package_info['package_id'])
                peso = float(package_info['peso']) if package_info.get('peso') else None
                quantidade = int(package_info['quantidade'])
                try:
                    package_manager.select_pre_defined_package(package_id, peso, quantidade)
                except ValueError as e:
                    logger.error(f"Erro ao adicionar embalagem pré-definida: {e}")
            elif package_info['type'] == 'custom':
                nome = package_info['nome']
                comprimento = float(package_info['comprimento'])
                altura = float(package_info['altura'])
                largura = float(package_info['largura'])
                peso = float(package_info['peso'])
                quantidade = int(package_info['quantidade'])
                package_manager.add_custom_package(
                    nome, comprimento, altura, largura, peso, quantidade
                )
            else:
                logger.warning(f"Tipo de embalagem desconhecido: {package_info['type']}")
        return package_manager.get_packages_for_cotation()

    @staticmethod
    def get_predefined_packages():
        """Retorna embalagens pré-definidas."""
        package_manager = PackageManager()
        return package_manager.pre_defined_packages
