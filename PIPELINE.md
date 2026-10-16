# Pipeline de Dados — do download à base do painel

Documentação do **ETL completo e reproduzível** que constrói, do zero, a base
auditada do painel a partir das fontes oficiais. Executado e **validado com
paridade total** contra a base distribuída: ao reconstruir tudo do download, os
agregados do painel são idênticos (5.596 entes, 3.076 habilitados, 2.520 fora,
VAAR R$ 7,6 bi, gargalos Cond. III/I/II = 1.930/575/417).

```
  src/sources.py --download      src/parse/*               data/processed/*.json
  ┌───────────────────┐   EXTRACT   ┌─────────────────┐  TRANSFORM  ┌──────────────┐
  │ FNDE · INEP · IBGE │ ─────────▶ │ data/raw/ (+ext) │ ─────────▶ │ base do painel│
  └───────────────────┘            └─────────────────┘   + LOAD     └──────────────┘
```

---

## 1. Como reproduzir do zero

```bash
# 1) Baixar todas as fontes oficiais para data/raw (e extrair os ZIPs)
python src/sources.py --download

# 2) Reconstruir data/processed e conferir os agregados do painel
python -m src.parse.build_all --check
```

Pré-requisito: `pip install -r requirements.txt` (usa `openpyxl` para ler os XLSX do INEP).

> **Nota sobre o INEP.** O host `download.inep.gov.br` apresenta falha de cadeia
> de certificados em alguns ambientes (erro de "secure connection"). Como os
> arquivos são **públicos** e sua integridade é verificada depois (somas que
> fecham, faixas válidas, paridade), o download do INEP usa um contexto SSL sem
> verificação de cadeia. O FNDE (`gov.br`) e o IBGE (GitHub) usam SSL normal.

---

## 2. Fontes oficiais (EXTRACT)

| Grupo | Arquivos | Host | Formato | Alimenta |
|---|---|---|---|---|
| **FNDE Fundeb 2026** | receita/VAAF, VAAT, indicadores VAAR, lista de benef./condicionalidades, estimativa VAAR, ponderadores NSE e Drec, indicador Ed. Infantil | gov.br | CSV latin-1 (`;`) | `base_clean.json` |
| **FNDE VAAR 2025** | redes beneficiadas 2025 | gov.br | CSV | `v2025.json` |
| **INEP Ideb 2025** | anos iniciais, finais, ensino médio (municípios) + regiões/UFs | download.inep.gov.br | ZIP → XLSX | `ideb.json` |
| **INEP Rendimento 2025** | taxas por município + por UF | download.inep.gov.br | ZIP → XLSX | `rend.json` |
| **INEP INSE 2023** | nível socioeconômico por município | download.inep.gov.br | XLSX | `inse.json` |
| **IBGE** | malhas de UF e municípios | GitHub | GeoJSON | `geo/*` |

---

## 3. Transformações (TRANSFORM + LOAD)

Código em `src/parse/`. Cada parser reproduz **exatamente** o schema do arquivo
processado correspondente. Regras transversais (`src/parse/_util.py`): encoding
latin-1 e vírgula decimal no FNDE; `-`/`--`/vazio → `None` (nunca 0 implícito);
IBGE de 2 dígitos = rede estadual, 7 dígitos = município.

### 3.1 `fnde.py` → `base_clean.json`
*Merge* por código IBGE de 8 publicações do FNDE, tendo a **receita total** como
espinha. Mapeamentos não triviais confirmados por paridade:
- **IEI** é publicado em % (`"54%"`) e armazenado como fração (`0,54`).
- Rede estadual: `Entidade = "GOVERNO DO ESTADO"`.
- Condicionalidades/habilitação preservam o texto bruto da fonte (inclusive `-`);
  o painel os interpreta com `_sim()`.
- `VAAR_coef`, `VAAR_valor_redes` e `VAAT_hab_status` não são consumidos pelo
  DataFrame do painel (vestigiais) e recebem valor neutro.

### 3.2 `fnde.py` → `v2025.json`
VAAR recebido em 2025 por rede, em R$ inteiro (arredondamento meio-para-cima).

### 3.3 `inep.py` → `ideb.json`
Ideb 2025 (`VL_OBSERVADO_2025`), Saeb Matemática (`VL_NOTA_MATEMATICA_2025`),
Língua Portuguesa (`VL_NOTA_PORTUGUES_2025`) e indicador de rendimento, por etapa
(AI/AF/EM). **Município** usa a linha da rede *Municipal*; **rede estadual**
(IBGE de 2 dígitos) usa o arquivo de regiões/UFs, rede *Estadual*.

### 3.4 `inep.py` → `rend.json`
Aprovação/Reprovação/Abandono (EF e EM) das colunas `1_/2_/3_CAT_FUN|MED`,
recorte Localização *Total* e Dependência *Municipal* (município) ou *Estadual* (UF).

### 3.5 `inep.py` → `inse.json`
INSE 2023 por município, lendo os estratos já agregados pelo INEP:
`inse_tot` = `TP_TIPO_REDE=6` (todas as redes) e `inse_mun` = `TP_TIPO_REDE=3`
(municipal), ambos com `TP_LOCALIZACAO=0` (total).

---

## 4. Inputs já preparados (proveniência documentada)

Não têm URL de um único arquivo e são consumidos como estão; a reconstrução os
**preserva**:

| Arquivo | Origem | Como obter |
|---|---|---|
| `conect.json` | NIC.br/SIMET — Educação Conectada | export do Base dos Dados (dataset `br_simet_educacao_conectada`, tabela `escola`) |
| `sim_atend.json` | Matrículas da etapa do IEE 2017–2023 | repositório de referência *guimaraesca/Simulador-VAAR-PI* |
| `geo/*_simpl.json` | Malhas IBGE simplificadas | geometria reduzida das malhas IBGE (apenas para os mapas) |

---

## 5. Verificação de paridade

- `python -m src.parse.build_all --check` imprime os agregados do painel sobre a
  base reconstruída.
- `tests/test_pipeline.py` compara, campo a campo, a base reconstruída com a
  distribuída (pulado automaticamente quando `data/raw` está ausente, pois os
  brutos não são versionados — rode `src/sources.py --download` antes).

Resultado atual: **paridade total** nos campos consumidos pelo painel em
`base_clean`, `v2025`, `ideb`, `rend` e `inse`.

> Como as publicações do FNDE/INEP de 2026 podem ser atualizadas na origem, uma
> execução futura pode divergir da base distribuída — isso é esperado e reflete
> dado oficial mais recente, não erro do pipeline. Os cinco pilares de
> observabilidade (ver `DOCUMENTACAO_TECNICA.md`) sinalizam essas mudanças.
