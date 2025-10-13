"""
Gerenciador de banco de dados SQLite.
Responsável por toda a comunicação com o banco de dados.
"""
import sqlite3
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from models import Pessoa


class DatabaseManager:
    """Gerencia todas as operações com o banco de dados SQLite."""
    
    def __init__(self, db_path: str = "gym_database.db"):
        """
        Inicializa o gerenciador de banco de dados.
        
        Args:
            db_path: Caminho para o arquivo do banco de dados
        """
        # Se o caminho for relativo, usa o diretório pai de src/
        if not os.path.isabs(db_path):
            # Pega o diretório deste arquivo (src/)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Sobe um nível para o diretório do projeto
            project_dir = os.path.dirname(current_dir)
            # Cria o caminho completo
            self.db_path = os.path.join(project_dir, db_path)
        else:
            self.db_path = db_path
        
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
        try:
            cursor = self.connection.cursor()
            
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
    
    def get_member_by_id(self, member_id: int) -> Optional[Dict[str, Any]]:
        """
        Busca um membro pelo seu ID.
        
        Args:
            member_id: ID do membro
            
        Returns:
            Dicionário com os dados do membro ou None se não encontrado
        """
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
        
        Args:
            member_id: ID do membro
            checkin_datetime: Data e hora do check-in
            
        Returns:
            ID do registro de check-in ou None se houver erro
        """
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                INSERT INTO frequencia (member_id, checkin_datetime)
                VALUES (?, ?)
            """, (member_id, checkin_datetime.strftime('%Y-%m-%d %H:%M:%S')))
            
            self.connection.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Erro ao adicionar check-in: {e}")
            return None
    
    def get_members_by_birthday_month(self, month: int) -> List[Dict[str, Any]]:
        """
        Busca membros que fazem aniversário em um mês específico.
        Usa SQL para filtrar diretamente no banco de dados.
        
        Args:
            month: Número do mês (1-12)
            
        Returns:
            Lista de dicionários com os dados dos membros
        """
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
    
    def get_member_checkin_history(self, member_id: int) -> List[Dict[str, Any]]:
        """
        Busca todo o histórico de check-ins de um membro.
        
        Args:
            member_id: ID do membro
            
        Returns:
            Lista de dicionários com os dados dos check-ins, ordenados do mais recente ao mais antigo.
            Cada dicionário contém: id, member_id, checkin_datetime, created_at
        """
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
