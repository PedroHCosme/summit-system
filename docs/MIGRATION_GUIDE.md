# Guia de Migração de Dados

## Visão Geral

Existem **duas formas** de sincronizar dados do Google Sheets para o banco de dados SQLite local:

### 🖥️ Via Interface Gráfica (Recomendado para usuários)
Execute a sincronização diretamente pela aplicação:
1. Abra a aplicação
2. Menu **Ferramentas → 🔄 Sincronizar com Google Sheets**
3. Acompanhe o progresso em tempo real
4. Visualize relatório completo ao final

📖 **[Veja o guia completo da UI](SYNC_UI_GUIDE.md)**

### ⌨️ Via Linha de Comando (Recomendado para automação)
Execute o script de migração (`scripts/migrate_data.py`) que suporta dois modos:

#### 1. Modo Completo (Padrão)
Recria todas as tabelas do zero, apagando dados existentes.

```bash
python scripts/migrate_data.py
```

**Quando usar:**
- Primeira execução da migração
- Quando houver problemas na estrutura do banco
- Para resetar completamente o banco de dados

⚠️ **Atenção:** Este modo apaga TODOS os dados existentes!

#### 2. Modo Incremental (--append)
Preserva dados existentes e adiciona apenas novos registros.

```bash
python scripts/migrate_data.py --append
```

**Quando usar:**
- Para atualizar o banco com novos check-ins
- Quando não quiser perder dados locais
- Para sincronizações periódicas
- **Mesma funcionalidade da sincronização via UI**

✅ **Vantagens:**
- Preserva histórico existente
- Evita duplicação de check-ins
- Identifica e reutiliza membros existentes

## Funcionalidades

### Transações Atômicas

Ambos os modos agora utilizam transações para garantir atomicidade:

```python
with db_manager.transaction():
    # Todas as operações aqui são atômicas
    db_manager.add_member(...)
    db_manager.add_checkin(...)
```

**Benefícios:**
- Se houver erro, nenhuma alteração parcial é salva (rollback automático)
- Garante consistência dos dados
- Logs de erro detalhados

### Detecção de Duplicatas (Modo Incremental)

No modo `--append`, o sistema:

1. **Membros:** Verifica se o membro já existe pelo nome
   - Se existe: reutiliza o ID existente
   - Se novo: insere no banco

2. **Check-ins:** Verifica se já existe um check-in com mesma data/hora
   - Se existe: ignora (evita duplicação)
   - Se novo: insere no banco

## Exemplos de Uso

### Migração Inicial
```bash
# Primeira vez - cria todo o banco
python scripts/migrate_data.py
```

**Saída esperada:**
```
============================================================
MIGRAÇÃO DE DADOS: Google Sheets → SQLite (COMPLETA)
============================================================

[1/6] Conectando ao Google Sheets...
✓ Conectado ao Google Sheets

[2/6] Conectando ao banco de dados SQLite...
✓ Conectado ao SQLite

[3/6] Modo completo: limpando e recriando tabelas...
✓ Tabelas recriadas com sucesso

...

📊 Resumo:
  • Modo: COMPLETO (recriou tabelas)
  • Membros únicos migrados: 150
  • Total de check-ins: 3420
  • Banco de dados: gym_database.db
```

### Atualização Incremental
```bash
# Adiciona apenas novos dados
python scripts/migrate_data.py --append
```

**Saída esperada:**
```
============================================================
MIGRAÇÃO DE DADOS: Google Sheets → SQLite (INCREMENTAL (--append))
============================================================

[1/6] Conectando ao Google Sheets...
✓ Conectado ao Google Sheets

[2/6] Conectando ao banco de dados SQLite...
✓ Conectado ao SQLite

[3/6] Modo incremental: criando tabelas se não existirem...
✓ Tabelas verificadas/criadas com sucesso

[4/6] Lendo e consolidando dados dos membros...
  → Modo incremental: carregando membros existentes...
  → 150 membros já existentes no banco

[5/6] Inserindo membros consolidados no banco de dados...
✓ Membros processados: 5 novos, 145 existentes

[6/6] Migrando registros de check-in...
✓ 87 novos check-ins migrados (234 duplicados ignorados)

📊 Resumo:
  • Modo: INCREMENTAL (--append)
  • Membros novos: 5
  • Membros existentes: 145
  • Total de membros processados: 150
  • Novos check-ins: 87
  • Check-ins duplicados ignorados: 234
  • Banco de dados: gym_database.db
```

## API de Transações

O `DatabaseManager` agora expõe um context manager para transações:

```python
from src.data.database_manager import DatabaseManager

db = DatabaseManager()
db.connect()

# Uso básico
with db.transaction():
    member_id = db.add_member({'nome': 'João Silva', 'plano': 'Mensal'})
    db.add_checkin(member_id, datetime.now())
    # Se qualquer operação falhar, rollback automático

# Tratamento de erros
try:
    with db.transaction():
        # Operações que podem falhar
        db.add_member(invalid_data)
except Exception as e:
    print(f"Erro: {e}")
    # Transação já foi revertida automaticamente
```

## Fluxo de Execução

### Modo Completo
```
1. Conectar ao Sheets ✓
2. Conectar ao SQLite ✓
3. DROP + CREATE tabelas ✓
4. Consolidar membros do Sheets ✓
5. [TRANSAÇÃO] Inserir TODOS membros ✓
6. [TRANSAÇÃO] Inserir TODOS check-ins ✓
7. Resumo final ✓
```

### Modo Incremental
```
1. Conectar ao Sheets ✓
2. Conectar ao SQLite ✓
3. CREATE IF NOT EXISTS tabelas ✓
4. Consolidar membros do Sheets ✓
5. Carregar membros existentes do DB ✓
6. [TRANSAÇÃO] Inserir apenas NOVOS membros ✓
7. [TRANSAÇÃO] Inserir apenas NOVOS check-ins ✓
8. Resumo com estatísticas incrementais ✓
```

## Tratamento de Erros

### Durante Transação
Se qualquer erro ocorrer dentro de uma transação:
1. Rollback automático é executado
2. Erro é logado com stack trace
3. Script retorna código de saída 1
4. Nenhuma alteração parcial é salva

### Erros Comuns

**"Conexão com o banco de dados não estabelecida"**
- Causa: Falha ao conectar ao SQLite
- Solução: Verificar permissões do diretório

**"Erro ao autenticar no Google Sheets"**
- Causa: Credenciais inválidas ou expiradas
- Solução: Verificar `credentials.json`

**"Transação revertida devido a erro"**
- Causa: Erro durante operação em transação
- Solução: Verificar logs detalhados para identificar problema específico

## Boas Práticas

1. **Use modo incremental para atualizações frequentes:**
   ```bash
   # Em cron job diário
   0 1 * * * cd /path/to/project && python scripts/migrate_data.py --append
   ```

2. **Faça backup antes de migração completa:**
   ```bash
   cp gym_database.db gym_database.db.backup
   python scripts/migrate_data.py
   ```

3. **Monitore logs em produção:**
   ```bash
   python scripts/migrate_data.py --append 2>&1 | tee migration.log
   ```

## Próximos Passos

Melhorias futuras planejadas:
- [ ] Flag `--dry-run` para simular sem aplicar mudanças
- [ ] Filtro por período (ex: `--from-date 2025-01-01`)
- [ ] Validação de dados antes de inserir
- [ ] Relatório detalhado em JSON/CSV
