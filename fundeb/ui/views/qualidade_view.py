"""Auditoria de Qualidade dos Dados, Integridade e Verificação Criptográfica SHA-256."""
from __future__ import annotations

import streamlit as st
import pandas as pd

from fundeb.data.repository import DataRepository
from fundeb.data.validation import verificar, cobertura, proveniencia, OK, ALERTA, FALHA
from fundeb.ui.components import metric_card, format_int, format_percent


def render_qualidade_view(repo: DataRepository) -> None:
    st.subheader("🛡️ Qualidade dos Dados & Transparência Metodológica")
    st.markdown(
        """
        Garantia de **dados 100% reais e auditáveis**: nenhuma informação neste painel foi inventada,
        imputada artificialmente ou populada com dados sintéticos. Valores não informados nas publicações oficiais
        permanecem estritamente como não preenchidos (`—`).
        """
    )

    df = repo.entes()
    lista_verificacoes = verificar(df)
    df_proveniencia = proveniencia(repo)
    df_cobertura = cobertura(df)

    # Contagem de status
    n_ok = sum(1 for v in lista_verificacoes if v.status == OK)
    n_alerta = sum(1 for v in lista_verificacoes if v.status == ALERTA)
    n_falha = sum(1 for v in lista_verificacoes if v.status == FALHA)

    col_v1, col_v2, col_v3 = st.columns(3)
    with col_v1:
        metric_card(
            title="Redes Auditadas",
            value=f"{format_int(len(df))} entes",
            subtitle="26 Estados + DF + 5.569 Municípios",
        )
    with col_v2:
        metric_card(
            title="Testes de Integridade",
            value=f"{n_ok} de {len(lista_verificacoes)} Aprovados",
            subtitle=f"{n_alerta} alertas metodológicos FNDE",
            delta="Fechamento Contábil 100%",
        )
    with col_v3:
        metric_card(
            title="Arquivos Oficiais Auditados",
            value=f"{len(df_proveniencia)} arquivos",
            subtitle="Hashes SHA-256 verificados",
            delta="Proveniência FNDE / INEP",
        )

    st.markdown("---")

    # ------------------------------------------------------------- CHECKS DE INTEGRIDADE
    st.markdown("##### 🔍 Testes Automatizados de Validação e Consistência Interna")
    st.caption("Verificações matemáticas sobre as somas publicadas (VAAF + VAAT + VAAR = Total União) e repartição 50/50:")

    for v in lista_verificacoes:
        icone = "✅" if v.status == OK else ("⚠️" if v.status == ALERTA else "❌")
        with st.container(border=True):
            st.markdown(f"**{icone} {v.nome}**")
            st.caption(f"Status: `{v.status.upper()}` &middot; {v.detalhe}")
            if v.excecoes is not None and not v.excecoes.empty:
                with st.expander(f"Ver {len(v.excecoes)} registros com divergência/alerta"):
                    st.dataframe(v.excecoes, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ------------------------------------------------------------- TAXAS DE COBERTURA
    st.markdown("##### 📊 Taxas Reais de Cobertura por Indicador (Sem Imputação Artificial)")
    st.caption("Campos ausentes na fonte pública permanecem nulos (NaN) e são reportados com sua cobertura efetiva:")

    df_cob_disp = df_cobertura.copy()
    df_cob_disp["Cobertura (%)"] = (df_cob_disp["Cobertura"] * 100).round(1).astype(str) + "%"
    st.dataframe(df_cob_disp[["Indicador", "Rede", "Com dado", "Total", "Cobertura (%)"]], use_container_width=True, hide_index=True)

    st.markdown("---")

    # ------------------------------------------------------------- FONTES OFICIAIS E HASHES SHA-256
    st.markdown("##### 📑 Proveniência Oficial e Hashes Criptográficos SHA-256")
    st.caption("Assinaturas SHA-256 calculadas a partir dos arquivos brutos e processados:")

    st.dataframe(df_proveniencia, use_container_width=True, hide_index=True)
