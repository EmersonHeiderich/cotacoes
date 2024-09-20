# app.py
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, redirect, url_for, request, session, jsonify
from flask_socketio import SocketIO, emit, join_room
from services.controller.cliente_controller import ClienteController
from services.controller.embalagem_controller import EmbalagemController
from services.controller.cotacao_controller import CotacaoController
from services.controller.company_controller import CompanyController
from services.controller.cotacao_consulta_controller import CotacaoConsultaController  # Importar o novo controlador
import logging

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Substitua por uma chave segura em produção

# Initialize SocketIO
socketio = SocketIO(app, async_mode='eventlet')

# Definição do mapeamento das transportadoras
TRANSPORTADORA_MAP = {
    'BAU': 'Bauer',
    'TNT': 'TNT Mercúrio',
    'EPC': 'Princesa dos Campos',
    'EUC': 'Eucatur',
    'RTE': 'Rodonaves',
    'PEP': 'Zanotelli',
    'BTU': 'Braspress',
    'ESM': 'Exp. São Miguel',
    # Adicione mais mapeamentos conforme necessário
}

# Instanciar o CotacaoConsultaController
cotacao_consulta_controller = CotacaoConsultaController()

# Route para a página inicial
@app.route('/')
def index():
    return render_template('index.html')

# Route para entrada de dados do cliente
@app.route('/client', methods=['GET', 'POST'])
def client():
    if request.method == 'POST':
        identifier = request.form.get('identifier')
        invoice_value = request.form.get('invoice_value')
        if not identifier or not invoice_value:
            error = "Por favor, preencha todos os campos."
            return render_template('client.html', error=error)
        
        # Instanciar ClienteController
        cliente_controller = ClienteController()
        client_data, invoice_val = cliente_controller.coletar_dados_cliente(identifier, invoice_value)
        
        if client_data:
            # Armazenar dados do cliente na sessão
            session['client_data'] = client_data
            session['invoice_value'] = invoice_val
            # Limpar dados de embalagens anteriores
            session.pop('packages_data', None)
            return redirect(url_for('packages'))
        else:
            error = "Cliente não encontrado ou erro ao obter dados."
            return render_template('client.html', error=error)
    return render_template('client.html')

# Route para gestão de embalagens
@app.route('/packages', methods=['GET', 'POST'])
def packages():
    if 'client_data' not in session:
        return redirect(url_for('client'))
    if request.method == 'POST':
        # Processar dados das embalagens enviados via JSON
        packages_data = request.get_json()
        
        # Instanciar EmbalagemController
        embalagem_controller = EmbalagemController()
        processed_packages = embalagem_controller.coletar_dados_embalagens(packages_data)
        
        # Armazenar dados das embalagens na sessão
        session['packages_data'] = processed_packages
        return jsonify({'redirect': url_for('quotations')})
    return render_template('packages.html',
                           predefined_packages=EmbalagemController.get_predefined_packages(),
                           client_data=session['client_data'])  # Passar client_data

# Route para exibir cotações
@app.route('/quotations', methods=['GET'])
def quotations():
    if 'client_data' not in session or 'packages_data' not in session:
        return redirect(url_for('client'))
    # Instanciar CotacaoController
    cotacao_controller = CotacaoController()
    protocolo = cotacao_controller.gerar_protocolo()
    return render_template('quotations.html',
                           client_data=session['client_data'],
                           packages=session['packages_data']['pack'],
                           protocolo=protocolo,
                           total_weight=session['packages_data']['total_weight'],
                           total_volume=session['packages_data']['total_volume'],
                           total_packages=session['packages_data']['total_packages'],
                           invoice_value=session['invoice_value'])  # Passar invoice_value

# Rotas para consulta de cotações
@app.route('/consultations', methods=['GET'])
def consultations():
    return cotacao_consulta_controller.show_consultations()

@app.route('/consultations/filter', methods=['GET'])
def consultations_filter():
    return cotacao_consulta_controller.filter_consultations()

@app.route('/consultations/<int:quote_id>', methods=['GET'])
def quote_details(quote_id):
    return cotacao_consulta_controller.show_quote_details(quote_id)

@socketio.on('start_quotation')
def handle_start_quotation():
    app.logger.info(f"Received 'start_quotation' from session: {request.sid}")
    room = request.sid
    join_room(room)
    
    # Instanciar os controladores
    cotacao_controller = CotacaoController()
    
    client_data = session.get('client_data')
    packages_data = session.get('packages_data')
    invoice_value = session.get('invoice_value')
    
    cotacao_data = cotacao_controller.obter_dados_para_cotacao(
        client_data,
        packages_data,
        invoice_value
    )
    if not cotacao_data:
        emit('quotation_error', {'error': 'Dados insuficientes para cotação.'}, room=room)
        app.logger.error("Dados insuficientes para cotação.")
        return
    # Iniciar tarefa em background
    socketio.start_background_task(target=process_quotations, cotacao_data=cotacao_data, room=room)

def process_quotations(cotacao_data, room):
    app.logger.info(f"Processing quotations for protocol: {cotacao_data.get('protocolo')}")
    
    # Instanciar CotacaoController
    cotacao_controller = CotacaoController()
    
    def emit_new_quotation(cotacao):
        # Mapear o código da transportadora para o nome
        transportadora_code = cotacao.get('Transportadora')
        transportadora_name = TRANSPORTADORA_MAP.get(transportadora_code, transportadora_code)
        cotacao['Transportadora'] = transportadora_name

        # Verificar se a cotação é válida
        is_valid = True
        # Supondo que uma cotação inválida tenha 'frete' como None, '-', ou 0
        if cotacao.get('frete') in [None, '-', 0]:
            is_valid = False

        if not is_valid:
            # Definir os campos como '-'
            cotacao['modal'] = '-'
        else:
            # Caso válido, já mapeamos o nome da transportadora acima
            pass  # Nenhuma ação adicional necessária

        socketio.emit('new_quotation', {'cotacao': cotacao}, room=room)
        logger.info(f"Emitted quotation: {cotacao}")

    cotacao_controller.solicitar_cotacoes(cotacao_data, emit_new_quotation)
    
    # Após todas as cotações serem enviadas, emitir um evento de conclusão
    socketio.emit('quotations_complete', {}, room=room)
    logger.info("All quotations have been emitted.")

if __name__ == '__main__':
    socketio.run(app, host='10.1.1.15', port=5001, debug=True)
