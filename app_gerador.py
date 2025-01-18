import pandas as pd
import streamlit as st
import random
import requests
from io import BytesIO
from collections import defaultdict

# Função para calcular frequências
def calcular_frequencias(resultados, total_numeros):
    frequencias = [0] * total_numeros
    for jogo in resultados:
        for numero in jogo:
            frequencias[numero - 1] += 1
    return frequencias

# Função para calcular frequência por dezenas
def calcular_frequencias_dezenas(resultados):
    dezenas = [0] * 6  # Para dezenas 1-10, 11-20, ..., 51-60
    for jogo in resultados:
        for numero in jogo:
            indice = (numero - 1) // 10
            dezenas[indice] += 1
    return dezenas

# Função para calcular probabilidades condicionais entre números
def calcular_probabilidades_condicionais(resultados):
    condicional = defaultdict(lambda: defaultdict(int))
    total_ocorrencias = defaultdict(int)

    for jogo in resultados:
        for i, numero1 in enumerate(jogo):
            total_ocorrencias[numero1] += 1
            for numero2 in jogo[i + 1:]:
                condicional[numero1][numero2] += 1
                condicional[numero2][numero1] += 1

    # Calcular probabilidades condicionais
    probabilidades = {}
    for numero1, associados in condicional.items():
        probabilidades[numero1] = {
            numero2: associados[numero2] / total_ocorrencias[numero1]
            for numero2 in associados
        }
    return probabilidades

# Função principal para gerar números com base nas técnicas combinadas
def gerar_numeros(resultados, total_numeros=60, numeros_por_jogo=6):
    # Calcular frequências dos números
    frequencias = calcular_frequencias(resultados, total_numeros)

    # Calcular probabilidades condicionais
    probabilidades_condicionais = calcular_probabilidades_condicionais(resultados)

    # Obter os números mais frequentes
    numeros_ordenados = sorted(range(1, total_numeros + 1), key=lambda x: frequencias[x - 1], reverse=True)

    # Gerar 20 jogos sugeridos usando as técnicas combinadas
    jogos_sugeridos = []
    explicacoes = []
    for _ in range(20):
        jogo = sorted(random.sample(numeros_ordenados[:30], numeros_por_jogo))  # Usa os 30 mais frequentes

        explicacao_jogo = []

        # Ajustar o jogo usando probabilidades condicionais
        for numero in jogo:
            if numero in probabilidades_condicionais:
                associados = sorted(
                    probabilidades_condicionais[numero].items(), key=lambda x: x[1], reverse=True
                )
                for associado, prob in associados:
                    if associado not in jogo and len(jogo) < numeros_por_jogo:
                        jogo.append(associado)
                        jogo = sorted(set(jogo))[:numeros_por_jogo]
                        explicacao_jogo.append(f"Número {associado} foi escolhido porque o número {numero} aparece junto com ele em {prob:.2%} das vezes.")
                        break

        jogos_sugeridos.append(sorted(jogo))
        explicacoes.append(explicacao_jogo)

    return frequencias, probabilidades_condicionais, jogos_sugeridos, explicacoes

# Interface no Streamlit
st.title("Gerador de Números para Loterias")

st.write("Este gerador utiliza análise de frequência e probabilidades condicionais para sugerir combinações de números.")

st.subheader("Como funciona o gerador:")
st.markdown(
    """
    1. **Análise de Frequência**: O gerador analisa os resultados históricos da loteria para identificar os números que foram sorteados com maior frequência.
    2. **Probabilidades Condicionais**: Ele também avalia quais números tendem a aparecer juntos em sorteios anteriores, calculando a probabilidade de co-ocorrência.
    3. **Geração de Jogos**: A partir dessas análises, o gerador:
       - Prioriza os números mais frequentes.
       - Adiciona números com base em probabilidades condicionais para formar jogos balanceados.
    4. **Explicações Detalhadas**: Para cada jogo gerado, o aplicativo fornece explicações de por que certos números foram incluídos, destacando a relação entre eles.
    """
)

# Fazer download do arquivo Excel via request
url_excel = "https://loterias.caixa.gov.br/Paginas/Mega-Sena.aspx"
st.write("Obtendo os resultados diretamente da fonte oficial...")
response = requests.get(url_excel)
if response.status_code == 200:
    df = pd.read_excel(BytesIO(response.content))

    # Extrair os resultados dos sorteios
    resultados = df.iloc[:, 2:8].values.tolist()  # Considera que as colunas 2 a 7 contêm os números sorteados

    numeros_por_jogo = st.number_input(
        "Quantos números por jogo?", min_value=1, max_value=15, value=6
    )

    if st.button("Gerar Números"):
        frequencias, probabilidades_condicionais, jogos_sugeridos, explicacoes = gerar_numeros(
            resultados, total_numeros=60, numeros_por_jogo=numeros_por_jogo
        )

        st.subheader("Frequências dos Números:")
        st.bar_chart(frequencias)

        st.subheader("Probabilidades Condicionais:")
        for numero, associados in probabilidades_condicionais.items():
            associados_ordenados = sorted(associados.items(), key=lambda x: x[1], reverse=True)[:5]
            st.write(f"Número {numero}: {[f'{n} ({p:.2%})' for n, p in associados_ordenados]}")

        st.subheader("20 Jogos Sugeridos:")
        for jogo, explicacao in zip(jogos_sugeridos, explicacoes):
            st.write(f"{jogo}")
            for detalhe in explicacao:
                st.caption(detalhe)
else:
    st.error("Não foi possível obter os resultados. Verifique o link ou tente novamente mais tarde.")
