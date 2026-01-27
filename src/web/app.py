
import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Adiciona o diretório raiz ao PYTHONPATH para importar módulos do projeto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.data.db import get_session_factory
from src.data.models import Membro, Plano
from src.services.checkin_service import CheckinService
from src.services.member_service import MemberService
from src.core.models import Pessoa
from src.utils.utils import calculate_new_due_date
from src.config import TREINO_VALIDADE_DIAS
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

# Session factory para SQLAlchemy
SessionLocal = get_session_factory()


def get_db():
    """Obtém uma sessão do banco de dados para a requisição atual."""
    if 'db' not in g:
        g.db = SessionLocal()
    return g.db


@app.teardown_appcontext
def close_db(exception):
    """Fecha a sessão do banco ao final da requisição."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

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
        
        # Obtém sessão do banco de dados
        db = get_db()
        member_service = MemberService(db_session=db)
        checkin_service = CheckinService(db_session=db)

        if member_id:
            # Caso 1: ID específico fornecido (clique no botão Confirmar)
            try:
                member_id = int(member_id)
                member = member_service.get_by_id(member_id)
                member_data = member.to_dict() if member else None
            except (ValueError, TypeError):
                flash('ID de membro inválido.', 'error')
                return redirect(url_for('checkin'))
        
        elif identifier:
            # Caso 2: Busca por nome/apelido
            results = member_service.search_by_name(identifier)
            
            if not results:
                flash('Membro não encontrado. Tente novamente ou faça seu cadastro.', 'error')
                return redirect(url_for('checkin'))
            
            # Sempre mostrar a lista de resultados para confirmação (mesmo que seja apenas 1)
            results_dicts = [m.to_dict() if hasattr(m, 'to_dict') else m for m in results]
            
            if len(results) == 1:
                flash('Membro encontrado! Confirme o check-in abaixo.', 'info')
            else:
                flash(f'Encontramos {len(results)} membros com esse nome. Confirme quem é você:', 'warning')
            
            return render_template('checkin.html', results=results_dicts, identifier=identifier)

        # Realiza o check-in usando o serviço (Lógica comum para ambos os casos)
        if member_data:
            # Usa o CheckinService para realizar o check-in
            result = checkin_service.perform_checkin(member_id, datetime.now())
            
            if result.success:
                # Verifica status do plano para mensagem personalizada
                estado_plano = member_data.get('estado_plano', 'ATIVO')
                if estado_plano != 'ATIVO':
                    flash(f'Check-in realizado, mas atenção: Seu plano está {estado_plano}!', 'warning')
                else:
                    flash(f'Bem-vindo(a), {member_data["nome"]}! Bom treino!', 'success')
                return redirect(url_for('index'))
            else:
                # Erro no check-in (duplicado ou outro problema)
                flash(result.message, 'error')
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
        
        # Obtém sessão do banco de dados
        db = get_db()
        member_service = MemberService(db_session=db)
            
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
            'observacoes': request.form.get('observacoes'),
            'estado_plano': 'PENDENTE'  # Aguarda aprovação
        }

        # Buscar detalhes do plano no banco
        selected_plan_obj = db.query(Plano).filter_by(nome=plano, ativo=True).first()

        # Calcular vencimento do plano
        if selected_plan_obj and selected_plan_obj.requer_vencimento:
            new_due_date = calculate_new_due_date(plano)
            if new_due_date:
                 member_data['vencimento_plano'] = new_due_date.strftime('%d/%m/%Y')
        
        # Calcular vencimento do treino
        if member_data['treina'] == 'Sim':
            vencimento_treino = datetime.now() + timedelta(days=TREINO_VALIDADE_DIAS)
            member_data['vencimento_treino'] = vencimento_treino.strftime('%d/%m/%Y')
        
        # Adiciona membro usando o serviço
        try:
            result = member_service.create(member_data)
            if result.success:
                flash('Cadastro realizado! Aguarde a aprovação do administrador para fazer check-in.', 'success')
                return redirect(url_for('index'))
            else:
                flash(f'Erro ao cadastrar: {result.message}', 'error')
        except Exception as e:
            flash(f'Erro interno: {str(e)}', 'error')
            
    # Carrega planos ativos do banco
    db = get_db()
    plans = db.query(Plano).filter(Plano.ativo == True).all()
    plan_names = [p.nome for p in plans]
    return render_template('register.html', planos=plan_names)


if __name__ == '__main__':
    # Garante que as tabelas existam usando SQLAlchemy
    from src.data.db import init_db
    init_db()
    
    # Roda em todas as interfaces locais na porta 5000
    app.run(host='0.0.0.0', port=5000, debug=True)

