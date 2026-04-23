import pandas as pd
import ollama
import json
import re
import time
import os
from glob import glob
from typing import Optional
from pydantic import BaseModel, field_validator

# =========================
# CONFIG
# =========================
MODEL_NAME = "gemma4:e2b"
TESTE_RAPIDO = True  # 🔥 MUDA PARA False DEPOIS

# =========================
# FUNÇÃO PARA EXCEL
# =========================
def bool_to_str(valor):
    if valor is True:
        return "VERDADEIRO"
    if valor is False:
        return "FALSO"
    return valor


# =========================
# MODELO
# =========================
class Classificacao(BaseModel):
    MeioAmbiente: Optional[bool]
    CriseClimatica: Optional[bool]
    Justificativa: str

    @field_validator("Justificativa")
    def nao_vazia(cls, v):
        if not v or len(v.strip()) < 5:
            return "Justificativa ausente"
        return v


# =========================
# PARSER ROBUSTO
# =========================
def extrair_json(texto):
    try:
        match = re.search(r'\{.*?\}', texto, re.DOTALL)
        if match:
            dados = json.loads(match.group(0))
            return dados
    except:
        pass

    # fallback
    meio = bool(re.search(r'meio.*true', texto, re.I))
    crise = bool(re.search(r'crise.*true', texto, re.I))

    justificativa_match = re.search(r'justificativa[:\-]?\s*(.*)', texto, re.I)

    justificativa = (
        justificativa_match.group(1).strip()
        if justificativa_match else "Não foi possível extrair justificativa"
    )

    return {
        "MeioAmbiente": meio,
        "CriseClimatica": crise,
        "Justificativa": justificativa
    }


# =========================
# CLASSIFICAÇÃO
# =========================
def classificar(caption):

    PROMPT = f"""
Responda APENAS com JSON válido.

Formato:
{{
"MeioAmbiente": true ou false,
"CriseClimatica": true ou false,
"Justificativa": "texto curto"
}}

Regras:
- CriseClimatica implica MeioAmbiente
- Use true ou false (booleano)

Texto:
{caption}
"""

    try:
        resposta = ollama.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": PROMPT}],
            options={
                "temperature": 0,
                "num_ctx": 4096,
                "think": False  # 🔥 ESSENCIAL
            }
        )

        conteudo = resposta["message"]["content"]
        dados = extrair_json(conteudo)

        # normalização
        dados["MeioAmbiente"] = str(dados.get("MeioAmbiente")).lower() in ["true", "1"]
        dados["CriseClimatica"] = str(dados.get("CriseClimatica")).lower() in ["true", "1"]

        if dados["CriseClimatica"]:
            dados["MeioAmbiente"] = True

        return Classificacao(**dados)

    except Exception as e:
        print(f"⚠️ Erro: {e}")
        return Classificacao(
            MeioAmbiente=None,
            CriseClimatica=None,
            Justificativa="ERRO_PROCESSAMENTO"
        )


# =========================
# SALVAR
# =========================
def salvar_excel(df, caminho):
    df = df.copy()

    colunas_bool = ["meio", "crise"]

    for col in colunas_bool:
        if col in df.columns:
            df[col] = df[col].apply(bool_to_str)

    df.to_excel(caminho, index=False)


# =========================
# MAIN
# =========================
inicio_total = time.time()

arquivos = sorted(glob("data/*.xlsx"))
print(f"\n📂 Arquivos encontrados: {len(arquivos)}")

dfs = []
for arquivo in arquivos:
    print(f"📄 Lendo: {arquivo}")
    df = pd.read_excel(arquivo)
    df.columns = df.columns.str.strip()
    dfs.append(df)

df_total = pd.concat(dfs, ignore_index=True)
print(f"\n📊 Total de notícias: {len(df_total)}")

# 🔥 TESTE RÁPIDO
if TESTE_RAPIDO:
    df_total = df_total.head(50)
    print("⚡ MODO TESTE: apenas 50 notícias")

arquivo_saida = "resultado_gemma.xlsx"

# =========================
# CHECKPOINT
# =========================
if os.path.exists(arquivo_saida):
    print("\n♻️ Carregando progresso anterior...")
    df_existente = pd.read_excel(arquivo_saida)

    urls_processadas = set(df_existente["url"].astype(str))
    resultados = df_existente.to_dict("records")

    print(f"✅ Já processadas: {len(urls_processadas)}")
else:
    urls_processadas = set()
    resultados = []

# =========================
# LOOP
# =========================
for i, row in df_total.iterrows():

    caption = str(row.get("caption", ""))
    link = str(row.get("url", ""))

    if link in urls_processadas:
        continue

    print(f"\n🔎 [{i+1}/{len(df_total)}]")

    if not caption or len(caption.strip()) < 10:
        resultado = Classificacao(
            MeioAmbiente=False,
            CriseClimatica=False,
            Justificativa="Texto insuficiente"
        )
    else:
        resultado = classificar(caption)

    resultados.append({
        "url": link,
        "noticia": caption,
        "meio": resultado.MeioAmbiente,
        "crise": resultado.CriseClimatica,
        "justificativa": resultado.Justificativa
    })

    urls_processadas.add(link)

    print(f"✅ Meio: {resultado.MeioAmbiente} | Crise: {resultado.CriseClimatica}")

    # checkpoint
    if (i + 1) % 10 == 0:
        df_temp = pd.DataFrame(resultados)
        salvar_excel(df_temp, arquivo_saida)
        print("💾 Checkpoint salvo")

# =========================
# FINAL
# =========================
df_final = pd.DataFrame(resultados)
salvar_excel(df_final, arquivo_saida)

fim_total = time.time()

print("\n🎯 FINALIZADO")
print(f"🚀 Tempo total: {fim_total - inicio_total:.2f}s")