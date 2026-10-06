# Summit System - Guia de Instalação

Guia completo para configurar o Summit System em um novo computador.

---

## Pré-requisitos

O computador já deve ter:
- Python 3.10+
- PyQt6 (para a GUI)
- Dependências básicas do sistema

---

## Passo 1: Instalar Dependências do Web Service

```bash
# Navegar até a pasta do projeto
cd /caminho/para/summit-projv2

# Instalar todas as dependências
pip install -r requirements.txt
```

**Dependências do Web Service:**
- `flask` - Framework web
- `gunicorn` - Servidor WSGI (produção)
- `flask-limiter` - Rate limiting
- `sqlalchemy` - ORM do banco de dados

---

## Passo 2: Banco de Dados

O banco `gym_database.db` deve estar na raiz do projeto com os dados existentes.

### Sobre os Planos
As migrações **criam automaticamente** todos os planos base se não existirem:
- Mensal, Trimestral, Semestral, Anual, etc.
- Planos de check-in (Diária, Gympass, Totalpass)
- Planos quota (Voucher, Pacote 10)

> ✅ **Planos existentes NÃO são modificados** - apenas planos faltantes são criados.

> ⚠️ **Importante:** Faça backup do banco de dados antes de atualizar o código.

---

## Passo 3: Testar a Instalação

```bash
# Testar se tudo está funcionando
python -m pytest tests/ -v

# Deve mostrar: "XX passed"
```

---

## Passo 4: Executar o Sistema

```bash
python run.py
```

**O que acontece:**
1. 🌐 Servidor web inicia em `http://localhost:5000`
2. 🖥️ Interface gráfica abre
3. 🔄 Migrações do banco executam automaticamente
4. Ao fechar a GUI, servidor web encerra automaticamente

---

## (Opcional) Passo 5: Configurar Acesso Externo (Cloudflare Tunnel)

Se você precisa de acesso externo (celular, outros computadores):

### 5.1 Instalar Cloudflared
```bash
./setup_tunnel.sh
```

### 5.2a - Conectar a um Tunnel EXISTENTE (recomendado)

Se você já configurou um tunnel em outro computador:

1. Acesse https://one.dash.cloudflare.com/ → **Tunnels**
2. Clique no seu tunnel existente (ex: `summit-academia`)
3. Vá em **Configure** → aba **Connectors**
4. Copie o comando de instalação (algo como `sudo cloudflared service install <TOKEN>`)
5. Execute esse comando no novo computador

> 💡 **Nota:** A configuração do tunnel (rotas, domínios) está salva no Cloudflare, não no computador. Você só precisa instalar o cloudflared e conectar com o token.

### 5.2b - Criar um NOVO Tunnel

Se você precisa criar um tunnel do zero:

1. Acesse https://one.dash.cloudflare.com/
2. Vá em **Access > Tunnels > Create a Tunnel**
3. Escolha um nome (ex: `summit-academia`)
4. Copie o comando de instalação e execute no terminal
5. Configure a rota:
   - **Service:** `http://localhost:5000`
   - **Public hostname:** `academia.seudominio.com`

---

## Verificação Final

| Item | Comando de Teste |
|------|------------------|
| GUI | Fechar e abrir a janela |
| Web | Acessar `http://localhost:5000` no navegador |
| Migrações | Ver "✓ Migrações do banco" no console |
| Banco | `python -c "from src.services.plan_service import get_plan_service; print(get_plan_service().get_plan_names())"` |

---

## Troubleshooting

| Problema | Solução |
|----------|---------|
| `gunicorn: command not found` | `pip install gunicorn` |
| `ModuleNotFoundError: flask` | `pip install -r requirements.txt` |
| Porta 5000 em uso | Encerrar outro processo ou alterar porta |
| Banco vazio | Executar sync ou copiar `gym_database.db` |

---

## Arquivos Importantes

```
summit-projv2/
├── run.py                  # Script principal (GUI + Web)
├── gym_database.db         # Banco de dados SQLite
├── requirements.txt        # Dependências Python
├── src/
│   ├── ui/                 # Interface gráfica (PyQt6)
│   ├── web/                # Serviço web (Flask)
│   ├── services/           # Lógica de negócio
│   └── data/               # Modelos e migrations
└── setup_tunnel.sh         # Instalação do Cloudflare (opcional)
```
