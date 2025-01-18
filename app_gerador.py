import pandas as pd
import streamlit as st
import random
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

# Função para calcular frequência de faixas de totais
def calcular_frequencias_totais(resultados):
    totais = {}
    for jogo in resultados:
        soma = sum(jogo)
        faixa = (soma // 50) * 50  # Define a faixa (ex: 0-50, 51-100, etc.)
        if faixa not in totais:
            totais[faixa] = 0
        totais[faixa] += 1
    return totais

# Função para calcular números parceiros mais recorrentes
def calcular_parceiros(resultados):
    parceiros = defaultdict(lambda: defaultdict(int))
    for jogo in resultados:
        for i, numero1 in enumerate(jogo):
            for numero2 in jogo[i + 1:]:
                parceiros[numero1][numero2] += 1
                parceiros[numero2][numero1] += 1
    parceiros_final = {}
    for numero, associados in parceiros.items():
        parceiros_final[numero] = sorted(associados.items(), key=lambda x: x[1], reverse=True)[:5]
    return parceiros_final

# Função para calcular combinações mais recorrentes (pares, trios e quartetos)
def calcular_combinacoes(resultados):
    combinacoes = defaultdict(int)
    for jogo in resultados:
        # Pares
        for i in range(len(jogo)):
            for j in range(i + 1, len(jogo)):
                par = tuple(sorted([jogo[i], jogo[j]]))
                combinacoes[par] += 1
        # Trios
        for i in range(len(jogo)):
            for j in range(i + 1, len(jogo)):
                for k in range(j + 1, len(jogo)):
                    trio = tuple(sorted([jogo[i], jogo[j], jogo[k]]))
                    combinacoes[trio] += 1
        # Quartetos
        for i in range(len(jogo)):
            for j in range(i + 1, len(jogo)):
                for k in range(j + 1, len(jogo)):
                    for l in range(k + 1, len(jogo)):
                        quarteto = tuple(sorted([jogo[i], jogo[j], jogo[k], jogo[l]]))
                        combinacoes[quarteto] += 1
    combinacoes_ordenadas = sorted(combinacoes.items(), key=lambda x: x[1], reverse=True)[:10]
    return combinacoes_ordenadas

# Função principal para gerar números com base nos critérios
def gerar_numeros(resultados, total_numeros=60, numeros_por_jogo=6, faixa_soma=None, parceiros=None):
    # Calcular frequências dos números
    frequencias = calcular_frequencias(resultados, total_numeros)

    # Obter os números mais frequentes
    numeros_ordenados = sorted(range(1, total_numeros + 1), key=lambda x: frequencias[x - 1], reverse=True)

    # Gerar 20 jogos sugeridos que respeitem a faixa de soma
    jogos_sugeridos = []
    for _ in range(1000):  # Limite de tentativas para gerar combinações válidas
        jogo = sorted(random.sample(numeros_ordenados[:30], numeros_por_jogo))  # Usa os 30 mais frequentes
        soma = sum(jogo)
        if faixa_soma is None or (faixa_soma[0] <= soma <= faixa_soma[1]):
            # Incorporar números parceiros mais frequentes
            for numero in jogo:
                if numero in parceiros:
                    jogo.extend([n for n, _ in parceiros[numero] if n not in jogo])
                    jogo = sorted(set(jogo))[:numeros_por_jogo]
            jogos_sugeridos.append(jogo)
            if len(jogos_sugeridos) >= 20:
                break

    return frequencias, jogos_sugeridos

# Interface no Streamlit
st.title("Gerador de Números para Loterias")

st.write("Este gerador utiliza dados históricos da Mega-Sena para sugerir combinações baseadas na análise de frequência, respeitando a faixa de soma dos números e considerando números parceiros mais frequentes.")

# Upload do arquivo Excel
uploaded_file = st.file_uploader("Faça o upload do arquivo Excel com os resultados da Mega-Sena:", type="xlsx")

if uploaded_file:
    # Ler o arquivo Excel
    df = pd.read_excel(uploaded_file)

    # Extrair os resultados dos sorteios
    resultados = df.iloc[:, 2:8].values.tolist()  # Considera que as colunas 2 a 7 contêm os números sorteados

    numeros_por_jogo = st.number_input(
        "Quantos números por jogo?", min_value=1, max_value=15, value=6
    )

    frequencias_totais = calcular_frequencias_totais(resultados)
    faixa_mais_comum = max(frequencias_totais.items(), key=lambda x: x[1])[0]  # Faixa mais comum

    faixa_soma = st.slider(
        "Selecione a faixa de soma dos números:",
        min_value=0,
        max_value=300,
        value=(faixa_mais_comum, faixa_mais_comum + 49),
        step=1
    )

    if st.button("Gerar Números"):
        frequencias = calcular_frequencias(resultados, total_numeros=60)
        frequencias_dezenas = calcular_frequencias_dezenas(resultados)
        parceiros = calcular_parceiros(resultados)
        combinacoes_recorrentes = calcular_combinacoes(resultados)
        _, jogos_sugeridos = gerar_numeros(
            resultados, total_numeros=60, numeros_por_jogo=numeros_por_jogo, faixa_soma=faixa_soma, parceiros=parceiros
        )

        st.subheader("Frequências dos Números:")
        st.bar_chart(frequencias)

        st.subheader("Frequência por Dezenas:")
        dezenas_labels = ["1-10", "11-20", "21-30", "31-40", "41-50", "51-60"]
        st.bar_chart(dict(zip(dezenas_labels, frequencias_dezenas)))

        st.subheader("Frequências das Faixas de Totais:")
        faixas_labels = {f"{k}-{k+49}": v for k, v in sorted(frequencias_totais.items())}
        st.bar_chart(faixas_labels)

        st.subheader("Números Parceiros Mais Frequentes:")
        for numero, associados in parceiros.items():
            st.write(f"Número {numero}: {[f'{n} ({c} vezes)' for n, c in associados]}")

        st.subheader("Combinações Mais Recorrentes (Pares, Trios e Quartetos):")
        for combinacao, freq in combinacoes_recorrentes:
            st.write(f"{combinacao}: {freq} vezes")

        st.subheader("20 Jogos Sugeridos:")
        for jogo in jogos_sugeridos:
            st.write(f"{jogo}")
