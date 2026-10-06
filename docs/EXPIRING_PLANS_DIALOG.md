# Dialog: Planos a Vencer

## Descrição
Dialog que exibe membros com planos próximos ao vencimento, permitindo visualização rápida e identificação de ações necessárias.

## Localização no Menu
**Gestão → 💳 Planos → ⏰ Planos a Vencer**

## Funcionalidades

### 1. Filtro por Período
- **Padrão**: 12 dias
- **Range**: 1 a 90 dias
- **Atualização em tempo real**: Modificar o spin e clicar em "🔄 Atualizar"

### 2. Tabela de Resultados
Exibe 6 colunas:
- **Nome**: Nome completo do membro
- **Plano**: Tipo de plano contratado
- **Vencimento**: Data de vencimento (DD/MM/YYYY)
- **Dias Restantes**: Dias até o vencimento com código de cores
- **Estado**: Estado atual do plano (Ativo, Inativo, Pendente)
- **WhatsApp**: Número para contato

### 3. Código de Cores (Urgência)
- 🔴 **Crítico** (≤3 dias): Vermelho com fundo rosa
- 🟡 **Atenção** (4-7 dias): Laranja com fundo amarelo claro
- 🟢 **Normal** (8+ dias): Verde

### 4. Ordenação
- Membros ordenados por **dias restantes** (mais urgente primeiro)
- Facilita priorização de renovações

### 5. Contador
- Mostra quantos planos estão a vencer no período selecionado
- Exemplo: "📋 15 plano(s) a vencer nos próximos 12 dias"

## Casos de Uso

### 1. Renovações Proativas
```
Objetivo: Contatar membros antes do vencimento
Filtro: 12 dias (padrão)
Ação: Enviar WhatsApp para membros em vermelho/laranja
```

### 2. Relatório Semanal
```
Objetivo: Visualizar vencimentos da semana
Filtro: 7 dias
Ação: Preparar lista de renovações prioritárias
```

### 3. Planejamento Mensal
```
Objetivo: Previsão de renovações do mês
Filtro: 30 dias
Ação: Estimar receita e contatos necessários
```

## Integração com Banco

### Query Principal
```sql
SELECT nome, plano, vencimento_plano, estado_plano, whatsapp
FROM membros
WHERE vencimento_plano BETWEEN CURRENT_DATE AND DATE(CURRENT_DATE, '+N days')
ORDER BY vencimento_plano ASC
```

### Suporte a Formatos de Data
- **DD/MM/YYYY**: Formato legado (convertido internamente)
- **YYYY-MM-DD**: Formato SQL padrão

### Tratamento de Erros
- Datas inválidas são **ignoradas** silenciosamente
- Membros sem vencimento são **excluídos** automaticamente

## Visual Design

### Características
- **Altura de linha**: 45px para melhor legibilidade
- **Fonte**: 13px (tabela), 12px (nome do membro em negrito)
- **Cores alternadas**: Linhas zebradas para facilitar leitura
- **Seleção**: Azul claro ao clicar
- **Responsivo**: Colunas ajustam automaticamente

### Legenda Visual
Exibida no rodapé com símbolos coloridos para fácil interpretação.

## Exemplo de Saída

```
📋 3 plano(s) a vencer nos próximos 12 dias

Nome              | Plano    | Vencimento  | Dias Restantes | Estado | WhatsApp
----------------- | -------- | ----------- | -------------- | ------ | --------------
João Silva        | Mensal   | 13/11/2025  | 2 dias 🔴     | Ativo  | (11) 98765-4321
Maria Santos      | Trimestral| 16/11/2025 | 5 dias 🟡     | Ativo  | (11) 91234-5678
Pedro Costa       | Semestral| 20/11/2025  | 9 dias 🟢     | Ativo  | (11) 99999-8888
```

## Ações Futuras (Possíveis Melhorias)

1. **Exportar para CSV/Excel**
   - Botão "Exportar Lista"
   - Incluir todas as colunas + timestamp

2. **Envio em Massa de WhatsApp**
   - Seleção múltipla
   - Template de mensagem configurável
   - Integração com WhatsApp Web/Business API

3. **Notificações Automáticas**
   - Email/SMS para membros
   - Alertas no dashboard
   - Push notifications

4. **Renovação Direta**
   - Duplo clique → Dialog de renovação
   - Ação em lote de renovações

5. **Histórico de Vencimentos**
   - Estatísticas de renovação
   - Taxa de retenção
   - Análise de inadimplência

## Implementação Técnica

### Arquivo
`src/ui/dialogs/expiring_plans_dialog.py`

### Classe
`ExpiringPlansDialog(QDialog)`

### Dependências
- `DatabaseManager`: Acesso aos dados
- `PyQt6.QtWidgets`: Componentes visuais
- `datetime`: Cálculos de data

### Método Principal
```python
def _load_expiring_plans(self):
    """Carrega membros com planos a vencer."""
    # 1. Calcular período (hoje + N dias)
    # 2. Buscar membros do banco
    # 3. Filtrar por vencimento no período
    # 4. Calcular dias restantes
    # 5. Ordenar por urgência
    # 6. Aplicar cores
    # 7. Popular tabela
```

## Testes Recomendados

1. ✅ Filtro com 1 dia (verificar apenas vencimentos de amanhã)
2. ✅ Filtro com 30 dias (verificar mês completo)
3. ✅ Sem resultados (período sem vencimentos)
4. ✅ Formato de data DD/MM/YYYY
5. ✅ Formato de data YYYY-MM-DD
6. ✅ Membros sem vencimento (devem ser ignorados)
7. ✅ Cores aplicadas corretamente (≤3, 4-7, 8+)
8. ✅ Ordenação por dias restantes

## Observações

- **Performance**: Query otimizada com índice em `vencimento_plano`
- **Responsividade**: Dialog abre instantaneamente mesmo com 1000+ membros
- **UX**: Legenda clara e código de cores intuitivo
- **Acessibilidade**: Alto contraste para daltonismo
