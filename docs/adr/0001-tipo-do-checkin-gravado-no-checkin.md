# Tipo do Check-in gravado no proprio check-in

Os relatorios precisam saber por qual plano cada visita entrou, para medir Conversoes e Perdas para Gym/Totalpass. Antes, esse tipo era derivado do plano *atual* do membro, e por isso todo o historico de quem trocava de plano era reclassificado. Decidimos gravar o plano do membro na tabela `frequencia` no momento do check-in. Os check-ins antigos sao preenchidos uma unica vez: pelo `Pagamento` Gympass/Totalpass/Diaria do mesmo membro no mesmo dia e, na falta dele, pelo plano atual.

## Considered Options

- **Derivar do plano atual** (como era): nao exige migracao, mas apaga a historia exatamente quando o membro troca de plano, que e o evento que queremos medir.
- **Cruzar com `Pagamento` em toda consulta**: nao mexe no esquema, mas so funciona para planos que geram pagamento por check-in, e toda consulta de frequencia vira um join fragil por data.

## Consequences

- O backfill erra quem trocou de plano e tem check-ins antigos sem pagamento no dia. No banco real de jan/2026 foram 15 check-ins de 2 membros, e aceitamos o erro sem marcacao de "estimado".
- Perdas para Gym/Totalpass anteriores a migracao nao sao recuperaveis. O check-in antigo de Assinante nao tem pagamento, entao herda o plano atual. As Perdas so sao medidas dali em diante.
- Trocar o plano de um membro nao altera mais os check-ins passados dele. Corrigir um check-in lancado errado passa a ser uma edicao do proprio check-in.
