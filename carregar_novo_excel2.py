import pandas as pd
import ollama
import json
import re
import time
from pydantic import BaseModel, field_validator

# =========================
# Modelo FORTE
# =========================
class Classificacao(BaseModel):
    MeioAmbiente: bool
    Justificativa: str

    @field_validator("Justificativa")
    def nao_vazia(cls, v):
        if not v or len(v.strip()) < 5:
            raise ValueError("Justificativa vazia ou muito curta")
        return v


# =========================
# Extrair JSON
# =========================
def extrair_json(texto):
    match = re.search(r'\{.*\}', texto, re.DOTALL)
    return match.group(0) if match else None


# =========================
# Classificação com retry
# =========================
def classificar(caption, tentativas=3):
    for tentativa in range(tentativas):

        PROMPT = f"""
Classifique se a notícia está relacionada ao MEIO AMBIENTE.

Considere temas como:
desmatamento, poluição, mudanças climáticas, biodiversidade,
sustentabilidade, queimadas, recursos naturais.

Regra:
- A relação pode ser direta OU indiretamente relevante
- Se o tema impacta o meio ambiente de alguma forma → true
- Se não houver relação perceptível → false

Responda em JSON no formato:
{{"MeioAmbiente": true ou false, "Justificativa": "explicação clara"}}

Notícia:
{caption}
"""


        resposta = ollama.chat(
            model="llama3.2:3b",
            messages=[{"role": "user", "content": PROMPT}],
            options={"temperature": 0}
        )

        conteudo_bruto = resposta["message"]["content"]
        conteudo = conteudo_bruto.replace("```json", "").replace("```", "").strip()

        json_extraido = extrair_json(conteudo)

        if not json_extraido:
            json_extraido = conteudo_bruto

        try:
            dados = json.loads(json_extraido)

            if isinstance(dados.get("MeioAmbiente"), str):
                dados["MeioAmbiente"] = dados["MeioAmbiente"].lower() == "true"

            return Classificacao(**dados)

        except Exception:
            print(f"⚠️ tentativa {tentativa+1} falhou...")

    return None


# =========================
# MAIN
# =========================
inicio_total = time.time()

arquivos = [
    "dataset_instagram-post-scraper_2026-03-11_14-26-12-252.xlsx",
    "dataset_instagram-post-scraper_2026-03-11_16-31-48-149.xlsx",
    "dataset_instagram-post-scraper_2026-03-11_16-42-24-303.xlsx"
]

dfs = []

for arquivo in arquivos:
    print(f"\n📂 Lendo: {arquivo}")
    df = pd.read_excel(arquivo)
    df.columns = df.columns.str.strip()
    dfs.append(df)

df_total = pd.concat(dfs, ignore_index=True)

print(f"\n📊 Total de notícias: {len(df_total)}")


# =========================
# 🔥 LISTA DE RESULTADOS
# =========================
resultados = []


# =========================
# LOOP PRINCIPAL
# =========================
for i, row in df_total.iterrows():
    inicio_noticia = time.time()

    caption = str(row.get("caption", ""))
    link = row.get("url", "")
    pagina = row.get("ownerUsername", "")

    print(f"\n🔎 [{i+1}/{len(df_total)}]")
    print("🌐 URL:", link)
    print("📱 Página:", pagina)
    print("📰 NOTÍCIA:\n", caption)

    # 🚫 filtro
    if not caption or len(caption.strip()) < 10 or len(caption.split()) <= 3:
        print("\n⚠️ Notícia muito curta → FALSE")

        meio_ambiente = False
        justificativa = "Notícia muito curta ou sem conteúdo suficiente."

    else:
        resultado = classificar(caption)

        if resultado:
            meio_ambiente = resultado.MeioAmbiente
            justificativa = resultado.Justificativa

            print("\n✅ RESULTADO:")
            print("Meio ambiente:", meio_ambiente)
            print("Justificativa:", justificativa)

        else:
            print("\n❌ FALHOU DE VEZ")

            meio_ambiente = False
            justificativa = "Falha na classificação"

    # =========================
    # 💾 SALVAR RESULTADO
    # =========================
    resultados.append({
        "noticia": caption,
        "pagina": pagina,
        "url": link,
        "meio_ambiente": meio_ambiente,
        "justificativa": justificativa
    })

    # 💾 salvamento parcial (a cada 20)
    if (i + 1) % 20 == 0:
        pd.DataFrame(resultados).to_excel("resultado_parcial_medio.xlsx", index=False)
        print("💾 Salvamento parcial...")

    fim_noticia = time.time()
    print(f"\n⏱️ Tempo: {fim_noticia - inicio_noticia:.2f}s")
    print("\n" + "="*60)


# =========================
# 💾 SALVAMENTO FINAL
# =========================
df_resultado = pd.DataFrame(resultados)
df_resultado.to_excel("resultado_final_medio.xlsx", index=False)

fim_total = time.time()

print("\n✅ Planilha salva como resultado_final_medio.xlsx")
print(f"\n🚀 Tempo total: {fim_total - inicio_total:.2f} segundos")