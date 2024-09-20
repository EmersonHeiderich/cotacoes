# services/controller/company_controller.py
from db.company import get_company_by_code
import logging

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompanyController:
    def __init__(self, company_code="100000011"):
        self.company_code = company_code

    def get_company_data(self):
        """Recupera dados da empresa do banco de dados."""
        company_data = get_company_by_code(self.company_code)
        if not company_data:
            logger.error(f"Empresa com código {self.company_code} não encontrada.")
        return company_data
