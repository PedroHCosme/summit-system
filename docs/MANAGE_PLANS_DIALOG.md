# ⚙️ Diálogo "Gerenciar Planos" - Implementado

**Data:** 11/11/2025  
**Status:** ✅ Completo  
**Arquivos:** `src/ui/dialogs/manage_plans_dialog.py`, `src/ui/main_window.py`

---

## 📋 Visão Geral

Diálogo completo e visual para gerenciar planos, preços e configurações do sistema, com interface amigável em abas e salvamento local em JSON.

---

## ✨ Funcionalidades Implementadas

### 1. Interface com Abas

#### 📝 Tab 1: "Planos e Preços"
- **Tabela editável** com todos os planos
- **4 colunas:**
  - Nome do Plano (somente leitura)
  - Preço de Renovação (R$) - editável com spin
  - Pagamento por Check-in (R$) - editável com spin
  - Requer Vencimento - checkbox

**Recursos:**
- ✅ Spin boxes com incrementos de R$ 10 (renovação) e R$ 5 (check-in)
- ✅ Valores formatados com prefixo "R$"
- ✅ Checkboxes centralizados
- ✅ Header visual com bordas coloridas
- ✅ Botão "➕ Adicionar Novo Plano"

#### ⚙️ Tab 2: "Configurações"
- **Grupo 1:** Planos com Pagamento por Check-in
  - Lista dinâmica de planos pay-per-checkin
  - Mostra valor por check-in
  
- **Grupo 2:** Planos que Exigem Vencimento
  - Lista de planos com controle de vencimento
  
- **Grupo 3:** Configurações Futuras (Placeholder)
  - Grace Period
  - Pro-rata
  - Descontos automáticos
  - Regras de upgrade/downgrade

---

### 2. Adicionar Novos Planos

**Como funciona:**
1. Clicar em "➕ Adicionar Novo Plano"
2. Digitar nome do plano
3. Validação automática de duplicatas
4. Plano adicionado com valores padrão (R$ 0)
5. Configurar preços e opções na tabela

**Exemplo:**
```
Novo plano: "Personal Training"
→ Preço renovação: R$ 500,00
→ Pagamento check-in: R$ 0,00
→ Requer vencimento: ✓
```

---

### 3. Edição de Planos Existentes

**Edições permitidas:**
- ✅ Alterar preço de renovação
- ✅ Alterar valor por check-in
- ✅ Marcar/desmarcar "Requer Vencimento"
- ❌ Nome do plano (somente leitura - evita inconsistências)

**Validações automáticas:**
- Valores mínimos: R$ 0,00
- Valores máximos: R$ 10.000 (renovação), R$ 1.000 (check-in)
- Decimais: 2 casas

---

### 4. Salvamento Local

**Arquivo gerado:** `plans_config.json` (raiz do projeto)

**Estrutura:**
```json
{
    "PLANOS": [
        "Mensal",
        "Trimestral",
        "Anual",
        "Diária",
        "Gympass",
        "Totalpass",
        "Cortesia"
    ],
    "PLANOS_PRECOS": {
        "Mensal": 190.0,
        "Trimestral": 500.0,
        "Anual": 1900.0,
        "Diária": 0.0,
        "Gympass": 0.0,
        "Totalpass": 0.0,
        "Cortesia": 0.0
    },
    "PLANOS_PAGAMENTO_POR_CHECKIN": {
        "Diária": 35.0,
        "Gympass": 15.0,
        "Totalpass": 15.0
    },
    "PLANOS_COM_VENCIMENTO": [
        "Mensal",
        "Trimestral",
        "Anual"
    ],
    "_metadata": {
        "version": "1.0",
        "last_updated": "2025-11-11 10:30:45",
        "description": "Configuração de planos e preços editada via UI"
    }
}
```

**Vantagens:**
- ✅ Não modifica código-fonte (`config.py`)
- ✅ Versionável (Git)
- ✅ Portável entre ambientes
- ✅ Fácil backup/restauração
- ✅ Metadata com histórico

---

### 5. Restaurar Padrões

**Funcionalidade:**
- Botão "🔄 Restaurar Padrões"
- Confirmação antes de executar
- Recarrega valores originais de `config.py`
- Atualiza interface automaticamente

**Quando usar:**
- Reverter alterações não salvas
- Resetar após testes
- Voltar à configuração inicial

---

### 6. Proteções e Validações

#### ✅ Confirmações
- **Fechar com alterações não salvas:**
  - "Deseja salvar?"
  - Opções: Salvar | Descartar | Cancelar
  
- **Restaurar padrões:**
  - Confirmação obrigatória
  - Aviso de irreversibilidade

#### ✅ Validações
- Duplicatas de planos (ao adicionar)
- Valores dentro dos limites
- Campos obrigatórios

#### ✅ Feedback Visual
- Marcador de alterações não salvas (`has_changes`)
- Tooltips explicativos
- Labels informativos
- Cores de destaque (azul: info, amarelo: aviso, verde: sucesso)

---

## 🎨 Design e UX

### Paleta de Cores
- **Header da tabela:** #F5F5F5 com borda #007ACC
- **Botão Salvar:** #28A745 (verde)
- **Botão Restaurar:** #FFA726 (laranja)
- **Info Box:** #E3F2FD com texto #1976D2
- **Tabs selecionada:** #007ACC
- **Tabs hover:** #D0D0D0

### Espaçamento e Layout
- Margens: 15px
- Padding em boxes: 10px
- Altura de botões: 35px
- Altura de tabs: padrão com padding 10px 20px

### Tipografia
- **Título:** 16pt, bold
- **Descrição:** 12px, #666666
- **Tabela:** 14px
- **Labels de info:** 11px

---

## 🔄 Fluxo de Uso

### Cenário 1: Editar Preço de Plano Existente
1. Menu → Gestão → Planos → Gerenciar Planos e Preços
2. Na tab "Planos e Preços", localizar o plano
3. Alterar valor no spin box
4. Clicar em "💾 Salvar Alterações"
5. Confirmação de sucesso
6. Alterações aplicadas imediatamente

### Cenário 2: Adicionar Novo Plano
1. Abrir diálogo de gerenciamento
2. Clicar "➕ Adicionar Novo Plano"
3. Digitar nome (ex: "Day Use")
4. Confirmar
5. Configurar:
   - Preço renovação: R$ 0
   - Pagamento check-in: R$ 50
   - Requer vencimento: ☐
6. Salvar

### Cenário 3: Configurar Plano Pay-per-Checkin
1. Selecionar plano (ex: "Diária")
2. **Preço Renovação:** R$ 0,00 (importante!)
3. **Pagamento por Check-in:** R$ 35,00
4. **Requer Vencimento:** ☐ (desmarcar)
5. Verificar na tab "Configurações" → aparece em "Planos com Pagamento por Check-in"
6. Salvar

### Cenário 4: Restaurar Após Teste
1. Fazer alterações para testar
2. Clicar "🔄 Restaurar Padrões"
3. Confirmar
4. Valores voltam ao original
5. Opção de salvar ou descartar

---

## 🧪 Como Testar

### Teste 1: Abrir Diálogo
```bash
python run.py
```
1. Aguardar conexão
2. Menu → Gestão → Planos → Gerenciar Planos e Preços
3. Verificar interface com 2 tabs
4. Verificar tabela com planos atuais

### Teste 2: Editar Preços
1. Alterar "Mensal" de R$ 190 para R$ 200
2. Alterar "Trimestral" de R$ 500 para R$ 480
3. Clicar "Salvar"
4. Fechar e reabrir → verificar valores salvos
5. Verificar `plans_config.json` criado na raiz

### Teste 3: Adicionar Plano
1. Clicar "➕ Adicionar Novo Plano"
2. Nome: "Teste Premium"
3. Configurar:
   - R$ 300 renovação
   - R$ 0 check-in
   - ✓ Requer vencimento
4. Salvar
5. Verificar em Renovar Plano de membro → novo plano aparece

### Teste 4: Configurar Pay-per-Checkin
1. Adicionar plano "Day Pass"
2. Configurar:
   - R$ 0 renovação
   - R$ 40 check-in
   - ☐ vencimento
3. Ir para tab "Configurações"
4. Verificar aparece em "Planos com Pagamento por Check-in"
5. Salvar
6. Fazer check-in de membro com este plano → deve gerar pagamento de R$ 40

### Teste 5: Proteção de Fechamento
1. Fazer alterações
2. Tentar fechar (X)
3. Verificar aviso "Alterações não salvas"
4. Testar opções: Salvar | Descartar | Cancelar

### Teste 6: Restaurar Padrões
1. Fazer várias alterações
2. Clicar "🔄 Restaurar Padrões"
3. Confirmar
4. Verificar valores voltaram ao original
5. Salvar para aplicar restauração

---

## 📊 Comparação: Antes vs Depois

| Aspecto | ❌ Antes | ✅ Depois |
|---------|----------|-----------|
| **Editar planos** | Editar `config.py` manualmente | Interface visual |
| **Adicionar plano** | Editar 4 variáveis no código | 1 clique + nome |
| **Ver preços** | Procurar no código | Tabela organizada |
| **Configurar pay-per-checkin** | Editar dicionário | Spin box + checkbox |
| **Validação** | Nenhuma (erros em runtime) | Validação automática |
| **Backup de config** | Git commit | Arquivo JSON separado |
| **Aplicar mudanças** | Reiniciar app | Imediato |
| **Reverter** | Git revert | Botão "Restaurar" |

---

## 🔮 Melhorias Futuras

### Curto Prazo
- [ ] Importar/Exportar configurações (CSV)
- [ ] Preview de alterações antes de salvar
- [ ] Histórico de mudanças (log)

### Médio Prazo
- [ ] Grace Period por plano (dias de tolerância)
- [ ] Pro-rata (cálculo proporcional)
- [ ] Descontos configuráveis (%, valor fixo)
- [ ] Regras de upgrade/downgrade

### Longo Prazo
- [ ] Templates de planos (família, corporativo)
- [ ] Planos sazonais (verão, inverno)
- [ ] Planos promocionais com data de expiração
- [ ] Integração com gateway de pagamento

---

## 📁 Arquivos

### Criados
- ✅ `src/ui/dialogs/manage_plans_dialog.py` - Diálogo completo (560 linhas)
- ✅ `plans_config.json` - Arquivo de configuração (criado ao salvar)

### Modificados
- ✅ `src/ui/dialogs/__init__.py` - Export do diálogo
- ✅ `src/ui/main_window.py` - Import e conexão do menu

---

## 💡 Dicas de Uso

### Para Administradores
1. **Faça backup antes de grandes mudanças** - copie `plans_config.json`
2. **Teste em ambiente de desenvolvimento** primeiro
3. **Use "Restaurar Padrões"** se algo der errado
4. **Verifique tab "Configurações"** após edições para validar regras

### Para Desenvolvedores
1. **Arquivo JSON sobrescreve `config.py`** em memória após salvar
2. **Validações estão no diálogo** - adicione novas se necessário
3. **Metadata** no JSON facilita auditoria
4. **Signal `plans_updated`** pode ser conectado para refresh automático

---

## 🎯 Integração com Sistema

### Efeito Imediato ao Salvar
1. **Variáveis em `config.py` atualizadas** em memória
2. **Renovação de planos** usa novos preços
3. **Check-ins** geram pagamentos com novos valores
4. **Cadastro de membros** mostra novos planos
5. **Relatórios financeiros** calculam com novos preços

### Persistência
- Configurações salvas em `plans_config.json`
- Na próxima execução, sistema pode carregar do JSON
- Permite diferentes configs por ambiente (dev, prod)

---

## 🎉 Resultado Final

O diálogo "Gerenciar Planos" agora oferece:
- ✅ **Interface profissional** com tabs e tabelas editáveis
- ✅ **Validações robustas** previnem erros
- ✅ **Salvamento seguro** em JSON separado do código
- ✅ **Feedback visual** em todas as ações
- ✅ **Proteção contra perda** de alterações
- ✅ **Fácil reversão** com restaurar padrões
- ✅ **Extensível** para futuras configurações

**Status:** Pronto para uso em produção! 🚀

**Acesso:** Menu → Gestão → Planos → Gerenciar Planos e Preços
