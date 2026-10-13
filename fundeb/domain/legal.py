"""Parâmetros normativos — apenas o que é verificável em lei.

Nada aqui é estimado. Cada constante cita a norma de origem.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Condicionalidade:
    codigo: str          # coluna no dataset (c1..c5)
    inciso: str          # inciso do art. 14, § 1º
    titulo: str          # rótulo curto
    texto_legal: str     # transcrição da Lei nº 14.113/2020
    como_cumprir: str    # leitura operacional do dispositivo (não é dado)
    depende_do_estado: bool = False


CONDICIONALIDADES: tuple[Condicionalidade, ...] = (
    Condicionalidade(
        "c1", "I", "Gestor escolar por mérito e desempenho",
        "Provimento do cargo ou função de gestor escolar de acordo com critérios técnicos de mérito e "
        "desempenho ou a partir de escolha realizada com a participação da comunidade escolar dentre "
        "candidatos aprovados previamente em avaliação de mérito e desempenho.",
        "Editar/atualizar lei ou ato normativo do ente com critérios técnicos de mérito e desempenho "
        "para a seleção de diretores e registrar a comprovação no sistema do MEC no prazo do ciclo.",
    ),
    Condicionalidade(
        "c2", "II", "Participação mínima de 80% no Saeb",
        "Participação de pelo menos 80% dos estudantes de cada ano escolar periodicamente avaliado em "
        "cada escola ou rede de ensino nos exames nacionais do sistema nacional de avaliação da "
        "educação básica.",
        "Planejar a aplicação do Saeb escola a escola (lista nominal, busca ativa no dia da prova, "
        "reaplicação quando prevista) para que cada ano avaliado alcance ao menos 80% de presença.",
    ),
    Condicionalidade(
        "c3", "III", "Redução das desigualdades educacionais",
        "Redução das desigualdades educacionais socioeconômicas e raciais medidas nos exames nacionais "
        "do sistema nacional de avaliação da educação básica, respeitadas as especificidades da "
        "educação escolar indígena e suas realidades.",
        "Direcionar recomposição de aprendizagem aos estudantes de menor nível socioeconômico e aos "
        "estudantes pretos, pardos e indígenas, monitorando os resultados por grupo entre as edições "
        "do Saeb (metodologia de verificação definida pelo Inep).",
    ),
    Condicionalidade(
        "c4", "IV", "Regime de colaboração (ICMS Educação)",
        "Regime de colaboração entre Estado e Município formalizado na legislação estadual e em "
        "execução, nos termos do inciso II do parágrafo único do art. 158 da Constituição Federal e do "
        "art. 3º da Emenda Constitucional nº 108/2020.",
        "Depende de lei estadual que distribua parte da cota-parte municipal do ICMS com base em "
        "indicadores educacionais. Municípios devem articular-se com o governo estadual.",
        depende_do_estado=True,
    ),
    Condicionalidade(
        "c5", "V", "Referenciais curriculares alinhados à BNCC",
        "Referenciais curriculares alinhados à Base Nacional Comum Curricular, aprovados nos termos do "
        "respectivo sistema de ensino.",
        "Aprovar o documento curricular alinhado à BNCC Geral (10 Competências, Direitos/Campos na Ed. Infantil, "
        "Áreas e Habilidades no EF e FGB/Itinerários no EM) acompanhado dos anexos obrigatórios (Educação Especial Inclusiva/DUA, "
        "Relações Étnico-Raciais ERER Leis 10.639 e 11.645, Modalidades do Campo/Indígena/Quilombola e Educação Digital) no "
        "Conselho de Educação competente (CME/CEE), publicar a homologação em Diário Oficial e comprovar no Simec.",
    ),
)

CONDICIONALIDADE_POR_CODIGO = {c.codigo: c for c in CONDICIONALIDADES}

#: Implementação progressiva da complementação da União, em pontos percentuais da receita
#: total dos fundos (VAAF, VAAT, VAAR). Fonte: EC nº 108/2020 (ADCT, art. 60) e Lei nº 14.113/2020.
RAMPA_COMPLEMENTACAO: dict[int, tuple[float, float, float]] = {
    2021: (10.0, 2.0, 0.0),
    2022: (10.0, 5.0, 0.0),
    2023: (10.0, 6.25, 0.75),
    2024: (10.0, 7.5, 1.5),
    2025: (10.0, 9.0, 2.0),
    2026: (10.0, 10.5, 2.5),
}
FONTE_RAMPA = "EC nº 108/2020 (ADCT, art. 60) e Lei nº 14.113/2020"
