# Guia de Sincronização via Interface Gráfica

## 📋 Visão Geral

A funcionalidade de sincronização permite atualizar o banco de dados local com os dados mais recentes do Google Sheets diretamente pela interface gráfica, sem necessidade de executar scripts manualmente.

## 🚀 Como Usar

### 1. Acessar a Função de Sincronização

1. Abra a aplicação normalmente
2. Aguarde a conexão com o banco de dados ser estabelecida
3. No menu superior, clique em **Ferramentas → 🔄 Sincronizar com Google Sheets**

![Menu Sincronização](menu-sync.png)

### 2. Confirmar a Sincronização

Um diálogo de confirmação será exibido perguntando se você deseja prosseguir:

```
Deseja realmente sincronizar os dados?

Esta operação pode levar alguns minutos dependendo
da quantidade de dados no Google Sheets.
```

- Clique em **Sim** para continuar
- Clique em **Não** para cancelar

### 3. Acompanhar o Progresso

Uma vez iniciada, você verá:

- **Barra de progresso**: Mostra o percentual de conclusão (0-100%)
- **Status atual**: Indica qual fase está sendo executada
- **Log de atividades**: Registro detalhado de todas as operações

#### Fases da Sincronização

1. **Conectando ao Google Sheets** (5%)
2. **Conectando ao banco de dados local** (10%)
3. **Verificando estrutura do banco** (15%)
4. **Lendo dados do Google Sheets** (20-40%)
5. **Sincronizando membros** (45-70%)
6. **Sincronizando check-ins** (75-95%)
7. **Concluído** (100%)

### 4. Resultados

Ao final, um resumo completo será exibido:

```
📊 RESUMO DA SINCRONIZAÇÃO
==================================================
👥 Membros:
   • Novos: 5
   • Existentes: 145
   • Total processado: 150

📋 Check-ins:
   • Novos: 87
   • Duplicados ignorados: 234

🕐 Horário: 11/11/2025 14:30:45
==================================================
```

## 🔒 Segurança e Garantias

### Proteção de Dados

- **Modo Incremental**: A sincronização NUNCA apaga dados existentes
- **Transações Atômicas**: Se houver qualquer erro, NENHUMA alteração parcial é salva
- **Detecção de Duplicatas**: Check-ins já existentes são ignorados automaticamente
- **Confirmação Prévia**: Sempre requer confirmação do usuário antes de iniciar

### O que é Sincronizado?

✅ **Adicionado:**
- Novos membros encontrados no Google Sheets
- Novos check-ins que não existem no banco local
- Atualizações de dados de membros existentes

❌ **NÃO afetado:**
- Membros que só existem no banco local
- Check-ins já registrados
- Pagamentos registrados
- Histórico de transações

## 🎯 Casos de Uso

### Caso 1: Primeira Sincronização
**Situação:** Você acabou de configurar o sistema e quer importar dados do Sheets pela primeira vez.

**Ação:** Execute a sincronização normalmente. Todos os membros e check-ins serão importados.

### Caso 2: Atualização Periódica
**Situação:** Você usa o Google Sheets no dia a dia e quer manter o banco local atualizado.

**Recomendação:** Execute a sincronização diariamente ou semanalmente para capturar novos dados.

### Caso 3: Após Adicionar Muitos Check-ins no Sheets
**Situação:** Você registrou vários check-ins manualmente no Google Sheets.

**Ação:** Execute a sincronização. Apenas os novos check-ins serão adicionados, duplicatas são ignoradas.

### Caso 4: Verificar Integridade dos Dados
**Situação:** Você quer garantir que todos os dados do Sheets estão no banco local.

**Ação:** Execute a sincronização. O resumo mostrará quantos registros já existiam vs. quantos foram adicionados.

## ⚠️ Tratamento de Erros

### Erro: "Erro ao autenticar no Google Sheets"

**Causa:** Credenciais inválidas ou arquivo `credentials.json` ausente.

**Solução:**
1. Verifique se o arquivo `credentials.json` existe na raiz do projeto
2. Confirme que as credenciais não expiraram
3. Certifique-se de ter permissões de leitura na planilha

### Erro: "Erro ao conectar ao banco de dados"

**Causa:** Problema ao acessar o arquivo SQLite.

**Solução:**
1. Verifique se você tem permissões de escrita na pasta do projeto
2. Confirme que o arquivo `gym_database.db` não está corrompido
3. Tente fechar outras aplicações que possam estar bloqueando o arquivo

### Erro: "Transação revertida devido a erro"

**Causa:** Erro durante a operação, mas os dados foram protegidos.

**Solução:**
1. **BOA NOTÍCIA:** Nenhum dado foi corrompido (rollback automático)
2. Verifique o log detalhado para identificar o problema específico
3. Corrija o problema e tente novamente

## 📊 Interpretando o Resumo

### Membros Novos vs. Existentes

```
👥 Membros:
   • Novos: 5           ← Membros que foram ADICIONADOS ao banco
   • Existentes: 145    ← Membros que JÁ ESTAVAM no banco
   • Total: 150         ← Total de membros únicos processados
```

- **Novos > 0**: Novos cadastros foram encontrados no Sheets
- **Novos = 0**: Todos os membros do Sheets já estavam no banco

### Check-ins Novos vs. Duplicados

```
📋 Check-ins:
   • Novos: 87               ← Check-ins que foram ADICIONADOS
   • Duplicados ignorados: 234  ← Check-ins que JÁ EXISTIAM
```

- **Duplicados alto**: Normal se você sincroniza frequentemente
- **Novos alto**: Muitos check-ins foram registrados desde a última sync

## 🔄 Sincronização vs. Migração Completa

### Sincronização (via UI)
- ✅ Preserva todos os dados existentes
- ✅ Adiciona apenas novos registros
- ✅ Interface visual com progresso
- ✅ Ideal para uso frequente
- ⚠️ Modo apenas incremental

### Migração Completa (via script)
```bash
python scripts/migrate_data.py
```
- ⚠️ **APAGA** todos os dados existentes
- ✅ Recria o banco do zero
- ✅ Ideal para reset completo
- ❌ Perde dados locais não sincronizados

### Migração Incremental (via script)
```bash
python scripts/migrate_data.py --append
```
- ✅ Mesma funcionalidade da sincronização UI
- ✅ Pode ser agendada (cron/task scheduler)
- ❌ Sem interface visual
- ✅ Ideal para automação

## 💡 Dicas e Boas Práticas

### 1. Sincronize Regularmente
Execute a sincronização pelo menos 1x por semana para manter os dados atualizados.

### 2. Verifique o Resumo
Sempre revise o resumo final para identificar anomalias (ex: muitos duplicados pode indicar problema).

### 3. Dashboard Automático
Após a sincronização, o dashboard é automaticamente atualizado com os novos dados.

### 4. Backup Manual (Opcional)
Antes de grandes sincronizações, faça backup do banco:
```bash
cp gym_database.db gym_database.db.backup
```

### 5. Conexão Estável
Certifique-se de ter conexão estável com a internet durante todo o processo.

## 🆘 Suporte

Em caso de problemas não cobertos neste guia:

1. **Verifique o log de atividades** no próprio diálogo
2. **Consulte os logs do console** da aplicação
3. **Tente executar o script direto**:
   ```bash
   python scripts/migrate_data.py --append
   ```
4. **Reporte o erro** com o log completo para análise

## 📝 Histórico de Versões

- **v1.0** (Nov 2025): Lançamento inicial da funcionalidade de sincronização via UI
  - Sincronização incremental segura
  - Feedback visual em tempo real
  - Proteção contra perda de dados
  - Detecção automática de duplicatas
