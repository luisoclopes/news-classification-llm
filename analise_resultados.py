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
# GRÁFICO MELHORADO (SLIDE)
# =========================
def grafico(df):
    print("\n📈 Gerando gráfico...")

    labels = [
        "Rígido Meio", "Rígido Crise",
        "Médio Meio", "Médio Crise",
        "Leve Meio", "Leve Crise"
    ]

    verdadeiros = [
        (df["rigido_meio"] == "VERDADEIRO").sum(),
        (df["rigido_crise"] == "VERDADEIRO").sum(),
        (df["medio_meio"] == "VERDADEIRO").sum(),
        (df["medio_crise"] == "VERDADEIRO").sum(),
        (df["leve_meio"] == "VERDADEIRO").sum(),
        (df["leve_crise"] == "VERDADEIRO").sum(),
    ]

    falsos = [
        (df["rigido_meio"] == "FALSO").sum(),
        (df["rigido_crise"] == "FALSO").sum(),
        (df["medio_meio"] == "FALSO").sum(),
        (df["medio_crise"] == "FALSO").sum(),
        (df["leve_meio"] == "FALSO").sum(),
        (df["leve_crise"] == "FALSO").sum(),
    ]

    totais = [v + f for v, f in zip(verdadeiros, falsos)]

    x = range(len(labels))
    largura = 0.4

    plt.figure(figsize=(12, 6))

    # barras lado a lado
    plt.bar([i - largura/2 for i in x], verdadeiros, width=largura, label="VERDADEIRO")
    plt.bar([i + largura/2 for i in x], falsos, width=largura, label="FALSO")

    # valores + porcentagem
    for i in range(len(labels)):
        if totais[i] > 0:
            perc_v = (verdadeiros[i] / totais[i]) * 100
            perc_f = (falsos[i] / totais[i]) * 100
        else:
            perc_v = perc_f = 0

        plt.text(i - largura/2, verdadeiros[i] + 1,
                 f"{verdadeiros[i]}\n({perc_v:.1f}%)",
                 ha='center', fontsize=9)

        plt.text(i + largura/2, falsos[i] + 1,
                 f"{falsos[i]}\n({perc_f:.1f}%)",
                 ha='center', fontsize=9)

    # layout melhorado
    plt.xticks(x, labels, rotation=25)
    plt.title("Distribuição de Classificações por Prompt", fontsize=16)
    plt.ylabel("Quantidade de Notícias")

    plt.grid(axis='y', linestyle='--', alpha=0.5)

    plt.legend()
    plt.tight_layout()

    # salvar imagem para slide
    plt.savefig("grafico_classificacoes.png", dpi=300)

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

    # garantir string
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