"""
Modelo de dados para Pessoa/Membro.
Implementa conceitos de OOP: Encapsulamento, Properties, Métodos de classe.
"""
from datetime import datetime
from typing import Optional


class Pessoa:
    """
    Representa uma pessoa com seus dados pessoais.
    
    Atributos:
        nome (str): Nome completo da pessoa
        data_nascimento (datetime): Data de nascimento
        whatsapp (str): Número de WhatsApp
        plano (str): Plano contratado
    """
    
    def __init__(
        self, 
        nome: str, 
        data_nascimento: Optional[datetime],
        whatsapp: str = "",
        plano: str = "N/A",
        vencimento_plano: str = "",
        estado_plano: str = "",
        genero: str = "",
        frequencia: str = "",
        calcado: str = ""
    ):
        """
        Inicializa uma Pessoa.
        
        Args:
            nome: Nome completo
            data_nascimento: Data de nascimento como datetime
            whatsapp: Número de WhatsApp (opcional)
            plano: Plano contratado (opcional)
            vencimento_plano: Data de vencimento do plano (opcional)
            estado_plano: Estado do plano (Ativo/Inativo) (opcional)
            genero: Gênero do membro (opcional)
            frequencia: Frequência de treinos (opcional)
            calcado: Numeração de calçado (opcional)
        """
        self._nome = nome.strip()
        self._data_nascimento = data_nascimento
        self._whatsapp = whatsapp.strip()
        self._plano = plano.strip()
        self._vencimento_plano = vencimento_plano.strip()
        self._estado_plano = estado_plano.strip()
        self._genero = genero.strip()
        self._frequencia = frequencia.strip()
        self._calcado = calcado.strip()
    
    # --- Getters (Properties) ---
    
    @property
    def nome(self) -> str:
        """Retorna o nome da pessoa."""
        return self._nome
    
    @property
    def data_nascimento(self) -> Optional[datetime]:
        """Retorna a data de nascimento."""
        return self._data_nascimento
    
    @property
    def whatsapp(self) -> str:
        """Retorna o número de WhatsApp."""
        return self._whatsapp
    
    @property
    def plano(self) -> str:
        """Retorna o plano."""
        return self._plano
    
    @property
    def vencimento_plano(self) -> str:
        """Retorna o vencimento do plano."""
        return self._vencimento_plano

    @property
    def estado_plano(self) -> str:
        """Retorna o estado do plano."""
        return self._estado_plano

    @property
    def genero(self) -> str:
        """Retorna o gênero."""
        return self._genero

    @property
    def frequencia(self) -> str:
        """Retorna a frequência de treinos."""
        return self._frequencia

    @property
    def calcado(self) -> str:
        """Retorna a numeração do calçado."""
        return self._calcado

    @property
    def idade(self) -> Optional[int]:
        """
        Calcula e retorna a idade atual da pessoa.
        
        Returns:
            Idade em anos completos ou None se não houver data de nascimento
        """
        if not self._data_nascimento:
            return None
            
        hoje = datetime.now()
        idade = hoje.year - self._data_nascimento.year
        
        # Ajusta se ainda não fez aniversário este ano
        if (hoje.month, hoje.day) < (self._data_nascimento.month, self._data_nascimento.day):
            idade -= 1
        
        return idade
    
    @property
    def dia_aniversario(self) -> Optional[int]:
        """Retorna o dia do aniversário."""
        return self._data_nascimento.day if self._data_nascimento else None
    
    @property
    def mes_aniversario(self) -> Optional[int]:
        """Retorna o mês do aniversário."""
        return self._data_nascimento.month if self._data_nascimento else None
    
    @property
    def data_nascimento_formatada(self) -> str:
        """Retorna a data de nascimento formatada (dd/mm/aaaa)."""
        if not self._data_nascimento:
            return "N/A"
        return self._data_nascimento.strftime('%d/%m/%Y')
    
    # --- Setters ---
    
    @whatsapp.setter
    def whatsapp(self, valor: str):
        """Define um novo número de WhatsApp."""
        self._whatsapp = valor.strip()
    
    @plano.setter
    def plano(self, valor: str):
        """Define um novo plano."""
        self._plano = valor.strip()

    @vencimento_plano.setter
    def vencimento_plano(self, valor: str):
        """Define um novo vencimento de plano."""
        self._vencimento_plano = valor.strip()

    @estado_plano.setter
    def estado_plano(self, valor: str):
        """Define um novo estado de plano."""
        self._estado_plano = valor.strip()

    @genero.setter
    def genero(self, valor: str):
        """Define um novo gênero."""
        self._genero = valor.strip()

    @frequencia.setter
    def frequencia(self, valor: str):
        """Define uma nova frequência."""
        self._frequencia = valor.strip()

    @calcado.setter
    def calcado(self, valor: str):
        """Define uma nova numeração de calçado."""
        self._calcado = valor.strip()
    
    # --- Métodos de Negócio ---
    
    def faz_aniversario_no_mes(self, mes: int) -> bool:
        """
        Verifica se a pessoa faz aniversário no mês especificado.
        
        Args:
            mes: Número do mês (1-12)
            
        Returns:
            True se faz aniversário no mês, False caso contrário
        """
        if not self._data_nascimento:
            return False
        return self._data_nascimento.month == mes
    
    def tem_whatsapp(self) -> bool:
        """Verifica se a pessoa tem WhatsApp cadastrado."""
        return bool(self._whatsapp)
    
    def dias_ate_aniversario(self) -> Optional[int]:
        """
        Calcula quantos dias faltam até o próximo aniversário.
        
        Returns:
            Número de dias até o aniversário ou None se não houver data
        """
        if not self._data_nascimento:
            return None

        hoje = datetime.now()
        proximo_aniversario = datetime(
            hoje.year,
            self._data_nascimento.month,
            self._data_nascimento.day
        )
        
        # Se já passou este ano, considera o próximo ano
        if proximo_aniversario < hoje:
            proximo_aniversario = datetime(
                hoje.year + 1,
                self._data_nascimento.month,
                self._data_nascimento.day
            )
        
        return (proximo_aniversario - hoje).days
    
    # --- Métodos de Representação ---
    
    def __str__(self) -> str:
        """Representação em string da pessoa."""
        idade_str = f"{self.idade} anos" if self.idade is not None else "Idade não informada"
        return f"{self._nome} ({idade_str})"
    
    def __repr__(self) -> str:
        """Representação técnica da pessoa."""
        return (f"Pessoa(nome='{self._nome}', "
                f"data_nascimento={self.data_nascimento_formatada}, "
                f"whatsapp='{self._whatsapp}')")
    
    def __eq__(self, other) -> bool:
        """Verifica igualdade entre duas pessoas."""
        if not isinstance(other, Pessoa):
            return False
        return (self._nome == other._nome and 
                self._data_nascimento == other._data_nascimento)
    
    def __lt__(self, other) -> bool:
        """Compara pessoas por dia de aniversário (para ordenação)."""
        if not isinstance(other, Pessoa):
            return NotImplemented
        
        dia_self = self.dia_aniversario
        dia_other = other.dia_aniversario

        # Se ambos não têm aniversário, são considerados iguais
        if dia_self is None and dia_other is None:
            return False
        # Se apenas 'self' não tem aniversário, é considerado "menor" para fins de ordenação
        if dia_self is None:
            return True
        # Se apenas 'other' não tem aniversário, 'self' é considerado "maior"
        if dia_other is None:
            return False
        
        # Se ambos têm aniversário, compara os dias
        return dia_self < dia_other
    
    # --- Métodos de Conversão ---
    
    def to_dict(self) -> dict:
        """
        Converte a pessoa para um dicionário.
        
        Returns:
            Dicionário com todos os dados da pessoa
        """
        dias_ate = self.dias_ate_aniversario()
        return {
            'nome': self._nome,
            'data_nascimento': self.data_nascimento_formatada,
            'idade': self.idade,
            'whatsapp': self._whatsapp,
            'plano': self._plano,
            'vencimento_plano': self._vencimento_plano,
            'estado_plano': self._estado_plano,
            'genero': self._genero,
            'frequencia': self._frequencia,
            'calcado': self._calcado,
            'dia_aniversario': self.dia_aniversario,
            'mes_aniversario': self.mes_aniversario,
            'dias_ate_aniversario': dias_ate if dias_ate is not None else float('inf')
        }
    
    @classmethod
    def from_dict(cls, dados: dict) -> Optional['Pessoa']:
        """
        Cria uma Pessoa a partir de um dicionário.
        
        Args:
            dados: Dicionário com os dados da pessoa
            
        Returns:
            Instância de Pessoa ou None se dados inválidos
        """
        try:
            # Tenta parsear a data em diferentes formatos
            data_str = dados.get('data_nascimento', '')
            data_nascimento = None
            
            for formato in ('%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d'):
                try:
                    data_nascimento = datetime.strptime(data_str, formato)
                    break
                except ValueError:
                    continue
            
            if not data_nascimento:
                return None
            
            return cls(
                nome=dados.get('nome', ''),
                data_nascimento=data_nascimento,
                whatsapp=dados.get('whatsapp', ''),
                plano=dados.get('plano', 'N/A'),
                vencimento_plano=dados.get('vencimento_plano', ''),
                estado_plano=dados.get('estado_plano', ''),
                genero=dados.get('genero', ''),
                frequencia=dados.get('frequencia', ''),
                calcado=dados.get('calcado', '')
            )
        except Exception:
            return None


# Alias para compatibilidade com código existente
Aniversariante = Pessoa