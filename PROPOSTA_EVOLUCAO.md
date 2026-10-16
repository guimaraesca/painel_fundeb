# Proposta de Evolução — Plataforma FUNDEB & VAAR 2026

**De um painel de VAAR para uma plataforma educacional multidimensional, com ETL completo e geração de relatórios para redes municipais, estaduais e para o MEC.**

Data: 15/10/2026 · Status: proposta + protótipo funcional entregue neste repositório.

---

## 1. Resumo executivo

O painel atual cumpre bem um recorte: diagnosticar a **Complementação-VAAR** (habilitação, condicionalidades, valores). Esta proposta o transforma em uma **plataforma de gestão educacional baseada em evidências**, que:

1. **Atende três públicos** com a mesma base auditada — secretaria **municipal**, secretaria **estadual** e **MEC/gestão macro**;
2. **Vai além do financeiro**, tratando **fluxo escolar** (aprovação, reprovação, abandono), **aprendizagem** (Ideb/Saeb) e **contexto** (INSE, conectividade) como indicadores de primeira classe, ao lado dos recursos;
3. Roda um **ETL completo e auditável** (Extract → Transform → Load) que produz um *data warehouse* analítico com linhagem (SHA-256), frescor e verificações de integridade;
4. Entrega um **gerador de relatórios em PDF**, nos modos **geral** (panorama nacional) e **específico** (por rede), prontos para envio a gestores e ao Ministério.

O protótipo que acompanha esta proposta já implementa os itens 2, 3 e 4 de ponta a ponta, sobre a base real.

---

## 2. Públicos-alvo e necessidades

A mesma base, lida por três lentes distintas:

| Público | Pergunta central | Como a plataforma responde |
|---|---|---|
| **Rede municipal** | "O que me falta para habilitar/sustentar o VAAR e onde minha aprendizagem está frente à média?" | Relatório **específico** do ente: situação, indicadores vs. médias (própria rede e Brasil) e plano de ação por condicionalidade. |
| **Rede estadual** | "Como está minha rede e as redes do meu território (regime de colaboração, ICMS-Educação)?" | Relatório específico da rede estadual + geração em lote por UF. |
| **MEC / gestão macro** | "Onde estão os maiores gargalos nacionais e como priorizar política e recurso?" | Relatório **geral**: panorama por dimensão, ranking de UFs e funil de condicionalidades. |

---

## 3. O que muda — de VAAR-cêntrico para multidimensional

As fontes de **fluxo, Saeb e aprendizagem já existem na base processada**, mas eram subutilizadas pelas telas (centradas em VAAR). A evolução promove essas dimensões a cidadãs de primeira classe por meio de um **catálogo de indicadores** único (`fundeb/etl/indicadores.py`), que descreve cada métrica com dimensão, rótulo, unidade, fonte e o sentido de "melhor":

| Dimensão | Indicadores | Fonte |
|---|---|---|
| **Financeiro** | Receita de contribuição, VAAF, VAAT, VAAR (2025/2026), Complementação total | FNDE 2026 |
| **Fluxo escolar** | Aprovação/Reprovação/Abandono (EF e EM) | Inep — Taxas de rendimento 2025 |
| **Aprendizagem** | Ideb (AI/AF/EM), Saeb LP/MT (AI/AF/EM) | Inep — Ideb/Saeb 2025 |
| **Contexto** | INSE, conectividade (% internet, adequação, download) | Inep INSE 2023 · NIC.br/SIMET |
| **VAAR & condicionalidades** | Indicadores de atendimento/aprendizagem, condicionalidades I–V, habilitação | FNDE 2026 — art. 14 |

São **29 indicadores em 5 dimensões**, aplicados a **5.596 redes** (27 estaduais + 5.569 municipais).

---

## 4. Arquitetura do ETL completo

Pipeline em três estágios, orquestrado por `fundeb/etl/pipeline.py`:

```
EXTRACT   fontes oficiais (src/sources.py) — FNDE, Inep, NIC.br, IBGE
   │      download roda na máquina do usuário (gov.br/Inep bloqueiam a rede do agente)
   ▼
TRANSFORM consolidate.consolidar()  → base única (reusa a base auditada do painel + derivados)
          consolidate.tabela_fato() → visão tidy (ente × indicador), 162.284 linhas
          consolidate.agregados()   → nacional / por UF / por região / por rede
   ▼
LOAD      data/processed/warehouse/
            ├─ consolidado.parquet
            ├─ fato_indicadores.parquet
            ├─ agg_{nacional,por_uf,por_regiao,por_rede}.parquet
            └─ manifest.json  (linhagem SHA-256, frescor, volumetria, qualidade)
```

**Garantias de dados.** O *transform* reutiliza `JsonDataRepository.entes()` — ou seja, a evolução usa **exatamente a mesma base auditada** do painel, sem reprocessar nem divergir. O `manifest.json` registra, a cada execução: proveniência campo a campo com hash SHA-256, cobertura por indicador (quanto de cada métrica a fonte publicou) e o resultado das verificações de integridade (somas que fecham, faixas válidas, coerência da habilitação). Campos não publicados permanecem **nulos (—)**; nenhum valor é sintético.

Execução:

```bash
python -m fundeb.etl.pipeline --check
```

---

## 5. Recurso de geração de relatórios (PDF)

Módulo `fundeb/reports/`, construído com ReportLab (puro-Python, sem dependências de sistema).

### 5.1 Relatório Geral (público: MEC / gestão macro)
Panorama nacional em PDF: leitura executiva (BLUF), faixa de KPIs, financiamento por região, fluxo e aprendizagem por rede, funil de condicionalidades e ranking de prioridades por UF.

```bash
python -m fundeb.reports.generate --geral
```

### 5.2 Relatório Específico (público: secretarias municipais/estaduais)
PDF individual por rede: identificação e situação no VAAR, **indicadores de cada dimensão comparados às médias da própria rede e do Brasil** (com marcação de posição), e **plano de ação** ligado às condicionalidades reprovadas.

```bash
python -m fundeb.reports.generate --ente 3550308        # município (São Paulo)
python -m fundeb.reports.generate --ente 11             # rede estadual (RO)
python -m fundeb.reports.generate --uf PI --estaduais   # em lote, por UF
```

Saída padrão em `outputs/relatorios/`.

---

## 6. O que já está entregue neste protótipo

| Entregável | Local | Status |
|---|---|---|
| Catálogo de indicadores multidimensional | `fundeb/etl/indicadores.py` | ✅ |
| ETL completo + warehouse + linhagem | `fundeb/etl/` | ✅ roda sobre a base real |
| Relatório PDF geral | `fundeb/reports/geral.py` | ✅ 2 páginas |
| Relatório PDF específico (município/estado) | `fundeb/reports/especifico.py` | ✅ |
| CLI de geração | `fundeb/reports/generate.py` | ✅ |
| Testes automatizados | `tests/test_etl_reports.py` | ✅ 34 testes no total |

---

## 7. Roadmap (próximas iterações)

1. **Aba "Relatórios" no painel** — gerar e baixar o PDF geral/específico direto pela interface (seleção de ente), além da CLI.
2. **Série histórica real** — incorporar edições anteriores de Ideb/Saeb/rendimento para medir *variação* (hoje o foco é o retrato 2025/2026).
3. **Exportação complementar** — além do PDF, Excel/CSV com os microdados por ente (a tabela-fato já está pronta para isso).
4. **Agendamento** — rotina para reexecutar o ETL quando o FNDE/Inep publicarem novas bases, comparando hashes do `manifest.json`.
5. **Relatório de UF e de região** — um nível intermediário entre o geral (país) e o específico (ente).

---

## 8. Conformidade e governança

- **Base legal:** Lei nº 14.113/2020, EC nº 108/2020 (ADCT, art. 60), art. 14 e condicionalidades I–V; Notas Técnicas Inep.
- **Fontes oficiais:** FNDE (financiamento e VAAR), Inep (Ideb, Saeb, taxas de rendimento, INSE), NIC.br/SIMET (conectividade), IBGE (malhas).
- **Auditabilidade:** linhagem SHA-256 por arquivo, verificações de integridade a cada execução e transparência de cobertura — alinhadas aos cinco pilares de observabilidade já adotados no painel (Freshness, Volume, Distribution, Schema, Lineage).

> Ver também [`DOCUMENTACAO_TECNICA.md`](DOCUMENTACAO_TECNICA.md) para a proveniência campo a campo e as fórmulas da Nota Técnica Inep.
