
import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Adiciona o diretório raiz ao PYTHONPATH para importar módulos do projeto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.data.database_manager import DatabaseManager
from src.core.models import Pessoa
from src.utils.utils import calculate_new_due_date
from src.config import PLANOS_COM_VENCIMENTO, TREINO_VALIDADE_DIAS
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'summit_mobile_pass_secret_key'  # Em produção, usar variável de ambiente

# Configuração do Rate Limiter (Segurança contra força bruta)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Inicializa o gerenciador de banco de dados
db_manager = DatabaseManager()

@app.route('/')
def index():
    """Página inicial com opções de Check-in e Cadastro."""
    return render_template('index.html')

@app.route('/checkin', methods=['GET', 'POST'])
@limiter.limit("10 per minute")  # Limite específico para check-in
def checkin():
    """Página e processamento de Check-in."""
    if request.method == 'POST':
        # Verifica se foi enviado um ID específico (seleção da lista)
        member_id = request.form.get('member_id')
        identifier = request.form.get('identifier')
        
        # Conecta ao banco se necessário
        if not db_manager.connection:
            db_manager.connect()

        if member_id:
            # Caso 1: ID específico fornecido (clique no botão Confirmar)
            try:
                member_id = int(member_id)
                member_data = db_manager.get_member_by_id(member_id)
            except (ValueError, TypeError):
                flash('ID de membro inválido.', 'error')
                return redirect(url_for('checkin'))
        
        elif identifier:
            # Caso 2: Busca por nome/apelido
            results = db_manager.find_members_by_name(identifier)
            
            if not results:
                flash('Membro não encontrado. Tente novamente ou faça seu cadastro.', 'error')
                return redirect(url_for('checkin'))
            
            if len(results) > 1:
                # Se encontrou vários, mostra a lista para seleção
                flash(f'Encontramos {len(results)} membros com esse nome. Confirme quem é você:', 'warning')
                return render_template('checkin.html', results=results, identifier=identifier)

            # Se encontrou apenas um
            member_data = results[0]
            member_id = member_data['id']
            
        else:
            flash('Por favor, informe seu Nome ou Apelido.', 'error')
            return redirect(url_for('checkin'))

        # Realiza o check-in (Lógica comum para ambos os casos)
        if member_data:
            try:
                # add_checkin retorna o ID do check-in ou None em caso de erro
                # E requer datetime.now() como segundo argumento
                checkin_id = db_manager.add_checkin(member_id, datetime.now())
                
                if checkin_id:
                    # Verifica status do plano para mensagem personalizada
                    estado_plano = member_data.get('estado_plano', 'ATIVO')
                    if estado_plano != 'ATIVO':
                        flash(f'Check-in realizado, mas atenção: Seu plano está {estado_plano}!', 'warning')
                    else:
                        flash(f'Bem-vindo(a), {member_data["nome"]}! Bom treino!', 'success')
                    return redirect(url_for('index'))
                else:
                    # Se retornou None, provavelmente é check-in duplicado ou erro
                    # Como add_checkin imprime erro mas não retorna mensagem, assumimos duplicado ou erro genérico
                    flash('Erro ao fazer check-in. Você já fez check-in hoje?', 'error')
                    return redirect(url_for('checkin'))
            except ValueError as e:
                # add_checkin pode levantar ValueError para duplicatas com mensagem específica
                flash(str(e), 'error')
                return redirect(url_for('checkin'))
            except Exception as e:
                flash(f'Erro inesperado: {str(e)}', 'error')
                return redirect(url_for('checkin'))
        else:
             flash('Erro ao recuperar dados do membro.', 'error')
             return redirect(url_for('checkin'))

    return render_template('checkin.html')

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per hour")  # Limite estrito para cadastro
def register():
    """Página e processamento de Cadastro."""
    if request.method == 'POST':
        # Coleta dados do formulário
        nome = request.form.get('nome')
        apelido = request.form.get('apelido')
        whatsapp = request.form.get('whatsapp')
        plano = request.form.get('plano')
        
        if not nome or not plano:
            flash('Nome e Plano são obrigatórios.', 'error')
            return redirect(url_for('register'))
            
        # Conecta ao banco se necessário
        if not db_manager.connection:
            db_manager.connect()
            
        member_data = {
            'nome': nome,
            'apelido': apelido,
            'whatsapp': whatsapp,
            'plano': plano,
            'data_nascimento': request.form.get('data_nascimento'),
            'email': request.form.get('email'),
            'genero': request.form.get('genero'),
            'calcado': request.form.get('calcado'),
            'treina': request.form.get('treina', 'Não'),
            'treina': request.form.get('treina', 'Não'),
            'estado_plano': 'PENDENTE' # Aguarda aprovação
        }

        # Calcular vencimento do plano
        if plano in PLANOS_COM_VENCIMENTO:
            new_due_date = calculate_new_due_date(plano)
            if new_due_date:
                 member_data['vencimento_plano'] = new_due_date.strftime('%d/%m/%Y')
        
        # Calcular vencimento do treino
        if member_data['treina'] == 'Sim':
            vencimento_treino = datetime.now() + timedelta(days=TREINO_VALIDADE_DIAS)
            member_data['vencimento_treino'] = vencimento_treino.strftime('%d/%m/%Y')
        
        # Adiciona membro (reutilizando lógica do desktop)
        try:
            member_id = db_manager.add_member(member_data)
            if member_id:
                flash('Cadastro realizado! Aguarde a aprovação do administrador para fazer check-in.', 'success')
                return redirect(url_for('index'))
            else:
                flash('Erro ao cadastrar. Tente novamente.', 'error')
        except Exception as e:
            flash(f'Erro interno: {str(e)}', 'error')
            
    # Carrega planos do config
    from src import config
    return render_template('register.html', planos=config.PLANOS)

if __name__ == '__main__':
    # Garante que as tabelas existam
    if not db_manager.connection:
        db_manager.connect()
    db_manager.create_tables()
    
    # Roda em todas as interfaces locais na porta 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
