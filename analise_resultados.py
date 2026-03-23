import pandas as pd
import matplotlib.pyplot as plt

ARQUIVO = "resultado_final_oficial.xlsx"


# =========================
# CONTAGEM DETALHADA
# =========================
def contagem_completa(df):
    print("\n📊 CONTAGEM COMPLETA:\n")

    colunas = {
        "Rígido": ["rigido_meio", "rigido_crise"],
        "Médio": ["medio_meio", "medio_crise"],
        "Leve": ["leve_meio", "leve_crise"]
    }

    resultados = {}

    for tipo, cols in colunas.items():
        resultados[tipo] = {}

        for col in cols:
            verdadeiro = (df[col] == "VERDADEIRO").sum()
            falso = (df[col] == "FALSO").sum()

            resultados[tipo][col] = {
                "VERDADEIRO": verdadeiro,
                "FALSO": falso
            }

            print(f"{tipo} - {col}:")
            print(f"   VERDADEIRO: {verdadeiro}")
            print(f"   FALSO: {falso}\n")

    return resultados


# =========================
# GRÁFICO (VERDADEIRO vs FALSO)
# =========================
def grafico(df):
    print("\n📈 Gerando gráfico...")

    labels = []
    verdadeiros = []
    falsos = []

    colunas = [
        "rigido_meio", "rigido_crise",
        "medio_meio", "medio_crise",
        "leve_meio", "leve_crise"
    ]

    for col in colunas:
        labels.append(col)
        verdadeiros.append((df[col] == "VERDADEIRO").sum())
        falsos.append((df[col] == "FALSO").sum())

    x = range(len(labels))

    plt.figure()
    plt.bar(x, verdadeiros, label="VERDADEIRO")
    plt.bar(x, falsos, bottom=verdadeiros, label="FALSO")

    plt.xticks(x, labels, rotation=45)
    plt.title("Distribuição de classificações")
    plt.legend()
    plt.tight_layout()
    plt.show()


# =========================
# DIVERGÊNCIA
# =========================
def analisar_divergencia(df):
    print("\n⚖️ Analisando divergência...")

    divergentes = []

    for _, row in df.iterrows():

        meio_vals = {
            row["rigido_meio"],
            row["medio_meio"],
            row["leve_meio"]
        }

        crise_vals = {
            row["rigido_crise"],
            row["medio_crise"],
            row["leve_crise"]
        }

        if len(meio_vals) > 1 or len(crise_vals) > 1:
            divergentes.append(row["url"])

    print(f"⚠️ Total de notícias divergentes: {len(divergentes)}")

    # salvar
    pd.DataFrame({"url": divergentes}).to_excel(
        "links_divergentes.xlsx", index=False
    )

    print("💾 Arquivo salvo: links_divergentes.xlsx")

    return divergentes


# =========================
# MAIN
# =========================
def main():
    print("🚀 Iniciando análise...\n")

    df = pd.read_excel(ARQUIVO)

    # 🔥 garantir string
    df = df.astype(str)

    # 1. contagem
    contagem_completa(df)

    # 2. gráfico
    grafico(df)

    # 3. divergência
    analisar_divergencia(df)

    print("\n🎯 Finalizado!")


if __name__ == "__main__":
    main()