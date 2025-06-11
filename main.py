import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import timedelta

# ----------------------------
# Funções com cache (evita baixar os dados toda hora)
# ----------------------------

# Carrega os tickers do arquivo CSV e adiciona o sufixo ".SA" pra acessar via Yahoo Finance
@st.cache_data
def carregar_tickers_acoes():
    base_tickers = pd.read_csv(r"C:\Users\Lucas\OneDrive\Arquivos diversos\Desktop\dashboard com stream\IBOV (1).csv", sep=";")
    tickers = [f"{item}.SA" for item in base_tickers["Código"].tolist()]
    return tickers

# Baixa o histórico de preços de fechamento das ações
@st.cache_data
def carregar_dados(empresas):
    dados_acao = yf.Tickers(" ".join(empresas))
    hist = dados_acao.history(period="1d", start="2010-01-01", end="2024-07-01")
    close_df = hist['Close']  # Só pega os dados de fechamento
    return close_df

# ----------------------------
# Carregamento de dados
# ----------------------------

acoes = carregar_tickers_acoes()
dados = carregar_dados(acoes)

st.write("""
# App Preço de Ações
O gráfico abaixo representa a evolução do preço das ações ao longo dos anos
""")

st.sidebar.header("Filtros")

# Multiselect para escolher quais ações exibir
lista_acoes = st.sidebar.multiselect("Escolha as ações para visualizar", dados.columns.tolist())

# Se o usuário não escolher nenhuma ação, para a execução
if lista_acoes:
    dados_filtrados = dados[lista_acoes]
else:
    st.warning("Selecione pelo menos uma ação para visualizar.")
    st.stop()

# ----------------------------
# Filtro de datas baseado no DataFrame já filtrado
# ----------------------------

data_inicial = dados_filtrados.index.min().to_pydatetime()
data_final = dados_filtrados.index.max().to_pydatetime()

intervalo_data = st.sidebar.slider(
    "Selecione o período",
    min_value=data_inicial,
    max_value=data_final,
    value=(data_inicial, data_final),
    step=timedelta(days=1)
)

# Aplica o filtro de datas
dados_filtrados = dados_filtrados.loc[intervalo_data[0]:intervalo_data[1]]

# ----------------------------
# Gráfico + cálculo de performance
# ----------------------------

if not dados_filtrados.empty:
    st.line_chart(dados_filtrados)

    texto_performance_ativos = ""

    # Garante que tenha pelo menos uma ação na lista
    if len(lista_acoes) == 0:
        lista_acoes = list(dados.columns)

    # Caso só uma ação tenha sido escolhida, renomeia por precaução (parece sobrou de testes)
    elif len(lista_acoes) == 1:
        acao_unica = lista_acoes[0]
        dados = dados.rename(columns={"close": acao_unica})  # Essa linha parece não fazer nada útil no contexto atual

    # Cria uma carteira onde cada ativo começa com R$1000
    carteira = [1000 for acao in lista_acoes]
    total_inicial_carteira = sum(carteira)

    # Loop pra calcular a performance individual de cada ativo
    for i, acao in enumerate(lista_acoes):
        performance_ativo = dados[acao].iloc[-1] / dados[acao].iloc[0] - 1
        performance_ativo = float(performance_ativo)

        # Atualiza o valor da carteira com a performance
        carteira[i] = carteira[i] * (1 + performance_ativo)

        # Monta o texto de retorno com cor
        if performance_ativo > 0:
            texto_performance_ativos += f"  \n{acao}: :green[{performance_ativo:.1%}]"
        elif performance_ativo < 0:
            texto_performance_ativos += f"  \n{acao}: :red[{performance_ativo:.1%}]"
        else:
            texto_performance_ativos += f"  \n{acao}: {performance_ativo:.1%}"

    # Calcula a performance geral da carteira
    total_final_carteira = sum(carteira)
    perfomance_carteira = total_final_carteira / total_inicial_carteira - 1  

    # Texto com performance geral
    if perfomance_carteira > 0:
        texto_performance_carteira = f"Perfomance da carteira de todos os ativos :green[{perfomance_carteira:.1%}]"
    elif perfomance_carteira < 0:
        texto_performance_carteira = f"Perfomance da carteira de todos os ativos :red[{perfomance_carteira:.1%}]"
    else:
        texto_performance_carteira = f"Perfomance da carteira de todos os ativos {perfomance_carteira:.1%}"

    # Exibe o resultado no app
    st.write(f"""
    ### Performance dos Ativos
    Essa foi a performance de cada ativo no período selecionado:

    {texto_performance_ativos}

    {texto_performance_carteira}
    """)

else:
    st.warning("Nenhum dado disponível para as ações selecionadas.")
