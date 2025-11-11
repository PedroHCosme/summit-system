"""
Gerenciador de banco de dados SQLite.
Responsável por toda a comunicação com o banco de dados.
"""
import sqlite3
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from src.core.models import Pessoa


class DatabaseManager:
    """Gerencia todas as operações com o banco de dados SQLite."""
    
    def __init__(self, db_path: str = "gym_database.db"):
        """
        Inicializa o gerenciador de banco de dados.
        
        Args:
            db_path: Caminho para o arquivo do banco de dados
        """
        # O caminho do banco de dados agora é relativo à raiz do projeto
        project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.db_path = os.path.join(project_dir, db_path)
        
        self.connection = None
    
    def connect(self) -> bool:
        """
        Cria a conexão com o banco de dados.
        
        Returns:
            True se a conexão foi bem-sucedida, False caso contrário
        """
        try:
            # check_same_thread=False permite uso da conexão em múltiplas threads
            # Isso é seguro para nossa aplicação read-only
            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False
            )
            self.connection.row_factory = sqlite3.Row  # Permite acessar colunas por nome
            return True
        except Exception as e:
            print(f"Erro ao conectar ao banco de dados: {e}")
            return False
    
    def create_tables(self) -> bool:
        """
        Cria as tabelas do banco de dados se não existirem.
        
        Returns:
            True se as tabelas foram criadas com sucesso, False caso contrário
        """
        if not self.connection:
            return False
        try:
            cursor = self.connection.cursor()
            
            # Tabela de membros
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS membros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    plano TEXT,
                    vencimento_plano TEXT,
                    estado_plano TEXT,
                    data_nascimento TEXT,
                    whatsapp TEXT,
                    genero TEXT,
                    frequencia TEXT,
                    calcado TEXT,
                    email TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de frequência (check-ins)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS frequencia (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    member_id INTEGER NOT NULL,
                    checkin_datetime TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (member_id) REFERENCES membros (id)
                )
            """)
            
            # Tabela de pagamentos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pagamentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    member_id INTEGER,
                    data_pagamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tipo_transacao TEXT NOT NULL,
                    descricao TEXT,
                    valor REAL NOT NULL,
                    metodo_pagamento TEXT,
                    nova_data_vencimento TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (member_id) REFERENCES membros (id)
                )
            """)
            
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Erro ao criar tabelas: {e}")
            return False
    
    def recreate_tables(self) -> bool:
        """
        Apaga as tabelas existentes e as cria novamente.
        Garante um estado limpo para a migração.

        Returns:
            True se a operação foi bem-sucedida, False caso contrário
        """
        if not self.connection:
            return False
        try:
            cursor = self.connection.cursor()
            
            print("    - Apagando tabela 'pagamentos' (se existir)...")
            cursor.execute("DROP TABLE IF EXISTS pagamentos")
            
            print("    - Apagando tabela 'frequencia' (se existir)...")
            cursor.execute("DROP TABLE IF EXISTS frequencia")
            
            print("    - Apagando tabela 'membros' (se existir)...")
            cursor.execute("DROP TABLE IF EXISTS membros")
            
            self.connection.commit()
            
            # Agora, chama o método existente para criar as tabelas limpas
            return self.create_tables()
            
        except Exception as e:
            print(f"Erro ao recriar tabelas: {e}")
            return False

    
    def add_member(self, pessoa_obj: Pessoa) -> Optional[int]:
        """
        Adiciona um novo membro ao banco de dados.
        
        Args:
            pessoa_obj: Objeto Pessoa a ser inserido
            
        Returns:
            ID do novo membro ou None se houver erro
        """
        if not self.connection:
            return None
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                INSERT INTO membros (
                    nome, plano, vencimento_plano, estado_plano,
                    data_nascimento, whatsapp, genero, frequencia, calcado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pessoa_obj.nome,
                pessoa_obj.plano,
                pessoa_obj.vencimento_plano,
                pessoa_obj.estado_plano,
                pessoa_obj.data_nascimento.strftime('%d/%m/%Y') if pessoa_obj.data_nascimento else None,
                pessoa_obj.whatsapp,
                pessoa_obj.genero,
                pessoa_obj.frequencia,
                pessoa_obj.calcado
            ))
            
            self.connection.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Erro ao adicionar membro: {e}")
            return None
    
    def add_member(self, member_data: Dict[str, Any]) -> Optional[int]:
        """
        Adiciona um novo membro ao banco de dados.

        Args:
            member_data: Dicionário com os dados do membro.

        Returns:
            O ID do membro recém-criado ou None em caso de erro.
        """
        if not self.connection:
            print("Erro: Conexão com o banco de dados não estabelecida.")
            return None

        # Define o estado do plano como 'ATIVO' por padrão para novos membros
        if 'estado_plano' not in member_data:
            member_data['estado_plano'] = 'ATIVO'

        # Prepara a query de inserção
        columns = ', '.join(member_data.keys())
        placeholders = ', '.join('?' for _ in member_data)
        query = f"INSERT INTO membros ({columns}) VALUES ({placeholders})"
        
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, list(member_data.values()))
            self.connection.commit()
            
            new_id = cursor.lastrowid
            print(f"Novo membro '{member_data.get('nome')}' adicionado com ID: {new_id}")
            return new_id

        except sqlite3.IntegrityError as e:
            print(f"Erro de integridade ao adicionar membro: {e}")
            return None
        except sqlite3.Error as e:
            print(f"Erro ao adicionar membro no banco de dados: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def get_member_by_id(self, member_id: int) -> Optional[Dict[str, Any]]:
        """
        Busca um membro pelo seu ID.
        
        Args:
            member_id: ID do membro
            
        Returns:
            Dicionário com os dados do membro ou None se não encontrado
        """
        if not self.connection:
            return None
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM membros WHERE id = ?", (member_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            print(f"Erro ao buscar membro por ID: {e}")
            return None
    
    def find_members_by_name(self, name_query: str) -> List[Dict[str, Any]]:
        """
        Busca membros por nome (busca parcial).
        
        Args:
            name_query: Nome ou parte do nome a buscar
            
        Returns:
            Lista de dicionários com os dados dos membros encontrados
        """
        if not self.connection:
            return []
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT * FROM membros WHERE nome LIKE ? ORDER BY nome",
                (f"%{name_query}%",)
            )
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Erro ao buscar membros por nome: {e}")
            return []
    
    def get_all_members(self) -> List[Dict[str, Any]]:
        """
        Retorna todos os membros do banco de dados.
        
        Returns:
            Lista de dicionários com os dados de todos os membros
        """
        if not self.connection:
            return []
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM membros ORDER BY nome")
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Erro ao buscar todos os membros: {e}")
            return []
    
    def add_checkin(self, member_id: int, checkin_datetime: datetime) -> Optional[int]:
        """
        Adiciona um registro de check-in na tabela de frequência.
        Para planos Diária, Gympass e Totalpass, registra pagamento automaticamente.
        
        Args:
            member_id: ID do membro
            checkin_datetime: Data e hora do check-in
            
        Returns:
            ID do registro de check-in ou None se houver erro
        """
        if not self.connection:
            return None
        try:
            cursor = self.connection.cursor()
            
            # Inserir check-in
            cursor.execute("""
                INSERT INTO frequencia (member_id, checkin_datetime)
                VALUES (?, ?)
            """, (member_id, checkin_datetime.strftime('%Y-%m-%d %H:%M:%S')))
            
            checkin_id = cursor.lastrowid
            
            # Buscar plano do membro para verificar se precisa registrar pagamento
            cursor.execute("SELECT plano, nome FROM membros WHERE id = ?", (member_id,))
            result = cursor.fetchone()
            
            if result:
                member_data = dict(result)
                plano = member_data.get('plano', '')
                nome = member_data.get('nome', '')
                
                # Verificar se é um plano que gera pagamento por check-in
                from src.config import PLANOS_PAGAMENTO_POR_CHECKIN
                
                if plano in PLANOS_PAGAMENTO_POR_CHECKIN:
                    valor = PLANOS_PAGAMENTO_POR_CHECKIN[plano]
                    
                    # Registrar pagamento automaticamente
                    self.add_payment(
                        member_id=member_id,
                        data_pagamento=checkin_datetime,
                        tipo_transacao=plano,
                        descricao=f"Check-in - {plano}",
                        valor=valor,
                        metodo_pagamento="Check-in"
                    )
                    
                    print(f"💰 Pagamento registrado: {nome} - {plano} - R$ {valor:.2f}")
            
            self.connection.commit()
            return checkin_id
        except Exception as e:
            print(f"Erro ao adicionar check-in: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def delete_checkin(self, checkin_id: int) -> bool:
        """
        Remove um registro de check-in da tabela de frequência.
        
        Args:
            checkin_id: ID do check-in a ser removido
            
        Returns:
            True se a exclusão foi bem-sucedida, False caso contrário
        """
        if not self.connection:
            return False
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                DELETE FROM frequencia
                WHERE id = ?
            """, (checkin_id,))
            
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Erro ao deletar check-in: {e}")
            return False
    
    # ========================================================================
    # MÉTODOS DE GESTÃO FINANCEIRA
    # ========================================================================
    
    def add_payment(
        self,
        member_id: Optional[int],
        valor: float,
        tipo_transacao: str,
        descricao: str = "",
        metodo_pagamento: str = "",
        nova_data_vencimento: Optional[str] = None,
        data_pagamento: Optional[datetime] = None
    ) -> Optional[int]:
        """
        Registra um novo pagamento no sistema.
        
        Args:
            member_id: ID do membro (None para vendas sem membro específico)
            valor: Valor do pagamento
            tipo_transacao: Tipo da transação (ex: "Renovação Plano", "Diária", "Venda Produto")
            descricao: Descrição detalhada (ex: "Plano Mensal", "Sapatilha X")
            metodo_pagamento: Método de pagamento (ex: "PIX", "Cartão", "Dinheiro")
            nova_data_vencimento: Nova data de vencimento (apenas para renovações)
            data_pagamento: Data e hora do pagamento (usa data atual se None)
            
        Returns:
            ID do pagamento registrado ou None se houver erro
        """
        if not self.connection:
            return None
        
        try:
            cursor = self.connection.cursor()
            
            # Usa a data atual se não fornecida
            if data_pagamento is None:
                data_pagamento = datetime.now()
            
            cursor.execute("""
                INSERT INTO pagamentos (
                    member_id, data_pagamento, tipo_transacao, descricao,
                    valor, metodo_pagamento, nova_data_vencimento
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                member_id,
                data_pagamento.strftime('%Y-%m-%d %H:%M:%S'),
                tipo_transacao,
                descricao,
                valor,
                metodo_pagamento,
                nova_data_vencimento
            ))
            
            self.connection.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Erro ao registrar pagamento: {e}")
            return None
    
    def get_financial_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Obtém um resumo financeiro para um período.
        
        Args:
            start_date: Data inicial (None para desde o início)
            end_date: Data final (None para até hoje)
            
        Returns:
            Dicionário com total_receita, total_transacoes, ticket_medio
        """
        if not self.connection:
            return {'total_receita': 0.0, 'total_transacoes': 0, 'ticket_medio': 0.0}
        
        try:
            cursor = self.connection.cursor()
            
            # Construir query com filtros de data
            query = "SELECT SUM(valor) as total, COUNT(*) as count FROM pagamentos WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND data_pagamento >= ?"
                params.append(start_date.strftime('%Y-%m-%d %H:%M:%S'))
            
            if end_date:
                query += " AND data_pagamento <= ?"
                params.append(end_date.strftime('%Y-%m-%d %H:%M:%S'))
            
            cursor.execute(query, params)
            result = cursor.fetchone()
            
            total_receita = result['total'] if result['total'] else 0.0
            total_transacoes = result['count'] if result['count'] else 0
            ticket_medio = total_receita / total_transacoes if total_transacoes > 0 else 0.0
            
            return {
                'total_receita': total_receita,
                'total_transacoes': total_transacoes,
                'ticket_medio': ticket_medio
            }
        except Exception as e:
            print(f"Erro ao obter resumo financeiro: {e}")
            return {'total_receita': 0.0, 'total_transacoes': 0, 'ticket_medio': 0.0}
    
    def get_revenue_breakdown(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtém a receita agrupada por tipo de transação (ideal para gráficos).
        
        Args:
            start_date: Data inicial (None para desde o início)
            end_date: Data final (None para até hoje)
            
        Returns:
            Lista de dicionários com tipo_transacao, total_valor, quantidade
        """
        if not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            
            query = """
                SELECT 
                    tipo_transacao,
                    SUM(valor) as total_valor,
                    COUNT(*) as quantidade
                FROM pagamentos
                WHERE 1=1
            """
            params = []
            
            if start_date:
                query += " AND data_pagamento >= ?"
                params.append(start_date.strftime('%Y-%m-%d %H:%M:%S'))
            
            if end_date:
                query += " AND data_pagamento <= ?"
                params.append(end_date.strftime('%Y-%m-%d %H:%M:%S'))
            
            query += " GROUP BY tipo_transacao ORDER BY total_valor DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Erro ao obter breakdown de receita: {e}")
            return []
    
    def get_transactions_in_range(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Lista todas as transações em um período.
        
        Args:
            start_date: Data inicial (None para desde o início)
            end_date: Data final (None para até hoje)
            limit: Número máximo de transações a retornar
            
        Returns:
            Lista de dicionários com dados das transações
        """
        if not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            
            query = """
                SELECT 
                    p.*,
                    m.nome as member_nome
                FROM pagamentos p
                LEFT JOIN membros m ON p.member_id = m.id
                WHERE 1=1
            """
            params = []
            
            if start_date:
                query += " AND p.data_pagamento >= ?"
                params.append(start_date.strftime('%Y-%m-%d %H:%M:%S'))
            
            if end_date:
                query += " AND p.data_pagamento <= ?"
                params.append(end_date.strftime('%Y-%m-%d %H:%M:%S'))
            
            query += " ORDER BY p.data_pagamento DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Erro ao obter transações: {e}")
            return []
    
    def get_member_payment_history(self, member_id: int) -> List[Dict[str, Any]]:
        """
        Obtém todo o histórico de pagamentos de um membro.
        
        Args:
            member_id: ID do membro
            
        Returns:
            Lista de dicionários com dados dos pagamentos do membro
        """
        if not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                SELECT *
                FROM pagamentos
                WHERE member_id = ?
                ORDER BY data_pagamento DESC
            """, (member_id,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Erro ao obter histórico de pagamentos do membro: {e}")
            return []
    
    def get_members_by_birthday_month(self, month: int) -> List[Dict[str, Any]]:
        """
        Busca membros que fazem aniversário em um mês específico.
        Usa SQL para filtrar diretamente no banco de dados.
        
        Args:
            month: Número do mês (1-12)
            
        Returns:
            Lista de dicionários com os dados dos membros
        """
        if not self.connection:
            return []
        try:
            cursor = self.connection.cursor()
            
            # Query SQL que extrai o mês da data de nascimento
            # Suporta diferentes formatos de data: DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD
            cursor.execute("""
                SELECT * FROM membros
                WHERE 
                    -- Formato DD/MM/YYYY ou DD-MM-YYYY
                    (CAST(SUBSTR(data_nascimento, 4, 2) AS INTEGER) = ?)
                    OR
                    -- Formato YYYY-MM-DD
                    (CAST(SUBSTR(data_nascimento, 6, 2) AS INTEGER) = ?)
                ORDER BY 
                    -- Ordena pelo dia do mês
                    CAST(SUBSTR(data_nascimento, 1, 2) AS INTEGER)
            """, (month, month))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Erro ao buscar aniversariantes do mês: {e}")
            return []
    
    def update_member(
        self, 
        member_id: int,
        plano: Optional[str] = None,
        frequencia: Optional[str] = None,
        estado_plano: Optional[str] = None,
        vencimento_plano: Optional[str] = None,
        whatsapp: Optional[str] = None,
        genero: Optional[str] = None,
        calcado: Optional[str] = None
    ) -> bool:
        """
        Atualiza os dados de um membro existente.
        Atualiza apenas os campos que forem fornecidos (não-None).
        
        Args:
            member_id: ID do membro a ser atualizado
            plano: Novo plano (opcional)
            frequencia: Nova frequência (opcional)
            estado_plano: Novo estado do plano (opcional)
            vencimento_plano: Novo vencimento do plano (opcional)
            whatsapp: Novo WhatsApp (opcional)
            genero: Novo gênero (opcional)
            calcado: Novo calçado (opcional)
            
        Returns:
            True se a atualização foi bem-sucedida, False caso contrário
        """
        if not self.connection:
            return False
        try:
            cursor = self.connection.cursor()
            
            # Construir query dinamicamente apenas com os campos fornecidos
            updates = []
            values = []
            
            if plano is not None:
                updates.append("plano = ?")
                values.append(plano)
            
            if frequencia is not None:
                updates.append("frequencia = ?")
                values.append(frequencia)
            
            if estado_plano is not None:
                updates.append("estado_plano = ?")
                values.append(estado_plano)
            
            if vencimento_plano is not None:
                updates.append("vencimento_plano = ?")
                values.append(vencimento_plano)
            
            if whatsapp is not None:
                updates.append("whatsapp = ?")
                values.append(whatsapp)
            
            if genero is not None:
                updates.append("genero = ?")
                values.append(genero)
            
            if calcado is not None:
                updates.append("calcado = ?")
                values.append(calcado)
            
            # Sempre atualizar o timestamp
            updates.append("updated_at = CURRENT_TIMESTAMP")
            
            # Se não há nada para atualizar, retornar True
            if not values:
                return True
            
            # Adicionar o member_id no final dos valores
            values.append(member_id)
            
            # Executar a query
            query = f"UPDATE membros SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, values)
            
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Erro ao atualizar membro: {e}")
            return False
    
    def update_member_from_dict(
        self, 
        member_data: Dict[str, Any], 
        register_payment: bool = False,
        metodo_pagamento: str = ""
    ) -> bool:
        """
        Atualiza os dados de um membro usando um dicionário.
        Opcionalmente registra um pagamento se houver mudança de plano.
        
        Args:
            member_data: Dicionário com os dados do membro (deve incluir 'id')
            register_payment: Se True, registra pagamento ao atualizar plano/vencimento
            metodo_pagamento: Método de pagamento usado
            
        Returns:
            True se a atualização foi bem-sucedida, False caso contrário
        """
        if not self.connection or 'id' not in member_data:
            return False
        
        try:
            cursor = self.connection.cursor()
            member_id = member_data['id']
            
            # Buscar dados atuais do membro para detectar mudanças
            old_data = None
            if register_payment:
                cursor.execute("SELECT plano, vencimento_plano FROM membros WHERE id = ?", (member_id,))
                row = cursor.fetchone()
                if row:
                    old_data = dict(row)
            
            # Construir query dinamicamente com todos os campos fornecidos
            updates = []
            values = []
            
            # Mapeamento de campos do dicionário para colunas do banco
            field_mapping = {
                'nome': 'nome',
                'plano': 'plano',
                'vencimento_plano': 'vencimento_plano',
                'estado_plano': 'estado_plano',
                'data_nascimento': 'data_nascimento',
                'whatsapp': 'whatsapp',
                'genero': 'genero',
                'frequencia': 'frequencia',
                'calcado': 'calcado',
                'email': 'email'
            }
            
            # Adicionar campos que estão no dicionário
            for field_key, column_name in field_mapping.items():
                if field_key in member_data:
                    value = member_data[field_key]
                    # Permitir None ou string vazia para limpar campos
                    updates.append(f"{column_name} = ?")
                    values.append(value if value else None)
            
            # Sempre atualizar o timestamp
            updates.append("updated_at = CURRENT_TIMESTAMP")
            
            # Se não há nada para atualizar, retornar True
            if not values:
                return True
            
            # Adicionar o member_id no final dos valores
            values.append(member_id)
            
            # Executar a query
            query = f"UPDATE membros SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, values)
            
            self.connection.commit()
            
            # Registrar pagamento se solicitado e houver mudança de plano/vencimento
            if register_payment and old_data:
                new_plano = member_data.get('plano')
                new_vencimento = member_data.get('vencimento_plano')
                old_plano = old_data.get('plano')
                old_vencimento = old_data.get('vencimento_plano')
                
                # Detectar se houve mudança significativa
                plano_changed = new_plano and new_plano != old_plano
                vencimento_changed = new_vencimento and new_vencimento != old_vencimento
                
                if plano_changed or vencimento_changed:
                    # Importar config para buscar preços
                    from src.config import PLANOS_PRECOS, PLANOS_PAGAMENTO_POR_CHECKIN
                    
                    # Determinar tipo de transação e descrição
                    if plano_changed and new_plano:
                        tipo_transacao = f"Mudança de Plano"
                        descricao = f"De '{old_plano}' para '{new_plano}'"
                        valor = PLANOS_PRECOS.get(new_plano, 0.0)
                    elif new_plano:
                        tipo_transacao = f"Renovação Plano"
                        descricao = f"Plano: {new_plano}"
                        valor = PLANOS_PRECOS.get(new_plano, 0.0)
                    else:
                        return cursor.rowcount > 0
                    
                    # Só registrar pagamento se valor > 0 OU se for explicitamente Cortesia
                    # Planos como Gympass/Totalpass não geram receita na renovação (apenas por check-in)
                    if valor > 0 or new_plano == "Cortesia":
                        # Registrar o pagamento
                        self.add_payment(
                            member_id=member_id,
                            valor=valor,
                            tipo_transacao=tipo_transacao,
                            descricao=descricao,
                            metodo_pagamento=metodo_pagamento,
                            nova_data_vencimento=new_vencimento
                        )
                        print(f"💰 Pagamento registrado: {tipo_transacao} - R$ {valor:.2f}")
                        
                        # Informar planos pagos por check-in
                        if new_plano in PLANOS_PAGAMENTO_POR_CHECKIN and valor == 0:
                            print(f"ℹ️  Plano '{new_plano}' registrado (receita gerada por check-in)")

            
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Erro ao atualizar membro: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def delete_member(self, member_id: int) -> bool:
        """
        Deleta um membro do banco de dados.
        
        Args:
            member_id: ID do membro a ser deletado
            
        Returns:
            True se deletado com sucesso, False caso contrário
        """
        if not self.connection:
            print("Erro: Conexão não estabelecida")
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # Primeiro, deletar todos os check-ins do membro
            cursor.execute("DELETE FROM checkins WHERE member_id = ?", (member_id,))
            
            # Deletar todos os pagamentos do membro
            cursor.execute("DELETE FROM pagamentos WHERE membro_id = ?", (member_id,))
            
            # Finalmente, deletar o membro
            cursor.execute("DELETE FROM membros WHERE id = ?", (member_id,))
            
            self.connection.commit()
            
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Erro ao deletar membro: {e}")
            import traceback
            traceback.print_exc()
            if self.connection:
                self.connection.rollback()
            return False
    
    def get_member_checkin_history(self, member_id: int) -> List[Dict[str, Any]]:
        """
        Busca todo o histórico de check-ins de um membro.
        
        Args:
            member_id: ID do membro
            
        Returns:
            Lista de dicionários com os dados dos check-ins, ordenados do mais recente ao mais antigo.
            Cada dicionário contém: id, member_id, checkin_datetime, created_at
        """
        if not self.connection:
            return []
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                SELECT 
                    id,
                    member_id,
                    checkin_datetime,
                    created_at
                FROM frequencia
                WHERE member_id = ?
                ORDER BY checkin_datetime DESC
            """, (member_id,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Erro ao buscar histórico de check-ins: {e}")
            return []

    def get_checkins_today(self) -> int:
        """
        Conta o número de check-ins realizados hoje.
        
        Returns:
            Número de check-ins de hoje.
        """
        if not self.connection:
            return 0
        try:
            cursor = self.connection.cursor()
            
            today_str = datetime.now().strftime('%Y-%m-%d')
            
            cursor.execute("""
                SELECT COUNT(*)
                FROM frequencia
                WHERE DATE(checkin_datetime) = ?
            """, (today_str,))
            
            count = cursor.fetchone()[0]
            return count
        except Exception as e:
            print(f"Erro ao contar check-ins de hoje: {e}")
            return 0

    def get_checkins_today_details(self) -> List[Dict[str, Any]]:
        """
        Busca os detalhes de todos os check-ins realizados hoje.
        
        Returns:
            Lista de dicionários com dados dos check-ins de hoje (nome, plano, data).
        """
        try:
            if not self.connection:
                print("Erro: Conexão com o banco de dados não estabelecida.")
                return []
                
            cursor = self.connection.cursor()
            
            today_str = datetime.now().strftime('%Y-%m-%d')
            
            cursor.execute("""
                SELECT 
                    m.nome,
                    m.plano,
                    f.checkin_datetime
                FROM frequencia f
                JOIN membros m ON f.member_id = m.id
                WHERE DATE(f.checkin_datetime) = ?
                ORDER BY f.checkin_datetime DESC
            """, (today_str,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Erro ao buscar detalhes dos check-ins de hoje: {e}")
            return []

    def get_last_checkins(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Busca os últimos check-ins realizados.
        
        Args:
            limit: Número máximo de check-ins a retornar
            
        Returns:
            Lista de dicionários com dados dos últimos check-ins (membro e data)
        """
        try:
            if not self.connection:
                print("Erro: Conexão com o banco de dados não estabelecida.")
                return []

            cursor = self.connection.cursor()
            
            cursor.execute("""
                SELECT 
                    m.nome,
                    f.checkin_datetime
                FROM frequencia f
                JOIN membros m ON f.member_id = m.id
                ORDER BY f.checkin_datetime DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Erro ao buscar últimos check-ins: {e}")
            return []
    
    def close(self):
        """Fecha a conexão com o banco de dados."""
        if self.connection:
            self.connection.close()
            self.connection = None

    def update_expired_plans(self):
        """
        Atualiza o estado do plano para 'INATIVO' para membros cujo plano expirou.
        A verificação é feita com base na data atual.
        """
        if not self.connection:
            print("Erro: Conexão com o banco de dados não estabelecida.")
            return 0

        cursor = None
        try:
            cursor = self.connection.cursor()
            
            # A data no banco está como 'DD/MM/AAAA', precisamos converter para 'AAAA-MM-DD' para comparar
            # Usamos substr para reordenar a data para o formato YYYY-MM-DD
            # A data de hoje já está em 'YYYY-MM-DD'
            today_str = datetime.now().strftime('%Y-%m-%d')
            
            query = """
                UPDATE membros
                SET estado_plano = 'INATIVO'
                WHERE vencimento_plano IS NOT NULL 
                  AND vencimento_plano != ''
                  AND substr(vencimento_plano, 7, 4) || '-' || substr(vencimento_plano, 4, 2) || '-' || substr(vencimento_plano, 1, 2) < ?
                  AND estado_plano = 'ATIVO';
            """
            
            cursor.execute(query, (today_str,))
            self.connection.commit()
            
            updated_rows = cursor.rowcount
            if updated_rows > 0:
                print(f"Planos de {updated_rows} membro(s) foram atualizados para 'INATIVO'.")
            return updated_rows

        except sqlite3.Error as e:
            print(f"Erro ao atualizar planos expirados no banco de dados: {e}")
            return 0
        finally:
            if cursor:
                cursor.close()
