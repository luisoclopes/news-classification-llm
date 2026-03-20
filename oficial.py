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
# FUNÇÃO PARA EXCEL (BOOLEAN → TEXTO)
# =========================
def bool_to_str(valor):
    if valor is True:
        return "VERDADEIRO"
    if valor is False:
        return "FALSO"
    return valor


# =========================
# Modelo
# =========================
class Classificacao(BaseModel):
    MeioAmbiente: Optional[bool]
    CriseAmbiental: Optional[bool]
    Justificativa: str

    @field_validator("Justificativa")
    def nao_vazia(cls, v):
        if not v or len(v.strip()) < 5:
            return "Justificativa ausente"
        return v


# =========================
# Parser
# =========================
def extrair_json(texto):
    try:
        match = re.search(r'\{.*?\}', texto, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except:
        pass

    meio = False
    crise = False

    if re.search(r'meio.*true', texto, re.I):
        meio = True

    if re.search(r'crise.*true', texto, re.I):
        crise = True

    justificativa_match = re.search(r'justificativa[:\-]?\s*(.*)', texto, re.I)

    justificativa = (
        justificativa_match.group(1).strip()
        if justificativa_match else "Não foi possível extrair justificativa"
    )

    return {
        "MeioAmbiente": meio,
        "CriseAmbiental": crise,
        "Justificativa": justificativa
    }


# =========================
# Classificação
# =========================
def classificar(caption, prompt_tipo, tentativas=5):

    if prompt_tipo == "rigido":
        instrucao = "Relação deve ser direta. Se houver dúvida → false."
    elif prompt_tipo == "medio":
        instrucao = "Relação pode ser direta ou contextual. Se dúvida leve → true."
    else:
        instrucao = "Qualquer relação plausível → true. Só false se não houver relação."

    PROMPT = f"""
Classifique a notícia em:

1) Meio Ambiente
2) Crise Ambiental

Crise ambiental inclui:
- aquecimento global
- eventos extremos
- desastres ambientais
- colapso ambiental

Regra:
- Crise ambiental ⊂ Meio ambiente

{instrucao}

Responda em JSON:
{{
"MeioAmbiente": true ou false,
"CriseAmbiental": true ou false,
"Justificativa": "explicação única"
}}

Notícia:
{caption}
"""

    for tentativa in range(tentativas):
        try:
            resposta = ollama.chat(
                model="llama3.2:3b",
                messages=[{"role": "user", "content": PROMPT}],
                options={"temperature": 0}
            )

            conteudo = resposta["message"]["content"]
            dados = extrair_json(conteudo)

            if dados.get("CriseAmbiental"):
                dados["MeioAmbiente"] = True

            return Classificacao(**dados)

        except Exception:
            print(f"⚠️ [{prompt_tipo}] tentativa {tentativa+1} falhou...")

    return Classificacao(
        MeioAmbiente=None,
        CriseAmbiental=None,
        Justificativa="ERRO_PROCESSAMENTO"
    )


# =========================
# FUNÇÃO PARA SALVAR (CONVERSÃO FINAL)
# =========================
def salvar_excel(df, caminho):
    df = df.copy()

    colunas_bool = [
        "rigido_meio", "rigido_crise",
        "medio_meio", "medio_crise",
        "leve_meio", "leve_crise"
    ]

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

arquivo_saida = "resultado_final_oficial.xlsx"
arquivo_parcial = "parcial_resultado.xlsx"

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
# LOOP PRINCIPAL
# =========================
for i, row in df_total.iterrows():

    caption = str(row.get("caption", ""))
    link = str(row.get("url", ""))
    pagina = row.get("ownerUsername", "")

    if link in urls_processadas:
        continue

    print(f"\n🔎 [{i+1}/{len(df_total)}] - {link}")

    if not caption or len(caption.strip()) < 10:
        rigido = medio = leve = Classificacao(
            MeioAmbiente=False,
            CriseAmbiental=False,
            Justificativa="Texto insuficiente"
        )
    else:
        rigido = classificar(caption, "rigido")
        medio = classificar(caption, "medio")
        leve = classificar(caption, "leve")

    resultados.append({
        "noticia": caption,
        "pagina": pagina,
        "url": link,

        "rigido_meio": rigido.MeioAmbiente,
        "rigido_crise": rigido.CriseAmbiental,
        "rigido_justificativa": rigido.Justificativa,

        "medio_meio": medio.MeioAmbiente,
        "medio_crise": medio.CriseAmbiental,
        "medio_justificativa": medio.Justificativa,

        "leve_meio": leve.MeioAmbiente,
        "leve_crise": leve.CriseAmbiental,
        "leve_justificativa": leve.Justificativa,
    })

    urls_processadas.add(link)

    if (i + 1) % 10 == 0:
        df_temp = pd.DataFrame(resultados)

        salvar_excel(df_temp, arquivo_saida)
        salvar_excel(df_temp, arquivo_parcial)

        print("💾 Checkpoint + parcial atualizados")


# =========================
# SALVAMENTO FINAL
# =========================
df_final = pd.DataFrame(resultados)

salvar_excel(df_final, arquivo_saida)
salvar_excel(df_final, arquivo_parcial)

# =========================
# REPROCESSAR ERROS
# =========================
print("\n♻️ Verificando erros para reprocessar...")

df_final = pd.read_excel(arquivo_saida)

erros = df_final[
    (df_final["rigido_justificativa"] == "ERRO_PROCESSAMENTO") |
    (df_final["medio_justificativa"] == "ERRO_PROCESSAMENTO") |
    (df_final["leve_justificativa"] == "ERRO_PROCESSAMENTO")
]

print(f"⚠️ Erros encontrados: {len(erros)}")

for idx in erros.index:
    caption = str(df_final.loc[idx, "noticia"])

    print(f"\n🔄 Reprocessando índice {idx}")

    rigido = classificar(caption, "rigido")
    medio = classificar(caption, "medio")
    leve = classificar(caption, "leve")

    df_final.at[idx, "rigido_meio"] = rigido.MeioAmbiente
    df_final.at[idx, "rigido_crise"] = rigido.CriseAmbiental
    df_final.at[idx, "rigido_justificativa"] = rigido.Justificativa

    df_final.at[idx, "medio_meio"] = medio.MeioAmbiente
    df_final.at[idx, "medio_crise"] = medio.CriseAmbiental
    df_final.at[idx, "medio_justificativa"] = medio.Justificativa

    df_final.at[idx, "leve_meio"] = leve.MeioAmbiente
    df_final.at[idx, "leve_crise"] = leve.CriseAmbiental
    df_final.at[idx, "leve_justificativa"] = leve.Justificativa

    salvar_excel(df_final, arquivo_saida)

print("\n✅ Reprocessamento concluído!")

# =========================
# BACKUP
# =========================
timestamp = time.strftime("%Y%m%d_%H%M%S")
backup_nome = f"backup_resultado_{timestamp}.xlsx"

salvar_excel(df_final, backup_nome)

print(f"\n🛡️ Backup criado: {backup_nome}")

# =========================
# FINAL
# =========================
fim_total = time.time()
print(f"\n🚀 Tempo total: {fim_total - inicio_total:.2f}s")