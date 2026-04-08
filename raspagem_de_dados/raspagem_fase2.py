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

        # 🔥 corrigir timezone bug (teu erro do 31 virar 2026)
        data = datetime.fromisoformat(data_str.replace("Z", ""))
        return data.replace(tzinfo=None)

    except:
        return None


# =========================
# EXTRAIR TEXTO REAL (CORRETO)
# =========================
def extrair_caption_real(page):

    try:
        # 🔥 seletor do container do caption
        container = page.locator("div[role='dialog']")

        spans = container.locator("span")

        textos = []

        for i in range(spans.count()):
            txt = spans.nth(i).inner_text()

            # 🔥 FILTRO INTELIGENTE
            if (
                len(txt) > 40
                and "See translation" not in txt
                and "Curtir" not in txt
                and "Like" not in txt
                and "Seguir" not in txt
            ):
                textos.append(txt)

        # juntar tudo
        caption = " ".join(textos)

        return caption.strip()

    except:
        return ""


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
                page.wait_for_selector("time", timeout=10000)

                data = extrair_data(page)

                if not data:
                    print("⚠️ Sem data")
                    continue

                print(f"📅 {data}")

                # 🔥 FILTRO DE ANO
                if data > DATA_FIM:
                    print("⏩ Ignorando (2026)")
                    continue

                if data < DATA_INICIO:
                    print("🛑 Chegou antes de 2025 — FINALIZANDO")
                    break

                # =========================
                # PEGAR TEXTO REAL
                # =========================
                caption = extrair_caption_real(page)

                if not caption:
                    print("⚠️ Caption vazio")
                    continue

                dados.append({
                    "url": link,
                    "caption": caption,
                    "data": data.strftime("%Y-%m-%d")
                })

                urls_processadas.add(link)

                print("✅ SALVO")

                # 💾 salvamento frequente (ESSENCIAL)
                if len(dados) % 20 == 0:
                    pd.DataFrame(dados).to_excel(ARQUIVO_OUTPUT, index=False)
                    print("💾 Salvamento parcial")

                # 🔥 delay anti-bloqueio
                time.sleep(1.5)

            except Exception as e:
                print(f"⚠️ Erro: {e}")
                continue

        # salvar final
        pd.DataFrame(dados).to_excel(ARQUIVO_OUTPUT, index=False)

        print("\n🎯 FINALIZADO")


if __name__ == "__main__":
    main()