import pandas as pd
import time
import os
from datetime import datetime
from playwright.sync_api import sync_playwright

ARQUIVO_INPUT = "urls_folha.xlsx"
ARQUIVO_OUTPUT = "posts_2025.xlsx"

DATA_INICIO = datetime(2025, 1, 1)
DATA_FIM = datetime(2025, 12, 31)


# =========================
# CARREGAR PROGRESSO
# =========================
def carregar_progresso():
    if os.path.exists(ARQUIVO_OUTPUT):
        df = pd.read_excel(ARQUIVO_OUTPUT)
        urls_processadas = set(df["url"].astype(str))
        print(f"♻️ Retomando: {len(urls_processadas)} já processados")
        return df.to_dict("records"), urls_processadas
    return [], set()


# =========================
# EXTRAIR DATA
# =========================
def extrair_data(page):
    try:
        time_el = page.locator("time").first
        data_str = time_el.get_attribute("datetime")

        if not data_str:
            return None

        data = datetime.fromisoformat(data_str.replace("Z", ""))
        return data.replace(tzinfo=None)

    except:
        return None


# =========================
# EXTRAIR TEXTO + LIKES + COMENTÁRIOS (OG)
# =========================
def extrair_og_data(page):
    try:
        meta = page.locator("meta[property='og:description']")
        content = meta.get_attribute("content")

        if not content:
            return "", "N/A", "N/A"

        # exemplo:
        # "4,766 likes, 1,068 comments - folhadespaulo on December..."

        partes = content.split(" - ", 1)

        if len(partes) < 2:
            return content, "N/A", "N/A"

        metricas = partes[0]
        texto = partes[1]

        likes = "N/A"
        comentarios = "N/A"

        try:
            if "likes" in metricas:
                likes = metricas.split("likes")[0].strip()

            if "comments" in metricas:
                comentarios = metricas.split("comments")[0].split(",")[-1].strip()

        except:
            pass

        return texto.strip(), likes, comentarios

    except:
        return "", "N/A", "N/A"


# =========================
# LIMPAR TEXTO (IMPORTANTE)
# =========================
def limpar_texto(texto):
    try:
        # remove "folhadespaulo on December..."
        if ": " in texto:
            texto = texto.split(": ", 1)[1]

        # remove aspas finais
        texto = texto.strip().strip('"')

        return texto

    except:
        return texto


# =========================
# MAIN
# =========================
def main():

    dados, urls_processadas = carregar_progresso()
    df_urls = pd.read_excel(ARQUIVO_INPUT)

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("🔐 Faça login no Instagram")
        page.goto("https://www.instagram.com/")
        input("👉 ENTER após login...")

        print("\n📜 Iniciando extração...\n")

        for i, row in df_urls.iterrows():

            link = row["url"]

            if link in urls_processadas:
                continue

            print(f"\n🔎 {link}")

            try:
                page.goto(link, timeout=60000)

                # ⚡ não precisa esperar DOM inteiro
                page.wait_for_selector("meta[property='og:description']", timeout=8000)

                data = extrair_data(page)

                if not data:
                    print("⚠️ Sem data")
                    continue

                print(f"📅 {data}")

                # ignorar 2026
                if data > DATA_FIM:
                    print("⏩ Ignorando (2026)")
                    continue

                # parar em 2024
                if data < DATA_INICIO:
                    print("🛑 Chegou antes de 2025 — FINALIZANDO")
                    break

                # 🔥 EXTRAÇÃO PRINCIPAL
                caption, curtidas, comentarios = extrair_og_data(page)

                if not caption:
                    print("⚠️ Sem caption")
                    continue

                caption = limpar_texto(caption)

                dados.append({
                    "url": link,
                    "caption": caption,
                    "data": data.strftime("%Y-%m-%d"),
                    "curtidas": curtidas,
                    "comentarios": comentarios
                })

                urls_processadas.add(link)

                print(f"✅ SALVO | 👍 {curtidas} | 💬 {comentarios}")

                # 💾 salvamento frequente
                if len(dados) % 20 == 0:
                    pd.DataFrame(dados).to_excel(ARQUIVO_OUTPUT, index=False)
                    print("💾 Salvamento parcial")

                # ⚡ mais rápido e seguro
                time.sleep(1.2)

            except Exception as e:
                print(f"⚠️ Erro: {e}")
                continue

        pd.DataFrame(dados).to_excel(ARQUIVO_OUTPUT, index=False)

        print("\n🎯 FINALIZADO")


if __name__ == "__main__":
    main()