import pandas as pd

arquivo = "resultado_final_oficial.xlsx"

df = pd.read_excel(arquivo)

def normalizar(valor):
    if str(valor).lower() in ["1", "true", "verdadeiro"]:
        return "VERDADEIRO"
    if str(valor).lower() in ["0", "false", "falso"]:
        return "FALSO"
    return valor

colunas_bool = [
    "rigido_meio", "rigido_crise",
    "medio_meio", "medio_crise",
    "leve_meio", "leve_crise"
]

for col in colunas_bool:
    if col in df.columns:
        df[col] = df[col].apply(normalizar)

df.to_excel("resultado_final_corrigido.xlsx", index=False)

print("✅ Arquivo corrigido gerado!")