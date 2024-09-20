# services/controller/cotacao_consulta_controller.py
from flask import render_template, request, redirect, url_for, jsonify
from db.quotes import get_last_quotations, filter_quotations, get_quote_details
import logging

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CotacaoConsultaController:
    def __init__(self):
        pass

    def show_consultations(self):
        """Renderiza a página de consulta de cotações com as últimas 15 cotações."""
        try:
            quotations = get_last_quotations(limit=15)
            return render_template('consultations.html', quotations=quotations)
        except Exception as e:
            logger.error(f"Erro ao mostrar consultas: {str(e)}")
            return render_template('consultations.html', quotations=[], error="Erro ao carregar as cotações.")

    def filter_consultations(self):
        """Aplica filtros e retorna cotações filtradas."""
        try:
            filters = {
                'code': request.args.get('code', '').strip(),
                'cnpj': request.args.get('cnpj', '').strip(),
                'name': request.args.get('name', '').strip(),
                'date': request.args.get('date', '').strip()
            }
            quotations = filter_quotations(filters)
            return jsonify({'quotations': quotations})
        except Exception as e:
            logger.error(f"Erro ao filtrar consultas: {str(e)}")
            return jsonify({'error': 'Erro ao filtrar cotações.'}), 500

    def show_quote_details(self, quote_id):
        """Renderiza a página de detalhes de uma cotação específica."""
        try:
            quote_details = get_quote_details(quote_id)
            if not quote_details:
                return render_template('quote_details.html', error="Cotação não encontrada.")
            return render_template('quote_details.html', quote=quote_details)
        except Exception as e:
            logger.error(f"Erro ao mostrar detalhes da cotação {quote_id}: {str(e)}")
            return render_template('quote_details.html', error="Erro ao carregar os detalhes da cotação.")
