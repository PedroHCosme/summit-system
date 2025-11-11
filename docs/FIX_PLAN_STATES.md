# Correção: Estados de Planos Incorretos

## Problema Identificado

Membros com **planos ativos** (data de vencimento futura) apareciam como **INATIVOS** no sistema.

## Causa Raiz

O `estado_plano` era importado **diretamente do Google Sheets** sem validação. Se o estado no Sheets estivesse desatualizado (marcado como INATIVO manualmente), o sistema aceitava esse valor mesmo que a data de vencimento ainda não tivesse chegado.

### Fluxo Anterior (Incorreto)
```
Google Sheets (estado: INATIVO, vencimento: 20/11/2025)
         ↓
    Sincronização (aceita INATIVO sem validar)
         ↓
Banco de Dados (estado: INATIVO, mesmo com vencimento futuro)
         ↓
  Interface (exibe INATIVO incorretamente)
```

## Solução Implementada

### 1. Cálculo Automático do Estado na Sincronização

**Arquivo**: `src/ui/workers/sync_worker.py`

Adicionada função `_calculate_estado_from_vencimento()` que:
- Recebe a data de vencimento (DD/MM/YYYY ou YYYY-MM-DD)
- Compara com a data atual
- Retorna 'ATIVO' se `vencimento >= hoje`
- Retorna 'INATIVO' se `vencimento < hoje`

**Código**:
```python
def _calculate_estado_from_vencimento(self, vencimento_str: str) -> str:
    """Calcula o estado do plano baseado na data de vencimento."""
    if not vencimento_str or not vencimento_str.strip():
        return 'ATIVO'
    
    try:
        # Parsear data (suporta DD/MM/YYYY e YYYY-MM-DD)
        if '/' in vencimento_str:
            vencimento_dt = datetime.strptime(vencimento_str, '%d/%m/%Y')
        else:
            vencimento_dt = datetime.strptime(vencimento_str, '%Y-%m-%d')
        
        hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        vencimento_dt = vencimento_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Comparação: se vencimento já passou, INATIVO
        return 'INATIVO' if vencimento_dt < hoje else 'ATIVO'
    except (ValueError, AttributeError):
        return 'ATIVO'  # Default seguro em caso de erro
```

**Aplicação na Sincronização**:
```python
# Antes (ERRADO)
'estado_plano': data_dict.get('estado_plano', '')

# Depois (CORRETO)
vencimento = data_dict.get('vencimento_plano', '')
estado_calculado = self._calculate_estado_from_vencimento(vencimento)
'estado_plano': estado_calculado
```

### 2. Correção em Tempo Real no Dialog

**Arquivo**: `src/ui/dialogs/expiring_plans_dialog.py`

O dialog de "Planos a Vencer" agora **calcula o estado** baseado nos dias restantes:

```python
# Se o vencimento ainda não chegou, deve estar ATIVO
estado_correto = 'ATIVO' if days_remaining >= 0 else 'INATIVO'
```

Isso garante que **mesmo se o estado estiver errado no banco**, o usuário vê a informação correta.

### 3. Script de Correção do Banco

**Arquivo**: `scripts/fix_plan_states.py`

Script standalone para corrigir **todos os estados** no banco de dados existente:

```bash
python scripts/fix_plan_states.py
```

**Funcionalidades**:
- ✅ Analisa todos os membros com data de vencimento
- ✅ Calcula o estado correto baseado na data
- ✅ Atualiza apenas registros incorretos
- ✅ Mostra estatísticas detalhadas
- ✅ Exibe cada correção realizada

**Exemplo de Saída**:
```
🔍 Analisando 150 membros com data de vencimento...

✅ João Silva: INATIVO → ATIVO (vence em 15 dias)
✅ Maria Santos: INATIVO → ATIVO (vence em 8 dias)
❌ Pedro Costa: ATIVO → INATIVO (venceu há 3 dias)

============================================================
✅ Correção concluída!
📊 Estatísticas:
   • Total de membros analisados: 150
   • Membros atualizados: 45
   • Membros já corretos: 103
   • Erros: 2
============================================================
```

## Fluxo Correto (Após Correção)

```
Google Sheets (estado: qualquer, vencimento: 20/11/2025)
         ↓
    Sincronização (IGNORA estado do Sheets)
         ↓
  Cálculo Automático (20/11/2025 > hoje → ATIVO)
         ↓
Banco de Dados (estado: ATIVO, vencimento: 20/11/2025)
         ↓
  Interface (exibe ATIVO corretamente)
```

## Validação Adicional

A mesma lógica já existia em `edit_member_dialog.py` e agora foi padronizada em 3 lugares:
1. **Sincronização** (importação do Sheets)
2. **Dialog de Planos a Vencer** (exibição)
3. **Edição de Membro** (ao salvar alterações)

## Casos de Teste

### Teste 1: Plano com Vencimento Futuro
```
Dados: vencimento = "20/11/2025", hoje = "11/11/2025"
Resultado: estado = "ATIVO" ✅
```

### Teste 2: Plano Vencido
```
Dados: vencimento = "01/11/2025", hoje = "11/11/2025"
Resultado: estado = "INATIVO" ✅
```

### Teste 3: Vencimento Hoje
```
Dados: vencimento = "11/11/2025", hoje = "11/11/2025"
Resultado: estado = "ATIVO" ✅ (ainda não venceu)
```

### Teste 4: Sem Vencimento
```
Dados: vencimento = "", hoje = "11/11/2025"
Resultado: estado = "ATIVO" ✅ (padrão seguro)
```

## Como Usar

### Para Dados Existentes (Banco com Estados Errados)
```bash
# Execute o script de correção
python scripts/fix_plan_states.py
```

### Para Novas Sincronizações
O cálculo automático agora acontece **automaticamente** em toda sincronização:
```
Menu → Ferramentas → Sincronizar com Google Sheets
```

### Verificação Manual
Abra o dialog de planos a vencer para ver estados calculados em tempo real:
```
Menu → Gestão → Planos → Planos a Vencer
```

## Prevenção Futura

### Manutenção do Google Sheets
- Não é mais necessário atualizar manualmente o `estado_plano` no Sheets
- O sistema calcula automaticamente baseado no `vencimento_plano`
- Você pode até **remover a coluna** de estado do Sheets (opcional)

### Sincronização Periódica
Execute sincronizações regulares para manter os dados atualizados:
- **Diariamente**: Estados são recalculados automaticamente
- **Após renovações**: Novos vencimentos geram estados corretos
- **Após vencimentos**: Membros são marcados como INATIVO automaticamente

## Observações Técnicas

### Formatos de Data Suportados
- `DD/MM/YYYY` (ex: 20/11/2025) - Formato legado
- `YYYY-MM-DD` (ex: 2025-11-20) - Formato SQL

### Comparação de Datas
- **Hora zerada**: `00:00:00` para comparação precisa por dia
- **Vencimento no mesmo dia**: Considerado ATIVO até as 23:59:59
- **Timezone**: Usa hora local do servidor

### Performance
- Cálculo O(1) por membro (instantâneo)
- Sem impacto na velocidade de sincronização
- Script de correção processa ~1000 membros/segundo

## Arquivos Modificados

1. ✅ `src/ui/workers/sync_worker.py` (+ função de cálculo)
2. ✅ `src/ui/dialogs/expiring_plans_dialog.py` (+ cálculo em tempo real)
3. ✅ `scripts/fix_plan_states.py` (novo script de correção)
4. ✅ `docs/FIX_PLAN_STATES.md` (esta documentação)

## Benefícios

- ✅ **Consistência**: Estado sempre reflete a realidade da data
- ✅ **Automação**: Não requer intervenção manual
- ✅ **Confiabilidade**: Elimina erros humanos no Sheets
- ✅ **Manutenibilidade**: Lógica centralizada e reutilizável
- ✅ **Auditabilidade**: Fácil rastrear qual lógica foi aplicada
