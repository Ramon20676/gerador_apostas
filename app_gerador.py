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
def calcular_frequencias_dezenas(resultados, total_numeros):
    dezenas = [0] * (total_numeros // 10 + 1)
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
def gerar_numeros(resultados, total_numeros, numeros_por_jogo):
    # Calcular frequências dos números
    frequencias = calcular_frequencias(resultados, total_numeros)

    # Calcular probabilidades condicionais
    probabilidades_condicionais = calcular_probabilidades_condicionais(resultados)

    # Obter os números mais frequentes
    numeros_ordenados = sorted(range(1, total_numeros + 1), key=lambda x: frequencias[x - 1], reverse=True)

    # Evitar jogos duplicados
    resultados_existentes = [sorted(jogo) for jogo in resultados]

    # Gerar 20 jogos sugeridos usando as técnicas combinadas
    jogos_sugeridos = []
    explicacoes = []
    while len(jogos_sugeridos) < 20:
        # Randomiza o primeiro número entre os mais frequentes
        primeiro_numero = random.choice(numeros_ordenados[:30])
        jogo = [primeiro_numero]

        explicacao_jogo = [
            f"O número {primeiro_numero} foi escolhido como ponto de partida devido à sua alta frequência nos sorteios."
        ]

        # Adicionar números usando probabilidades condicionais
        while len(jogo) < numeros_por_jogo:
            ultimo_numero = jogo[-1]
            if ultimo_numero in probabilidades_condicionais:
                associados = sorted(
                    probabilidades_condicionais[ultimo_numero].items(), key=lambda x: x[1], reverse=True
                )
                for associado, prob in associados:
                    if associado not in jogo:
                        jogo.append(associado)
                        explicacao_jogo.append(
                            f"O número {associado} foi incluído porque o número {ultimo_numero} aparece junto com ele em {prob:.2%} das vezes."
                        )
                        break
            else:
                # Se não houver probabilidades condicionais, completa com os mais frequentes
                for numero in numeros_ordenados:
                    if numero not in jogo:
                        jogo.append(numero)
                        explicacao_jogo.append(
                            f"O número {numero} foi incluído para completar o jogo com base na análise de frequência."
                        )
                        break

        jogo = sorted(jogo)
        if jogo not in resultados_existentes and jogo not in jogos_sugeridos:
            jogos_sugeridos.append(jogo)
            explicacoes.append(explicacao_jogo)

    return frequencias, probabilidades_condicionais, jogos_sugeridos, explicacoes

# Interface no Streamlit
st.title("Gerador de Números para Loterias")

# Botão para escolher o tipo de loteria
tipo_loteria = st.radio("Selecione a loteria:", ("Mega-Sena", "Lotofácil"))

if tipo_loteria == "Mega-Sena":
    total_numeros = 60
    numeros_por_jogo = 6
    url_excel = "https://servicebus2.caixa.gov.br/portaldeloterias/api/resultados/download?modalidade=Mega-Sena"
else:
    total_numeros = 25
    numeros_por_jogo = 15
    url_excel = "https://servicebus2.caixa.gov.br/portaldeloterias/api/resultados/download?modalidade=Lotof%C3%A1cil"

st.write(f"Obtendo os resultados da {tipo_loteria} diretamente da fonte oficial...")
response = requests.get(url_excel)
if response.status_code == 200:
    df = pd.read_excel(BytesIO(response.content))

    # Ajustar as colunas de acordo com o tipo de loteria
    if tipo_loteria == "Mega-Sena":
        resultados = df.iloc[:, 2:8].values.tolist()  # Mega-Sena: 6 números
    else:
        resultados = df.iloc[:, 2:17].values.tolist()  # Lotofácil: 15 números

    if st.button(f"Gerar Números para {tipo_loteria}"):
        frequencias, probabilidades_condicionais, jogos_sugeridos, explicacoes = gerar_numeros(
            resultados, total_numeros=total_numeros, numeros_por_jogo=numeros_por_jogo
        )

        st.subheader("Frequências dos Números:")
        st.bar_chart(frequencias)

        st.subheader("Probabilidades Condicionais:")
        for numero, associados in probabilidades_condicionais.items():
            associados_ordenados = sorted(associados.items(), key=lambda x: x[1], reverse=True)[:5]
            st.write(f"Número {numero}: {[f'{n} ({p:.2%})' for n, p in associados_ordenados]}")

        st.subheader(f"20 Jogos Sugeridos para {tipo_loteria}:")
        for jogo, explicacao in zip(jogos_sugeridos, explicacoes):
            st.write(f"{jogo}")
            for detalhe in explicacao:
                st.caption(detalhe)
else:
    st.error("Não foi possível obter os resultados. Verifique o link ou tente novamente mais tarde.")

