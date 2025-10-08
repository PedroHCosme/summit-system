# Sistema de Gestão de Membros

Aplicação para gerenciamento de membros com integração ao Google Sheets.

## Funcionalidades

### 1. Aniversariantes do Mês
- Exibe lista de membros que fazem aniversário no mês atual
- Mostra nome, data de nascimento, idade, plano e link do WhatsApp
- Ordenação automática por dia do aniversário

### 2. Buscar Membro
- Busca por nome (busca parcial, não precisa digitar o nome completo)
- Busca por CPF (com ou sem formatação)
- Exibe todos os dados do membro encontrado

## Estrutura do Projeto

```
src/
├── gui.py                      # Interface gráfica principal
├── config.py                   # Configurações (IDs, colunas)
├── models.py                   # Modelo de dados (Pessoa)
├── aniversariantes_manager.py  # Lógica de aniversariantes
├── member_search_service.py    # Lógica de busca de membros
├── google_sheets_service.py    # Integração com Google Sheets
├── html_formatter.py           # Formatação HTML
├── utils.py                    # Funções utilitárias
├── styles.py                   # Estilos CSS da interface
└── credentials.json            # Credenciais do Google (não versionado)
```

## Configuração

### Colunas da Planilha
As colunas utilizadas estão definidas em `config.py`:
- `COL_NOME` (coluna A): Nome do membro
- `COL_PLANO` (coluna B): Plano contratado
- `COL_CPF` (coluna C): CPF do membro
- `COL_DATA_NASCIMENTO` (coluna BR): Data de nascimento
- `COL_WHATSAPP` (coluna BU): Telefone WhatsApp

### Google Sheets
1. Certifique-se de ter o arquivo `credentials.json` na pasta `src/`
2. O ID da planilha está configurado em `config.py`

## Execução

Para executar a aplicação:

```bash
python run.py
```

## Menu de Navegação

A aplicação possui um menu superior com as seguintes opções:

**Membros**
- Aniversariantes: Exibe aniversariantes do mês
- Buscar Membro: Permite buscar por nome ou CPF

## Requisitos

- Python 3.12+
- PyQt6
- google-auth
- google-api-python-client
- (outros requisitos em requirements.txt)
