"""
Serviço de Membros.

Encapsula toda a lógica de negócio relacionada à gestão de membros,
incluindo CRUD, busca e validações.

Este módulo utiliza SQLAlchemy para type safety e queries tipadas.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple, Union
from dataclasses import dataclass
import re
import unicodedata

from sqlalchemy import func, or_, and_
from sqlalchemy.orm import Session

from src.core.plan_status import ATIVO, INATIVO
from src.data.models import Membro, Frequencia, Pagamento, Plano
from src.utils.date_utils import coerce_to_date, format_display_date


@dataclass
class MemberResult:
    """Resultado de uma operação de membro."""
    success: bool
    member_id: Optional[int] = None
    message: str = ""
    member: Optional[Membro] = None


@dataclass
class PaginatedResult:
    """Resultado de uma busca paginada."""
    members: List[Dict[str, Any]]
    total: int
    page: int
    total_pages: int
    page_size: int


class MemberService:
    """
    Serviço responsável por gerenciar operações de membros.
    
    Regras de negócio encapsuladas:
    - Validação de campos obrigatórios
    - Normalização de dados
    - Gestão de planos e vencimentos
    
    """

    def __init__(self, db_session: Session):
        """
        Inicializa o serviço de membros.

        Args:
            db_session: Sessão SQLAlchemy para acesso aos dados
        """
        self._session = db_session

    @property
    def session(self) -> Optional[Session]:
        """Retorna a sessão SQLAlchemy se disponível."""
        return self._session
    
    # =========================================================================
    # MÉTODOS CRUD
    # =========================================================================
    
    def create(self, member_data: Dict[str, Any]) -> MemberResult:
        """
        Cria um novo membro.
        
        Args:
            member_data: Dicionário com os dados do membro.
                        Campos obrigatórios: nome
        
        Returns:
            MemberResult com o resultado da operação
        """
        # Validação
        nome = member_data.get('nome', '').strip()
        if not nome:
            return MemberResult(
                success=False,
                message="O campo 'nome' é obrigatório."
            )

        duplicate_error = self._validate_unique_registration(member_data)
        if duplicate_error:
            return MemberResult(success=False, message=duplicate_error)
        
        # Definir estado padrão se não fornecido
        if 'estado_plano' not in member_data:
            member_data['estado_plano'] = ATIVO
        
        # Limpar vencimento para planos sem vencimento.
        plano = member_data.get('plano')
        if plano and not self._plan_requires_vencimento(plano):
            member_data['vencimento_plano'] = None
        
        return self._create_sqlalchemy(member_data)
    
    def get_by_id(self, member_id: int) -> Optional[Union[Membro, Dict[str, Any]]]:
        """
        Busca um membro por ID.
        
        Args:
            member_id: ID do membro
            
        Returns:
            Membro (SQLAlchemy) ou Dict (legado) ou None se não encontrado
        """
        return self._session.query(Membro).filter(Membro.id == member_id).first()
    
    def get_by_id_as_dict(self, member_id: int) -> Optional[Dict[str, Any]]:
        """
        Busca um membro por ID, sempre retornando como dicionário.
        
        Args:
            member_id: ID do membro
            
        Returns:
            Dicionário com dados do membro ou None
        """
        result = self.get_by_id(member_id)
        if result is None:
            return None
        if isinstance(result, Membro):
            return result.to_dict()
        return result
    
    def search_by_name(self, name_query: str) -> List[Union[Membro, Dict[str, Any]]]:
        """
        Busca membros por nome com busca inteligente.
        
        Suporta busca por palavras separadas:
        - "Pedro Cosme" encontra "Pedro Henrique de Menezes Cosme"
        - "Cosme" encontra "Pedro Henrique de Menezes Cosme"
        
        Args:
            name_query: Nome ou parte do nome a buscar
            
        Returns:
            Lista de membros encontrados
        """
        return self._search_by_name_sqlalchemy(name_query)
    
    def search_by_name_as_dicts(self, name_query: str) -> List[Dict[str, Any]]:
        """Busca membros por nome, sempre retornando como lista de dicts."""
        results = self.search_by_name(name_query)
        return [
            m.to_dict() if isinstance(m, Membro) else m
            for m in results
        ]
    
    def get_all(self) -> List[Union[Membro, Dict[str, Any]]]:
        """
        Retorna todos os membros.
        
        Returns:
            Lista de todos os membros
        """
        return self._session.query(Membro).order_by(Membro.nome).all()
    
    def get_all_as_dicts(self) -> List[Dict[str, Any]]:
        """Retorna todos os membros como lista de dicts."""
        results = self.get_all()
        return [
            m.to_dict() if isinstance(m, Membro) else m
            for m in results
        ]

    def get_recent_members(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retorna os membros cadastrados mais recentemente.

        Usa ID como critério secundário para ordenar cadastros feitos no mesmo dia.
        """
        members = (
            self._session.query(Membro)
            .order_by(Membro.data_cadastro.desc().nulls_last(), Membro.id.desc())
            .limit(limit)
            .all()
        )
        return [member.to_dict() for member in members]
    
    def get_paginated(
        self,
        page: int = 1,
        page_size: int = 50,
        filter_text: str = "",
        filter_plan: str = "",
        filter_status: str = "",
        sort_by: str = "nome",
        sort_dir: str = "asc"
    ) -> PaginatedResult:
        """
        Retorna membros com paginação e filtros.
        
        Args:
            page: Número da página (começa em 1)
            page_size: Quantidade de itens por página
            filter_text: Texto para filtrar por nome
            filter_plan: Filtrar por plano específico
            filter_status: Filtrar por status (ATIVO/INATIVO) — ver plan_status.py
            sort_by: Coluna para ordenação (nome, data_cadastro, vencimento_plano)
            sort_dir: Direção da ordenação (asc, desc)
            
        Returns:
            PaginatedResult com os membros e metadados de paginação
        """
        return self._get_paginated_sqlalchemy(
            page, page_size, filter_text, filter_plan, filter_status,
            sort_by, sort_dir
        )

    
    def update(self, member_id: int, **kwargs) -> MemberResult:
        """
        Atualiza os dados de um membro.
        
        Args:
            member_id: ID do membro
            **kwargs: Campos a atualizar (plano, nome, whatsapp, etc.)
            
        Returns:
            MemberResult com o resultado da operação
        """
        return self._update_sqlalchemy(member_id, **kwargs)
    
    def update_from_dict(
        self, 
        member_data: Dict[str, Any],
        register_payment: bool = False,
        metodo_pagamento: str = ""
    ) -> MemberResult:
        """
        Atualiza os dados de um membro usando um dicionário.
        
        Args:
            member_data: Dicionário com os dados (deve incluir 'id')
            register_payment: Se True, registra pagamento ao atualizar plano
            metodo_pagamento: Método de pagamento usado
            
        Returns:
            MemberResult com o resultado da operação
        """
        member_id = member_data.get('id')
        if not member_id:
            return MemberResult(
                success=False,
                message="O campo 'id' é obrigatório para atualização."
            )
        
        return self._update_from_dict_sqlalchemy(
            member_data, register_payment, metodo_pagamento
        )
    
    def delete(self, member_id: int) -> MemberResult:
        """
        Remove um membro do sistema.
        
        Args:
            member_id: ID do membro a ser removido
            
        Returns:
            MemberResult com o resultado da operação
        """
        return self._delete_sqlalchemy(member_id)
    
    # =========================================================================
    # MÉTODOS DE CONSULTA ESPECIALIZADOS
    # =========================================================================
    
    def get_birthdays(self, month: int) -> List[Dict[str, Any]]:
        """
        Busca membros que fazem aniversário em um mês.
        
        Args:
            month: Número do mês (1-12)
            
        Returns:
            Lista de membros aniversariantes
        """
        return self._get_birthdays_sqlalchemy(month)
    
    def update_expired_plans(self) -> int:
        """
        Atualiza o estado do plano para INATIVO para membros vencidos.
        
        Returns:
            Número de membros atualizados
        """
        return self._update_expired_plans_sqlalchemy()
    
    def count_by_status(self) -> Dict[str, int]:
        """
        Conta membros por status de plano.
        
        Returns:
            Dicionário com contagem por status
        """
        return self._count_by_status_sqlalchemy()
    
    def count_by_plan(self) -> Dict[str, int]:
        """
        Conta membros por tipo de plano.
        
        Returns:
            Dicionário com contagem por plano
        """
        return self._count_by_plan_sqlalchemy()
    
    # =========================================================================
    # IMPLEMENTAÇÃO SQLALCHEMY
    # =========================================================================
    
    def _create_sqlalchemy(self, member_data: Dict[str, Any]) -> MemberResult:
        """Cria um membro usando SQLAlchemy."""
        try:
            plano_nome = member_data.get('plano')
            plano_ref = None
            if plano_nome:
                plano_ref = self._session.query(Plano).filter(Plano.nome == plano_nome).first()

            new_member = Membro(
                nome=member_data.get('nome'),
                data_cadastro=date.today(),
                plano=plano_nome,
                plano_id=plano_ref.id if plano_ref else None,
                vencimento_plano=coerce_to_date(member_data.get('vencimento_plano')),
                estado_plano=member_data.get('estado_plano', ATIVO),
                data_nascimento=coerce_to_date(member_data.get('data_nascimento')),
                whatsapp=member_data.get('whatsapp'),
                genero=member_data.get('genero'),
                email=member_data.get('email'),
                apelido=member_data.get('apelido'),
                profissao=member_data.get('profissao'),
                contato_emergencia=member_data.get('contato_emergencia'),
                frequencia=member_data.get('frequencia'),
                observacoes=member_data.get('observacoes'),
                calcado=member_data.get('calcado'),
                voucher_credits=member_data.get('voucher_credits', 0),
                treina=member_data.get('treina'),
                vencimento_treino=coerce_to_date(member_data.get('vencimento_treino'))
            )
            
            self._session.add(new_member)
            self._session.commit()
            
            return MemberResult(
                success=True,
                member_id=new_member.id,
                message=f"Membro '{new_member.nome}' criado com sucesso.",
                member=new_member
            )
            
        except Exception as e:
            self._session.rollback()
            return MemberResult(
                success=False,
                message=f"Erro ao criar membro: {str(e)}"
            )
    
    def _validate_unique_registration(self, member_data: Dict[str, Any]) -> str:
        """
        Valida duplicidade nos dados-chave de cadastro.

        Nome, email e WhatsApp identificam cadastros duplicados. WhatsApp repetido
        é permitido quando o novo membro é menor de idade, pois pode ser o contato
        do responsável.
        """
        nome = self._normalize_name(member_data.get('nome'))
        email = self._normalize_email(member_data.get('email'))
        whatsapp = self._normalize_phone(member_data.get('whatsapp'))
        is_minor = self._is_minor(member_data.get('data_nascimento'))

        for member in self.get_all():
            existing = member.to_dict() if isinstance(member, Membro) else member

            if nome and self._normalize_name(existing.get('nome')) == nome:
                return "Já existe um membro cadastrado com este nome."

            if email and self._normalize_email(existing.get('email')) == email:
                return "Já existe um membro cadastrado com este email."

            if (
                whatsapp
                and not is_minor
                and self._normalize_phone(existing.get('whatsapp')) == whatsapp
            ):
                return "Já existe um membro maior de idade cadastrado com este WhatsApp."

        return ""

    def _get_plan_by_name(self, plan_name: str) -> Optional[Plano]:
        """Busca plano ativo pelo nome quando há sessão SQLAlchemy disponível."""
        if not plan_name:
            return None
        return self._session.query(Plano).filter(
            Plano.nome == plan_name,
            Plano.ativo == True
        ).first()

    def _plan_requires_vencimento(self, plan_name: str) -> bool:
        """Define se um plano exige vencimento usando a tabela Plano como fonte principal."""
        plan = self._get_plan_by_name(plan_name)
        if plan is not None:
            return bool(plan.requer_vencimento and not plan.is_quota)

        from src.config import PLANOS_COM_VENCIMENTO
        return plan_name in PLANOS_COM_VENCIMENTO

    @staticmethod
    def _is_training_active(value: Any) -> bool:
        """Normaliza o campo treina para comparação."""
        return str(value or "").strip().casefold() == "sim"

    @staticmethod
    def _normalize_name(value: Any) -> str:
        """Normaliza nome para comparação de duplicidade."""
        if value is None:
            return ""
        text = str(value).strip().casefold()
        text = unicodedata.normalize('NFD', text)
        text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
        return ' '.join(text.split())

    @staticmethod
    def _normalize_email(value: Any) -> str:
        """Normaliza email para comparação de duplicidade."""
        if value is None:
            return ""
        return str(value).strip().casefold()

    @staticmethod
    def _normalize_phone(value: Any) -> str:
        """Mantém apenas dígitos para comparação de WhatsApp."""
        if value is None:
            return ""
        return re.sub(r'\D+', '', str(value))

    @staticmethod
    def _is_minor(data_nascimento: Any) -> bool:
        """Retorna True quando a data de nascimento indica menor de 18 anos."""
        birth_date = coerce_to_date(data_nascimento)
        if not birth_date:
            return False

        today = date.today()
        age = today.year - birth_date.year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
        return age < 18
    
    def _search_by_name_sqlalchemy(self, name_query: str) -> List[Membro]:
        """Busca membros por nome usando SQLAlchemy."""
        tokens = [t.strip() for t in name_query.split() if t.strip()]
        if not tokens:
            return []
        
        # Construir filtros para cada token
        filters = []
        for token in tokens:
            pattern = f"%{token}%"
            filters.append(
                or_(
                    func.unaccent(Membro.nome).ilike(func.unaccent(pattern)),
                    func.unaccent(Membro.apelido).ilike(func.unaccent(pattern))
                )
            )
        
        return self._session.query(Membro).filter(
            and_(*filters)
        ).order_by(Membro.nome).all()
    
    def _get_paginated_sqlalchemy(
        self,
        page: int,
        page_size: int,
        filter_text: str,
        filter_plan: str,
        filter_status: str,
        sort_by: str = "nome",
        sort_dir: str = "asc"
    ) -> PaginatedResult:
        """Busca paginada usando SQLAlchemy."""
        query = self._session.query(Membro)
        
        # Aplicar filtros
        if filter_text:
            tokens = filter_text.strip().split()
            for token in tokens:
                pattern = f"%{token}%"
                query = query.filter(
                    or_(
                        func.unaccent(Membro.nome).ilike(func.unaccent(pattern)),
                        func.unaccent(Membro.apelido).ilike(func.unaccent(pattern))
                    )
                )
        
        if filter_plan:
            query = query.filter(Membro.plano == filter_plan)
        
        if filter_status:
            query = query.filter(Membro.estado_plano == filter_status)
        
        # Contar total
        total = query.count()
        
        # Calcular paginação
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        page = max(1, min(page, total_pages)) if total_pages > 0 else 1
        offset = (page - 1) * page_size
        
        # Ordenação dinâmica com validação
        ALLOWED_SORT_COLUMNS = {
            'nome': Membro.nome,
            'data_cadastro': Membro.data_cadastro,
            'vencimento_plano': Membro.vencimento_plano,
        }
        sort_column = ALLOWED_SORT_COLUMNS.get(sort_by, Membro.nome)
        
        if sort_dir == "desc":
            order_clause = sort_column.desc().nulls_last()
        else:
            order_clause = sort_column.asc().nulls_last()
        order_clauses = [order_clause]
        if sort_by == 'data_cadastro':
            order_clauses.append(Membro.id.desc() if sort_dir == "desc" else Membro.id.asc())
        
        # Buscar membros da página
        members = query.order_by(*order_clauses).offset(offset).limit(page_size).all()
        
        return PaginatedResult(
            members=[m.to_dict() for m in members],
            total=total,
            page=page,
            total_pages=total_pages,
            page_size=page_size
        )

    
    def _update_sqlalchemy(self, member_id: int, **kwargs) -> MemberResult:
        """Atualiza um membro usando SQLAlchemy."""
        try:
            member = self._session.query(Membro).filter(Membro.id == member_id).first()
            if not member:
                return MemberResult(
                    success=False,
                    message=f"Membro com ID {member_id} não encontrado."
                )
            
            # Atualizar campos fornecidos
            for key, value in kwargs.items():
                if hasattr(member, key) and value is not None:
                    setattr(member, key, value)

            # Camada de compatibilidade: manter plano_id sincronizado ao atualizar plano por nome.
            if kwargs.get('plano'):
                plano_ref = self._session.query(Plano).filter(Plano.nome == kwargs['plano']).first()
                member.plano_id = plano_ref.id if plano_ref else None
            
            member.updated_at = datetime.now()
            self._session.commit()
            
            return MemberResult(
                success=True,
                member_id=member_id,
                message="Membro atualizado com sucesso.",
                member=member
            )
            
        except Exception as e:
            self._session.rollback()
            return MemberResult(
                success=False,
                message=f"Erro ao atualizar membro: {str(e)}"
            )
    
    def _update_from_dict_sqlalchemy(
        self,
        member_data: Dict[str, Any],
        register_payment: bool,
        metodo_pagamento: str
    ) -> MemberResult:
        """Atualiza um membro de dict usando SQLAlchemy."""
        member_id = member_data.get('id')
        
        try:
            member = self._session.query(Membro).filter(Membro.id == member_id).first()
            if not member:
                return MemberResult(
                    success=False,
                    message=f"Membro com ID {member_id} não encontrado."
                )
            
            # Verificar se houve mudança de plano
            old_plan = member.plano
            old_vencimento = member.vencimento_plano
            old_treina = member.treina
            old_vencimento_treino = member.vencimento_treino
            new_plan = member_data.get('plano', old_plan)
            new_vencimento = coerce_to_date(member_data.get('vencimento_plano', old_vencimento))
            new_treina = member_data.get('treina', old_treina)
            new_vencimento_treino = coerce_to_date(
                member_data.get('vencimento_treino', old_vencimento_treino)
            )
            plan_changed = (old_plan != new_plan) or (old_vencimento != new_vencimento)
            training_renewed = (
                self._is_training_active(new_treina)
                and (
                    not self._is_training_active(old_treina)
                    or old_vencimento_treino != new_vencimento_treino
                )
            )
            
            # Query new plan from database to check if quota-based
            new_plan_db = None
            is_new_plan_quota = False
            if new_plan:
                new_plan_db = self._session.query(Plano).filter(Plano.nome == new_plan).first()
                is_new_plan_quota = new_plan_db.is_quota if new_plan_db else False
            quota_purchase_requested = (
                is_new_plan_quota
                and register_payment
                and ('voucher_credits' in member_data or 'price' in member_data)
            )
            
            # Query old plan to check if it was quota-based
            old_plan_db = None
            is_old_plan_quota = False
            if old_plan:
                old_plan_db = self._session.query(Plano).filter(Plano.nome == old_plan).first()
                is_old_plan_quota = old_plan_db.is_quota if old_plan_db else False
            
            # Handle voucher credits based on plan type
            if is_new_plan_quota and (plan_changed or quota_purchase_requested):
                # Quota plan: accumulate credits
                credits_to_add = member_data.get('voucher_credits')
                if credits_to_add is None and new_plan_db:
                    credits_to_add = new_plan_db.quota_amount
                if credits_to_add:
                    member.voucher_credits = (member.voucher_credits or 0) + credits_to_add
                # Quota plans don't have expiration
                member.vencimento_plano = None
                member.estado_plano = ATIVO
            elif not is_new_plan_quota and is_old_plan_quota and plan_changed:
                # Switching from quota to time-based: reset credits (mutual exclusivity)
                member.voucher_credits = 0

            if new_plan and not is_new_plan_quota and not self._plan_requires_vencimento(new_plan):
                member.vencimento_plano = None
            
            # Atualizar campos (excluding voucher_credits which is handled above for quota plans)
            updatable_fields = [
                'nome', 'plano', 'vencimento_plano', 'estado_plano',
                'data_nascimento', 'whatsapp', 'genero', 'email', 'apelido',
                'profissao', 'contato_emergencia', 'frequencia', 'observacoes', 'calcado',
                'treina', 'vencimento_treino'
            ]
            
            for field in updatable_fields:
                if field in member_data:
                    # Skip vencimento_plano for plans without due date (already set to None above)
                    if (
                        field == 'vencimento_plano'
                        and new_plan
                        and not self._plan_requires_vencimento(new_plan)
                    ):
                        continue
                    value = member_data[field]
                    # Coerce date fields from any format (str, QDate, etc.) to date
                    if field in ('vencimento_plano', 'data_nascimento', 'vencimento_treino'):
                        value = coerce_to_date(value)
                    setattr(member, field, value)

            # Camada de compatibilidade: atualizar referência canônica opcional de plano.
            if 'plano' in member_data:
                member.plano_id = new_plan_db.id if new_plan_db else None
            
            # Handle voucher_credits manual override
            # We effectively allow update if provided, EXCEPT if it was already handled 
            # by the "new plan purchase" accumulation logic above (is_new_plan_quota and plan_changed)
            if 'voucher_credits' in member_data:
                already_handled = is_new_plan_quota and (plan_changed or quota_purchase_requested)
                if not already_handled:
                    member.voucher_credits = member_data['voucher_credits']
            
            member.updated_at = datetime.now()
            
            # Registrar pagamento se necessário
            if register_payment and new_plan and (plan_changed or quota_purchase_requested):
                from src.core.payment_constants import TIPO_COMPRA_VOUCHER, TIPO_RENOVACAO_PLANO
                valor = 0.0
                
                # For quota plans, use explicit price or plan price
                if is_new_plan_quota:
                    if 'price' in member_data:
                        valor = float(member_data['price'])
                    elif new_plan_db:
                        valor = new_plan_db.preco
                else:
                    # Time-based plan pricing
                    if new_plan_db:
                        valor = new_plan_db.preco
                    else:
                        from src.config import PLANOS_PRECOS
                        valor = PLANOS_PRECOS.get(new_plan, 0.0)
                
                is_quota_purchase = is_new_plan_quota and (valor > 0 or 'voucher_credits' in member_data)

                if valor > 0 or is_quota_purchase:
                    from src.core.plan_policy import PlanPolicy
                    tipo_transacao = (
                        PlanPolicy(new_plan_db).renewal_transaction_type
                        if new_plan_db
                        else (TIPO_COMPRA_VOUCHER if is_new_plan_quota else TIPO_RENOVACAO_PLANO)
                    )
                    new_payment = Pagamento(
                        member_id=member_id,
                        data_pagamento=datetime.now(),
                        tipo_transacao=tipo_transacao,
                        descricao=f"{new_plan} - {member.nome}",
                        valor=valor,
                        metodo_pagamento=metodo_pagamento,
                        nova_data_vencimento=coerce_to_date(new_vencimento) if not is_new_plan_quota else None
                    )
                    self._session.add(new_payment)

            if register_payment and training_renewed:
                from src.config import TREINO_PRECO
                from src.core.payment_constants import TIPO_PAGAMENTO_TREINO

                self._session.add(Pagamento(
                    member_id=member_id,
                    data_pagamento=datetime.now(),
                    tipo_transacao=TIPO_PAGAMENTO_TREINO,
                    descricao=f"Treino - {member.nome}",
                    valor=TREINO_PRECO,
                    metodo_pagamento=metodo_pagamento,
                    nova_data_vencimento=new_vencimento_treino
                ))
            
            self._session.commit()
            
            return MemberResult(
                success=True,
                member_id=member_id,
                message="Membro atualizado com sucesso.",
                member=member
            )
            
        except Exception as e:
            self._session.rollback()
            return MemberResult(
                success=False,
                message=f"Erro ao atualizar membro: {str(e)}"
            )
    
    def _delete_sqlalchemy(self, member_id: int) -> MemberResult:
        """Remove um membro usando SQLAlchemy."""
        try:
            member = self._session.query(Membro).filter(Membro.id == member_id).first()
            if not member:
                return MemberResult(
                    success=False,
                    message=f"Membro com ID {member_id} não encontrado."
                )
            
            nome = member.nome
            self._session.delete(member)
            self._session.commit()
            
            return MemberResult(
                success=True,
                member_id=member_id,
                message=f"Membro '{nome}' removido com sucesso."
            )
            
        except Exception as e:
            self._session.rollback()
            return MemberResult(
                success=False,
                message=f"Erro ao remover membro: {str(e)}"
            )
    
    def _get_birthdays_sqlalchemy(self, month: int) -> List[Dict[str, Any]]:
        """Busca aniversariantes usando SQLAlchemy."""
        # With native Date columns we can filter directly
        members = self._session.query(Membro).filter(
            Membro.data_nascimento.isnot(None)
        ).all()
        
        birthdays = []
        for member in members:
            if member.data_nascimento and member.data_nascimento.month == month:
                birthdays.append(member.to_dict())
        
        # Ordenar por dia
        from src.utils.date_utils import parse_date
        birthdays.sort(key=lambda m: parse_date(m.get('data_nascimento', '')).day if parse_date(m.get('data_nascimento', '')) else 0)
        return birthdays
    
    def _update_expired_plans_sqlalchemy(self) -> int:
        """Atualiza planos expirados usando SQLAlchemy.

        With native Date columns, comparison is direct — no string parsing needed.
        """
        today = date.today()
        updated_count = 0
        
        members = self._session.query(Membro).filter(
            Membro.vencimento_plano.isnot(None),
            Membro.estado_plano == ATIVO
        ).all()
        
        for member in members:
            if member.plano and not self._plan_requires_vencimento(member.plano):
                continue
            if member.vencimento_plano < today:
                member.estado_plano = INATIVO
                member.updated_at = datetime.now()
                updated_count += 1
        
        if updated_count > 0:
            self._session.commit()
        
        return updated_count
    
    def _count_by_status_sqlalchemy(self) -> Dict[str, int]:
        """Conta membros por status usando SQLAlchemy."""
        results = self._session.query(
            Membro.estado_plano,
            func.count(Membro.id)
        ).group_by(Membro.estado_plano).all()
        
        return {status or 'N/A': count for status, count in results}
    
    def _count_by_plan_sqlalchemy(self) -> Dict[str, int]:
        """Conta membros por plano usando SQLAlchemy."""
        results = self._session.query(
            Membro.plano,
            func.count(Membro.id)
        ).group_by(Membro.plano).all()

        return {plano or 'N/A': count for plano, count in results}

    # =========================================================================
    # QUERIES ESPECIALIZADAS
    # =========================================================================

    def get_all_excluding_pending(self) -> List[Membro]:
        """
        Retorna todos os membros excluindo os com estado PENDENTE.

        Usado por relatórios que não devem incluir cadastros web não aprovados.
        """
        from src.core.plan_status import PENDENTE
        return self._session.query(Membro).filter(Membro.estado_plano != PENDENTE).all()
