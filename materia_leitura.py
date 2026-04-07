import pandas as pd

ARQUIVO = "resultado_final_oficial.xlsx"

df = pd.read_excel(ARQUIVO)

# garantir string
df = df.astype(str)

print("\n🔎 NOTÍCIAS DIVERGENTES:\n")

for i, row in df.iterrows():

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

    divergencias = []

    if len(meio_vals) > 1:
        divergencias.append("Meio Ambiente")

    if len(crise_vals) > 1:
        divergencias.append("Crise Climática")

    if divergencias:
        print("="*80)
        print(f"📰 NOTÍCIA {i+1}")
        print(f"⚠️ Divergência em: {', '.join(divergencias)}\n")

        print("📄 TEXTO:")
        print(row["noticia"])
        print()

        print("📊 CLASSIFICAÇÕES:")
        print(f"Rígido  → Meio: {row['rigido_meio']} | Crise: {row['rigido_crise']}")
        print(f"Médio   → Meio: {row['medio_meio']} | Crise: {row['medio_crise']}")
        print(f"Leve    → Meio: {row['leve_meio']} | Crise: {row['leve_crise']}")
        print()