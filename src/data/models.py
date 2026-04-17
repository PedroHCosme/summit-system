"""
Modelos SQLAlchemy ORM para o banco de dados.

Este módulo define as classes que mapeiam as tabelas do banco de dados
para objetos Python, oferecendo type safety e autocomplete no IDE.
"""

from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, Date, ForeignKey,
    func, event, Boolean, Index
)
from sqlalchemy.orm import relationship, Mapped, mapped_column, declarative_base

from src.utils.date_utils import format_display_date

# Base declarativa para os modelos
Base = declarative_base()


class Membro(Base):
    """
    Modelo ORM para a tabela de membros.
    
    Representa um membro/aluno do sistema com seus dados pessoais,
    informações de plano e relacionamentos com check-ins e pagamentos.
    """
    __tablename__ = "membros"
    
    # Campos principais
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    plano: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    plano_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("planos.id", ondelete="SET NULL"), nullable=True
    )
    vencimento_plano: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    estado_plano: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Dados pessoais
    data_nascimento: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    data_cadastro: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    whatsapp: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    genero: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    apelido: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    profissao: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    contato_emergencia: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Informações adicionais
    frequencia: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    calcado: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    voucher_credits: Mapped[int] = mapped_column(Integer, default=0)
    
    # Treino
    treina: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    vencimento_treino: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=func.current_timestamp()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp()
    )
    
    # Relacionamentos
    checkins: Mapped[List["Frequencia"]] = relationship(
        "Frequencia", back_populates="membro", cascade="all, delete-orphan"
    )
    pagamentos: Mapped[List["Pagamento"]] = relationship(
        "Pagamento", back_populates="membro", cascade="all, delete-orphan"
    )
    plano_ref: Mapped[Optional["Plano"]] = relationship("Plano", back_populates="membros")
    
    def __repr__(self) -> str:
        return (
            f"<Membro(id={self.id}, nome='{self.nome}', plano='{self.plano}', "
            f"plano_id={self.plano_id})>"
        )
    
    def to_dict(self) -> dict:
        """Converte o modelo para dicionário (compatibilidade com código legado).

        Datas são convertidas para strings DD/MM/YYYY para exibição na UI.
        """
        return {
            "id": self.id,
            "nome": self.nome,
            # Camada de compatibilidade: durante a migração manter `plano` por nome.
            "plano": self.plano or (self.plano_ref.nome if self.plano_ref else None),
            "plano_id": self.plano_id,
            "vencimento_plano": format_display_date(self.vencimento_plano) if self.vencimento_plano else None,
            "estado_plano": self.estado_plano,
            "data_nascimento": format_display_date(self.data_nascimento) if self.data_nascimento else None,
            "data_cadastro": format_display_date(self.data_cadastro) if self.data_cadastro else None,
            "whatsapp": self.whatsapp,
            "genero": self.genero,
            "email": self.email,
            "apelido": self.apelido,
            "profissao": self.profissao,
            "contato_emergencia": self.contato_emergencia,
            "frequencia": self.frequencia,
            "observacoes": self.observacoes,
            "calcado": self.calcado,
            "voucher_credits": self.voucher_credits,
            "treina": self.treina,
            "vencimento_treino": format_display_date(self.vencimento_treino) if self.vencimento_treino else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Frequencia(Base):
    """
    Modelo ORM para a tabela de frequência (check-ins).
    
    Cada registro representa um check-in de um membro.
    Regra de negócio: apenas 1 check-in por membro por dia.
    """
    __tablename__ = "frequencia"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("membros.id", ondelete="CASCADE"), nullable=False
    )
    checkin_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=func.current_timestamp()
    )
    
    # Relacionamento com Membro
    membro: Mapped["Membro"] = relationship("Membro", back_populates="checkins")
    
    def __repr__(self) -> str:
        return f"<Frequencia(id={self.id}, member_id={self.member_id}, datetime={self.checkin_datetime})>"
    
    def to_dict(self) -> dict:
        """Converte o modelo para dicionário."""
        return {
            "id": self.id,
            "member_id": self.member_id,
            "checkin_datetime": self.checkin_datetime.isoformat() if self.checkin_datetime else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Pagamento(Base):
    """
    Modelo ORM para a tabela de pagamentos.
    
    Registra todas as transações financeiras do sistema,
    incluindo renovações de plano, check-ins de diárias, etc.
    """
    __tablename__ = "pagamentos"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    member_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("membros.id", ondelete="SET NULL"), nullable=True
    )
    data_pagamento: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=func.current_timestamp()
    )
    tipo_transacao: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    valor: Mapped[float] = mapped_column(Float, nullable=False)
    metodo_pagamento: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    nova_data_vencimento: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=func.current_timestamp()
    )
    
    # Relacionamento com Membro
    membro: Mapped[Optional["Membro"]] = relationship("Membro", back_populates="pagamentos")
    
    def __repr__(self) -> str:
        return f"<Pagamento(id={self.id}, tipo='{self.tipo_transacao}', valor={self.valor})>"
    
    def to_dict(self) -> dict:
        """Converte o modelo para dicionário."""
        return {
            "id": self.id,
            "member_id": self.member_id,
            "data_pagamento": self.data_pagamento.isoformat() if self.data_pagamento else None,
            "tipo_transacao": self.tipo_transacao,
            "descricao": self.descricao,
            "valor": self.valor,
            "metodo_pagamento": self.metodo_pagamento,
            "nova_data_vencimento": format_display_date(self.nova_data_vencimento) if self.nova_data_vencimento else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class Plano(Base):
    """
    Modelo ORM para a tabela de planos.
    
    Armazena as configurações de preços e regras de negócio dos planos.
    Substitui as configurações hardcoded em src/config.py.
    """
    __tablename__ = "planos"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    preco: Mapped[float] = mapped_column(Float, default=0.0)  # Preço de renovação
    valor_por_checkin: Mapped[float] = mapped_column(Float, default=0.0)  # Preço por check-in
    requer_vencimento: Mapped[bool] = mapped_column(Boolean, default=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Quota-based plans (e.g., "Pacote 10")
    is_quota: Mapped[bool] = mapped_column(Boolean, default=False)  # If True, plan is quantity-based
    quota_amount: Mapped[int] = mapped_column(Integer, default=0)   # Number of credits per purchase
    
    # Metadata
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=func.current_timestamp()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp()
    )
    membros: Mapped[List["Membro"]] = relationship("Membro", back_populates="plano_ref")
    
    def __repr__(self) -> str:
        return f"<Plano(nome='{self.nome}', preco={self.preco})>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "preco": self.preco,
            "valor_por_checkin": self.valor_por_checkin,
            "requer_vencimento": self.requer_vencimento,
            "ativo": self.ativo,
            "is_quota": self.is_quota,
            "quota_amount": self.quota_amount
        }

class Nota(Base):
    """
    Modelo ORM para a tabela de notas (Bloco de Notas).

    Armazena anotações do usuário (bugs, ideias, outros) que podem
    ser enviadas por e-mail ao desenvolvedor.
    """
    __tablename__ = "notas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False, default="Nova Nota")
    conteudo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False, default="outro")  # bug, ideia, outro
    enviada: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=func.current_timestamp()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp()
    )

    def __repr__(self) -> str:
        return f"<Nota(id={self.id}, titulo='{self.titulo}', tipo='{self.tipo}')>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "titulo": self.titulo,
            "conteudo": self.conteudo,
            "tipo": self.tipo,
            "enviada": self.enviada,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

# Nota: Para saber quais planos cobram por check-in, use config.PLANOS_PAGAMENTO_POR_CHECKIN
# ou consulte a tabela 'planos' (Plano.valor_por_checkin > 0).

# Índices e guardas de integridade para novos bancos.
Index("ix_membros_plano_id", Membro.plano_id)
Index("ix_frequencia_member_checkin_datetime", Frequencia.member_id, Frequencia.checkin_datetime)
Index("uq_frequencia_member_day", Frequencia.member_id, func.date(Frequencia.checkin_datetime), unique=True)
