# Painel Estratégico FUNDEB & Complementação VAAR 2026

Aplicação web e analítica desenvolvida para diagnóstico, simulação e prestação de contas do **FUNDEB** e da **Complementação VAAR** (Valor Aluno Ano Resultado), ciclo de distribuição 2026.

Construída segundo princípios de **engenharia de software (SOLID)**, **design de experiência de usuário (UX widescreen)**, **auditoria criptográfica de dados 100% reais** e **fórmulas matemáticas transparentes** alinhadas à Lei nº 14.113/2020 e à Nota Técnica Inep nº 23/2022.

---

## 🚀 Como Executar Localmente

### Pré-requisitos
- Python 3.9+ instalado (recomendado Python 3.11 ou 3.12/3.14).

### 1. Criar e Ativar Ambiente Virtual
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 3. Executar o Painel Streamlit
```bash
streamlit run app.py
```
O painel abrirá automaticamente em `http://localhost:8501`.

---

## 🌐 Como Publicar no Streamlit Community Cloud (`streamlit.app`)

O projeto está 100% configurado e pronto para deploy direto e gratuito na nuvem do Streamlit:

1. Suba o repositório para o seu GitHub:
   ```bash
   git add .
   git commit -m "feat: painel fundeb vaar com arquitetura solid e simulador"
   git branch -M main
   git remote add origin https://github.com/SEU_USUARIO/fundeb-painel.git
   git push -u origin main
   ```
2. Acesse [share.streamlit.io](https://share.streamlit.io).
3. Conecte sua conta GitHub e selecione o repositório `fundeb-painel`.
4. Defina:
   - **Main file path:** `app.py`
   - **Python version:** 3.11 ou 3.12
5. Clique em **Deploy!** Seu painel estará online no endereço `https://SEU_APP.streamlit.app`.

---

## 🏛️ Arquitetura de Software (SOLID)

A base de código foi estruturada em camadas independentes para desacoplar a lógica de negócio da camada de apresentação:

```
fundeb-painel/
├── app.py                     # Entrypoint do Streamlit
├── requirements.txt           # Dependências de produção
├── .streamlit/
│   └── config.toml            # Tema visual, cores e widescreen
├── fundeb/
│   ├── config.py              # Constantes de caminho e configuração
│   ├── domain/                # Entidades e Fórmulas Puras (Single Responsibility)
│   │   ├── formulas.py        # w = 2 - exp(-4*IND), IEE cenários, IAE, IPA
│   │   ├── legal.py           # Art. 14, § 1º (I a V), Rampa EC 108/2020
│   │   └── territorio.py      # Códigos IBGE, UFs e Grandes Regiões
│   ├── data/                  # Repositório e Validações (Dependency Inversion)
│   │   ├── sources.py         # Catálogo de fontes oficiais com proveniência
│   │   ├── repository.py      # Protocolo DataRepository e JsonDataRepository
│   │   └── validation.py      # Auditoria de integridade e SHA-256
│   ├── services/              # Casos de Uso de Negócio
│   │   ├── analytics.py       # Agregações nacionais, gargalos de condicionalidade
│   │   └── simulator.py       # Motor de simulação VAAR (Estadual vs Municipal)
│   └── ui/                    # Apresentação e Telas (Open/Closed)
│       ├── theme.py           # Estilos CSS widescreen e modo apresentação
│       ├── components.py      # Cards de KPI, badges e formatadores BRL
│       └── views/             # Telas do painel
│           ├── home_view.py               # Guia de Leitura e Modo Apresentação
│           ├── boletim_view.py            # Boletim Executivo em 2 Páginas (Few)
│           ├── condicionalidades_view.py  # Funil de reprovação (Cond. 3: 1.930, etc.)
│           ├── mapas_view.py              # Mapas em 3 Fases (Brasil, Região, Município)
│           ├── ranking_view.py            # Ranking de UFs com cores e micrográficos
│           ├── historico_view.py          # Rampa EC 108/2020 e Guia Como Agir
│           ├── simulador_view.py          # Simulador Estadual vs Municipal
│           └── qualidade_view.py          # Auditoria de integridade e SHA-256
├── DOCUMENTACAO_TECNICA.md    # Linhagem dos dados (Data Lineage), auditoria e fórmulas
└── tests/                     # 22 Testes automatizados de fórmulas, serviços e ABNT
```

---

## 📚 Documentação Técnica & Linhagem dos Dados (Data Lineage)

Para uma compreensão aprofundada da proveniência campo a campo, integridade contábil e auditoria matemática das funções da Nota Técnica Inep nº 23/2022, consulte o documento completo:

👉 **[DOCUMENTACAO_TECNICA.md](DOCUMENTACAO_TECNICA.md)**

Para reconstruir a base **do zero** (download das fontes oficiais FNDE/INEP/IBGE → `data/processed`), com paridade verificada, consulte o pipeline completo:

👉 **[PIPELINE.md](PIPELINE.md)** — `python src/sources.py --download && python -m src.parse.build_all --check`

Para a proposta de evolução (plataforma multidimensional para redes e MEC, ETL e relatórios PDF):

👉 **[PROPOSTA_EVOLUCAO.md](PROPOSTA_EVOLUCAO.md)**

---

## 📐 Fórmulas Matemáticas & Metodologia

O painel utiliza as funções puras documentadas na **Nota Técnica Inep nº 23/2022** e no repositório de referência [*guimaraesca/Simulador-VAAR-PI*](https://github.com/guimaraesca/Simulador-VAAR-PI):

1. **Peso da Matrícula no VAAR:**
   $$w = 2 - e^{-4 \cdot \text{IND}}$$
   Onde $w \in [1.0, 2.0]$. Quando o indicador é zero, o peso é 1. Quando o indicador tende ao infinito, o peso converge assintoticamente para 2.

2. **Diferenciação Estrita por Esfera:**
   - **Rede Estadual:** A etapa de atendimento avaliada no IEE é o **Ensino Médio** (matrículas e taxas de abandono).
   - **Rede Municipal:** A etapa avaliada no IEE é a **Educação Infantil** (Creche e Pré-Escola).

3. **Divisão Legal de Recursos:**
   - 50% dos recursos do VAAR são alocados pela parcela de **Atendimento**.
   - 50% dos recursos são alocados pela parcela de **Aprendizagem com Redução de Desigualdades**.

---

## 🛡️ Garantia de Dados 100% Reais (Sem Imputação Fake)

Todos os 5.596 entes federados (26 Estados + DF + 5.569 Municípios) foram auditados:
- **Fechamento Contábil Perfeito:** Em 100% dos entes, $\text{VAAF} + \text{VAAT} + \text{VAAR} = \text{Total Complementação União}$.
- **Repartição 50/50 Confirmada:** A soma nacional de Atendimento e Aprendizagem fecha com precisão centesimal.
- **Zero Dados Sintéticos:** Campos não publicados pelos órgãos oficiais são mantidos estritamente como nulos (`—`) e suas taxas de cobertura são exibidas com transparência na tela de Qualidade.
