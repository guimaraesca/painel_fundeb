# PNAE & PNATE — exposição à subcontagem do Censo

Módulo que estende o painel para além do Fundeb/VAAR, cobrindo dois programas da
União **financiados por matrícula do Censo Escolar (Educacenso)**:

- **PNAE** — Programa Nacional de Alimentação Escolar (merenda)
- **PNATE** — Programa Nacional de Apoio ao Transporte Escolar (transporte rural)

## Motivação (caso RN)

Quando a rede **não cadastra corretamente seus alunos no Educacenso**, perde
repasses proporcionais à matrícula — no PNAE, no PNATE e também no Fundeb/VAAR.
Foi o relatado no Rio Grande do Norte: ~4,48 mil alunos não cadastrados em 2025,
com perdas estimadas pela SEEC/RN em vários programas federais. Este módulo
quantifica a **parcela PNAE+PNATE** dessa exposição.

## O que o módulo entrega

1. **Valores per capita oficiais** (constantes citáveis) — `fundeb/programas/suplementares.py`
2. **Simulador de impacto da subcontagem** — tela `🍎 Programas Suplementares (PNAE/PNATE)`
   no painel completo (`app.py`): nº de alunos não cadastrados × etapa × % rural ×
   anos → perda anual e acumulada de PNAE e PNATE.
3. **Seção no relatório PDF específico** de cada ente (estadual ou municipal):
   quanto custam 100/500/1.000 alunos não cadastrados por ano.

## Valores per capita (fontes)

**PNAE** — por aluno/**dia**, Resolução CD/FNDE nº 1/2026 (base de 200 dias de atendimento):

| Etapa / modalidade | Per capita/dia | Por aluno/ano |
|---|---|---|
| Creche | R$ 1,57 | R$ 314,00 |
| Pré-escola | R$ 0,82 | R$ 164,00 |
| Fundamental / Médio / EJA | R$ 0,57 | R$ 114,00 |
| Escolas indígenas/quilombolas | R$ 0,98 | R$ 196,00 |

**PNATE** — por aluno **rural transportado/ano**, Resolução CD/FNDE nº 14/2026
(reajuste de 14,35% sobre a nº 8/2023): faixa de **R$ 138,06 a R$ 196,95**, variando
por município pelo Fator de Necessidade de Recursos do Município (FNRM).

## Exemplo (caso RN)

4.480 alunos não cadastrados, com 15% em área rural:
- **PNAE:** R$ 510,7 mil a R$ 1,41 mi/ano (faixa fundamental → creche)
- **PNATE:** R$ 92,8 mil a R$ 132,4 mil/ano
- **PNAE + PNATE:** R$ 603,5 mil a R$ 1,54 mi/ano — e R$ 1,81 a 4,62 mi em 3 anos.

> PNAE/PNATE são a **parcela menor** da perda por subcontagem; o Fundeb (VAAF/VAAT)
> e o VAAR respondem pela maior parte (cobertos nas demais telas e no relatório do ente).

## Escopo e honestidade de dados

- Os **valores per capita** e o **custo por aluno** são exatos (constantes oficiais);
  a perda por subcontagem é calculada diretamente a partir deles.
- O módulo **não** ingere os valores *efetivamente pagos* de PNAE/PNATE por ente
  (publicados pelo FNDE em plataforma/arquivo compactado de acesso instável) nem a
  **matrícula por rede** do Censo — por isso trabalha com exposição/impacto por aluno,
  não com o repasse realizado de cada ente. Ingerir os repasses reais e a matrícula
  por rede/etapa é a evolução natural seguinte.
