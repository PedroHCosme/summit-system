"""Aplicação web Flask para cadastro e check-in de membros."""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, g
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
except ImportError:
    def get_remote_address():
        return request.remote_addr or "127.0.0.1"

    class Limiter:
        """Fallback para ambientes de teste/desenvolvimento sem Flask-Limiter."""

        def __init__(self, *args, **kwargs):
            pass

        def limit(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.data.db import get_session_factory
from src.data.models import Membro, Plano
from src.services.checkin_service import CheckinService
from src.services.member_service import MemberService
from src.core.plan_status import (
    PENDENTE,
    STATUS_PLANO_EM_DIA,
    STATUS_PLANO_SEM_VENCIMENTO,
    STATUS_PLANO_VENCIDO,
    calcular_status_plano,
)
from src.core.models import Pessoa
from src.utils.utils import calculate_new_due_date

app = Flask(__name__)
app.secret_key = 'summit_mobile_pass_secret_key'

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

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


def _member_checkin_card(member: Membro, db) -> dict:
    """Monta dados seguros para o card de check-in web."""
    plan = None
    if member.plano_id:
        plan = db.query(Plano).filter(Plano.id == member.plano_id).first()
    if plan is None and member.plano:
        plan = db.query(Plano).filter(Plano.nome == member.plano).first()

    is_quota = bool(plan.is_quota) if plan else False
    voucher_credits = int(member.voucher_credits or 0)
    no_vouchers = is_quota and voucher_credits <= 0

    status = calcular_status_plano(
        vencimento_plano=member.vencimento_plano,
        estado_plano_db=member.estado_plano,
        is_quota=is_quota,
        valor_por_checkin=float(plan.valor_por_checkin or 0.0) if plan else 0.0,
    )

    status_labels = {
        STATUS_PLANO_EM_DIA: "Plano em dia",
        STATUS_PLANO_VENCIDO: "Plano vencido",
        STATUS_PLANO_SEM_VENCIMENTO: "Sem vencimento",
        PENDENTE: "Cadastro pendente",
    }

    digits = ''.join(ch for ch in str(member.whatsapp or '') if ch.isdigit())
    return {
        **member.to_dict(),
        'whatsapp_hint': f"Final {digits[-4:]}" if len(digits) >= 4 else "",
        'status_plano': status,
        'status_label': status_labels.get(status, status),
        'status_class': str(status).lower().replace(" ", "-"),
        'is_quota': is_quota,
        'voucher_credits': voucher_credits,
        'no_vouchers': no_vouchers,
        'can_checkin': status != PENDENTE and not no_vouchers,
        'requires_warning': status == STATUS_PLANO_VENCIDO,
    }

@app.route('/')
def index():
    """Página inicial com opções de Check-in e Cadastro."""
    return render_template('index.html')

@app.route('/checkin', methods=['GET', 'POST'])
@limiter.limit("10 per minute")  # Limite específico para check-in
def checkin():
    """Página e processamento de Check-in."""
    if request.method == 'POST':
        member_id = request.form.get('member_id')
        identifier = request.form.get('identifier')

        db = get_db()
        member_service = MemberService(db_session=db)
        checkin_service = CheckinService(db_session=db)

        if member_id:
            try:
                member_id = int(member_id)
                member = member_service.get_by_id(member_id)
                member_data = member.to_dict() if member else None
            except (ValueError, TypeError):
                flash('ID de membro inválido.', 'error')
                return redirect(url_for('checkin'))

            if member and member.estado_plano == PENDENTE:
                flash('Seu cadastro ainda está aguardando aprovação da academia.', 'warning')
                return redirect(url_for('checkin'))
        
        elif identifier:
            results = member_service.search_by_name(identifier)
            
            if not results:
                return render_template('checkin.html', not_found=True, identifier=identifier)
            
            results_dicts = [_member_checkin_card(m, db) for m in results]
            
            if len(results) == 1:
                flash('Membro encontrado! Confirme o check-in abaixo.', 'info')
            else:
                flash(f'Encontramos {len(results)} membros com esse nome. Confirme quem é você:', 'warning')
            
            return render_template('checkin.html', results=results_dicts, identifier=identifier)

        if member_data:
            result = checkin_service.perform_checkin(member_id, datetime.now())
            
            if result.success:
                card_data = _member_checkin_card(member, db)
                if card_data['status_plano'] == STATUS_PLANO_VENCIDO:
                    flash('Check-in realizado, mas atenção: seu plano parece vencido. Fale com a recepção.', 'warning')
                else:
                    flash(f'Bem-vindo(a), {member_data["nome"]}! Bom treino!', 'success')
                return redirect(url_for('index'))
            else:
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
        nome = request.form.get('nome', '').strip()
        sobrenome = request.form.get('sobrenome', '').strip()
        apelido = request.form.get('apelido')
        whatsapp = request.form.get('whatsapp')
        plano = request.form.get('plano')
        
        if not nome or not sobrenome:
            flash('Nome e Sobrenome são obrigatórios.', 'error')
            return redirect(url_for('register'))
        
        if not plano:
            flash('Plano é obrigatório.', 'error')
            return redirect(url_for('register'))

        whatsapp = request.form.get('whatsapp', '').strip()
        if not whatsapp:
            flash('WhatsApp é obrigatório.', 'error')
            return redirect(url_for('register'))

        calcado = request.form.get('calcado', '').strip()
        if not calcado:
            flash('Tamanho do calçado é obrigatório.', 'error')
            return redirect(url_for('register'))
        
        data_nascimento = request.form.get('data_nascimento')
        if data_nascimento:
            from datetime import date as date_cls
            try:
                dt_nasc = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
                if dt_nasc >= date_cls.today():
                    flash('A data de nascimento não pode ser a data de hoje ou uma data futura.', 'error')
                    return redirect(url_for('register'))
            except ValueError:
                flash('Data de nascimento inválida.', 'error')
                return redirect(url_for('register'))
        
        nome_completo = f"{nome} {sobrenome}"

        db = get_db()
        member_service = MemberService(db_session=db)
            
        member_data = {
            'nome': nome_completo,
            'apelido': apelido,
            'whatsapp': whatsapp,
            'plano': plano,
            'data_nascimento': data_nascimento,
            'email': request.form.get('email'),
            'genero': request.form.get('genero'),
            'calcado': request.form.get('calcado'),
            'treina': 'Não',
            'observacoes': request.form.get('observacoes'),
            'estado_plano': 'PENDENTE'
        }

        selected_plan_obj = db.query(Plano).filter_by(nome=plano, ativo=True).first()

        if selected_plan_obj and selected_plan_obj.requer_vencimento:
            new_due_date = calculate_new_due_date(plano)
            if new_due_date:
                 member_data['vencimento_plano'] = new_due_date.date() if hasattr(new_due_date, 'date') else new_due_date
        
        try:
            result = member_service.create(member_data)
            if result.success:
                flash('Cadastro realizado! Aguarde a aprovação do administrador para fazer check-in.', 'success')
                return redirect(url_for('index'))
            else:
                flash(f'Erro ao cadastrar: {result.message}', 'error')
        except Exception as e:
            flash(f'Erro interno: {str(e)}', 'error')
            
    db = get_db()
    plans = db.query(Plano).filter(Plano.ativo == True).all()
    plan_names = [p.nome for p in plans]
    return render_template('register.html', planos=plan_names)


if __name__ == '__main__':
    from src.data.db import init_db
    init_db()

    app.run(host='0.0.0.0', port=5000, debug=True)

