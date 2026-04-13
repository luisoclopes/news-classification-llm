import pandas as pd
import time
import os
from playwright.sync_api import sync_playwright

USERNAME = "folhadespaulo"
TOTAL_POSTS = 12500

ARQUIVO = "urls_folha.xlsx"


# =========================
# CARREGAR PROGRESSO
# =========================
def carregar_progresso():

    if os.path.exists(ARQUIVO):
        df = pd.read_excel(ARQUIVO)
        vistos = set(df["url"].astype(str))
        dados = df.to_dict("records")

        print(f"♻️ Retomando: {len(dados)} URLs já coletadas")
        return dados, vistos

    return [], set()


# =========================
# SALVAR
# =========================
def salvar(dados):
    pd.DataFrame(dados).to_excel(ARQUIVO, index=False)


# =========================
# MAIN
# =========================
def main():

    dados, vistos = carregar_progresso()

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("🔐 Faça login no Instagram")
        page.goto("https://www.instagram.com/")
        input("👉 ENTER após login...")

        page.goto(f"https://www.instagram.com/{USERNAME}/")
        page.wait_for_selector("a[href*='/p/']", timeout=60000)

        print("\n📜 Coletando URLs...\n")

        while len(dados) < TOTAL_POSTS:

            anchors = page.locator("a[href*='/p/']")
            total = anchors.count()

            print(f"🔗 Visíveis: {total} | Coletados: {len(dados)}")

            for i in range(total):

                try:
                    a = anchors.nth(i)
                    href = a.get_attribute("href")

                    if not href:
                        continue

                    link = f"https://www.instagram.com{href}"

                    if link in vistos:
                        continue

                    vistos.add(link)

                    dados.append({"url": link})

                except:
                    continue

            # 💾 salva SEMPRE (checkpoint real)
            salvar(dados)

            # scroll
            page.mouse.wheel(0, 8000)
            time.sleep(2)

        salvar(dados)
        print("\n🎯 Finalizado")


if __name__ == "__main__":
    main()