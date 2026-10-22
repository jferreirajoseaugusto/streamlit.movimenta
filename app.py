import io
 
import pandas as pd
import plotly.express as px
import streamlit as st
 
# Dados embutidos no código (Anatel, reproduzidos pelo Teleco: teleco.com.br/blarga1.asp).
# Valores em milhares de acessos de banda larga fixa.
DADOS_CSV = """Ano;Tecnologia;Acessos_mil
2014;ATM;268
2015;ATM;231
2016;ATM;219
2014;Cable Modem;7561
2015;Cable Modem;8254
2016;Cable Modem;8576
2014;Ethernet;287
2015;Ethernet;322
2016;Ethernet;406
2014;Fibra;948
2015;Fibra;1292
2016;Fibra;1734
2014;FWA;80
2015;FWA;80
2016;FWA;91
2014;HFC;25
2015;HFC;29
2016;HFC;41
2014;LTE;138
2015;LTE;304
2016;LTE;344
2014;Satélite;61
2015;Satélite;67
2016;Satélite;66
2014;Spread Spectrum;1341
2015;Spread Spectrum;1611
2016;Spread Spectrum;1779
2014;WiMAX;11
2015;WiMAX;16
2016;WiMAX;18
2014;xDSL;13227
2015;xDSL;13256
2016;xDSL;13382
2014;Outras;23
2015;Outras;21
2016;Outras;19
"""
 
 
def br(x, casas=0):
    """Formata número no padrão brasileiro: 1.234,5"""
    texto = "{:,.{c}f}".format(x, c=casas)
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")
 
 
def sinal(x):
    return ("+" if x > 0 else "") + br(x)
 
 
st.set_page_config(page_title="Banda larga fixa por tecnologia", layout="wide")
st.title("Banda larga fixa no Brasil, por tecnologia (2014 a 2016)")
st.write(
    "Este dashboard mostra quantos acessos de banda larga fixa existiam em cada tecnologia "
    "(em milhares) e como isso mudou entre 2014 e 2016. Fonte: Anatel, reproduzida pelo Teleco "
    "(teleco.com.br/blarga1.asp)."
)
 
arquivo = st.file_uploader("Quer usar outro CSV? Envie aqui (colunas: Ano, Tecnologia, Acessos_mil; separador ;)", type=["csv"])
 
try:
    if arquivo is not None:
        df = pd.read_csv(arquivo, sep=";", encoding="utf-8-sig")
    else:
        df = pd.read_csv(io.StringIO(DADOS_CSV), sep=";")
except Exception as e:
    st.error("Não foi possível ler o arquivo: " + str(e))
    st.stop()
 
df.columns = [str(c).strip() for c in df.columns]
colunas = ["Ano", "Tecnologia", "Acessos_mil"]
faltando = [c for c in colunas if c not in df.columns]
if faltando:
    st.error("O arquivo precisa ter as colunas Ano, Tecnologia e Acessos_mil. Faltando: " + ", ".join(faltando))
    st.stop()
 
df["Tecnologia"] = df["Tecnologia"].astype(str).str.strip()
df["Ano"] = pd.to_numeric(df["Ano"], errors="coerce")
df["Acessos_mil"] = pd.to_numeric(df["Acessos_mil"], errors="coerce")
df = df.dropna(subset=["Ano", "Acessos_mil"])
if df.empty:
    st.error("O arquivo não tem dados válidos.")
    st.stop()
df["Ano"] = df["Ano"].astype(int)
 
anos = sorted(df["Ano"].unique())
tecs = sorted(df["Tecnologia"].unique())
 
st.sidebar.header("Filtros")
ano_sel = st.sidebar.selectbox("Ano (gráfico de barras)", anos, index=len(anos) - 1)
tec_sel = st.sidebar.multiselect("Tecnologias (gráfico de linhas)", tecs, default=tecs)
 
dado_ano = df[df["Ano"] == ano_sel]
dado_tec = df[df["Tecnologia"].isin(tec_sel)]
 
total_ano = dado_ano["Acessos_mil"].sum()
c1, c2, c3 = st.columns(3)
c1.metric("Total de acessos em " + str(ano_sel), br(total_ano) + " mil")
c2.metric("Tecnologias no arquivo", len(tecs))
c3.metric("Período", str(anos[0]) + " a " + str(anos[-1]))
 
# ---------- Gráfico 1 ----------
st.subheader("1. Quais tecnologias têm mais acessos? (" + str(ano_sel) + ")")
g1 = dado_ano.sort_values("Acessos_mil", ascending=False)
fig1 = px.bar(g1, x="Tecnologia", y="Acessos_mil", text="Acessos_mil",
              title="Acessos de banda larga fixa por tecnologia em " + str(ano_sel),
              labels={"Acessos_mil": "Acessos (milhares)"})
st.plotly_chart(fig1, use_container_width=True)
if total_ano > 0:
    top = g1.iloc[0]
    base = g1.iloc[-1]
    st.markdown(
        "**O que podemos observar?** Em " + str(ano_sel) + ", a tecnologia com mais acessos é **" + top["Tecnologia"]
        + "** (" + br(top["Acessos_mil"]) + " mil, " + br(top["Acessos_mil"] / total_ano * 100, 1)
        + "% do total) e a com menos é **" + base["Tecnologia"] + "** (" + br(base["Acessos_mil"])
        + " mil). Isso descreve os dados; não explica o motivo."
    )
 
# ---------- Gráfico 2 ----------
st.subheader("2. Como os acessos mudaram ao longo dos anos?")
if dado_tec.empty:
    st.warning("Selecione ao menos uma tecnologia na barra lateral.")
else:
    fig2 = px.line(dado_tec.sort_values("Ano"), x="Ano", y="Acessos_mil", color="Tecnologia", markers=True,
                   title="Evolução dos acessos por tecnologia",
                   labels={"Acessos_mil": "Acessos (milhares)"})
    fig2.update_xaxes(dtick=1)
    st.plotly_chart(fig2, use_container_width=True)
    pivo = dado_tec.pivot_table(index="Tecnologia", columns="Ano", values="Acessos_mil", aggfunc="sum")
    a0 = pivo.columns.min()
    a1 = pivo.columns.max()
    pivo = pivo[pivo[a0] > 0].dropna(subset=[a0, a1])
    if a0 != a1 and not pivo.empty:
        cresc = ((pivo[a1] - pivo[a0]) / pivo[a0] * 100).sort_values(ascending=False)
        absol = (pivo[a1] - pivo[a0]).sort_values(ascending=False)
        st.markdown(
            "**O que podemos observar?** Entre " + str(a0) + " e " + str(a1)
            + ", o maior crescimento percentual entre as tecnologias selecionadas foi o de **" + cresc.index[0]
            + "** (" + sinal(cresc.iloc[0]) + "%), e o maior aumento em número de acessos foi o de **" + absol.index[0]
            + "** (" + sinal(absol.iloc[0]) + " mil). A maior queda em acessos foi a de **" + absol.index[-1]
            + "** (" + sinal(absol.iloc[-1]) + " mil). Variações percentuais altas podem vir de um ponto de partida pequeno."
        )
 
with st.expander("Ver os dados"):
    st.text(df.to_string(index=False))
st.caption("Valores em milhares de acessos. Limitação: dados de 2014 a 2016, fonte secundária (Teleco, com base na Anatel).")
 