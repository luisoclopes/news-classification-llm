import pandas as pd
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

USERNAME = "natgeo"

ARQUIVO_FEED = "feed_temp.xlsx"
ARQUIVO_FINAL = "posts_2025.xlsx"

TOTAL_POSTS = 1000  # quantidade para estimativa

DATA_INICIO = datetime(2025, 1, 1)
DATA_FIM = datetime(2025, 12, 31)


# =========================
# COLETA RÁPIDA DO FEED
# =========================
def coletar_feed(page):

    dados = []
    vistos = set()

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

                img = a.locator("img").first
                alt = img.get_attribute("alt")

                if not alt:
                    continue

                dados.append({
                    "url": link,
                    "caption": alt.strip()
                })

            except:
                continue

        page.mouse.wheel(0, 6000)
        time.sleep(2)

    df = pd.DataFrame(dados)
    df.to_excel(ARQUIVO_FEED, index=False)

    return df


# =========================
# PEGAR DATA
# =========================
def pegar_data(page):
    try:
        t = page.locator("time").first.get_attribute("datetime")
        return datetime.fromisoformat(t.replace("Z", ""))
    except:
        return None


# =========================
# ESTIMATIVA AUTOMÁTICA
# =========================
def estimar_intervalo(df, page):

    print("\n🧠 Estimando intervalo de 2025...\n")

    tamanho = len(df)

    # pontos espalhados
    indices = [
        int(tamanho * 0.1),
        int(tamanho * 0.2),
        int(tamanho * 0.3),
        int(tamanho * 0.4),
        int(tamanho * 0.5),
        int(tamanho * 0.6),
        int(tamanho * 0.7),
        int(tamanho * 0.8),
        int(tamanho * 0.9),
    ]

    mapa = {}

    for idx in indices:

        row = df.iloc[idx]
        link = row["url"]

        print(f"🔎 Testando índice {idx}")

        try:
            page.goto(link)
            page.wait_for_selector("time", timeout=5000)

            data = pegar_data(page)

            if data:
                ano = data.year
                mapa[idx] = ano
                print(f"📅 {ano}")

            time.sleep(1)

        except:
            continue

    # descobrir faixa de 2025
    inicio = None
    fim = None

    for idx, ano in mapa.items():

        if ano == 2025 and inicio is None:
            inicio = idx

        if ano == 2025:
            fim = idx

    # fallback
    if inicio is None:
        inicio = int(tamanho * 0.2)

    if fim is None:
        fim = int(tamanho * 0.6)

    print(f"\n🎯 Intervalo estimado: {inicio} → {fim}\n")

    return inicio, fim


# =========================
# FILTRAR 2025
# =========================
def filtrar_2025(df, page, inicio, fim):

    resultados = []

    df = df.iloc[inicio:fim]

    print("\n📜 Coletando apenas 2025...\n")

    for _, row in df.iterrows():

        link = row["url"]
        caption = row["caption"]

        print(f"\n🔎 {link}")

        try:
            page.goto(link)
            page.wait_for_selector("time", timeout=5000)

            data = pegar_data(page)

            if not data:
                continue

            data = data.replace(tzinfo=None)

            print(f"📅 {data}")

            if DATA_INICIO <= data <= DATA_FIM:

                resultados.append({
                    "url": link,
                    "caption": caption,
                    "data": data.strftime("%Y-%m-%d")
                })

                print("✅ SALVO")

            time.sleep(1)

        except:
            continue

    pd.DataFrame(resultados).to_excel(ARQUIVO_FINAL, index=False)

    print("\n🎯 FINALIZADO")


# =========================
# MAIN
# =========================
def main():

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("🔐 Faça login no Instagram")
        page.goto("https://www.instagram.com/")
        input("👉 ENTER após login...")

        page.goto(f"https://www.instagram.com/{USERNAME}/")
        page.wait_for_selector("a[href*='/p/']", timeout=60000)

        # 1. coletar feed
        df = coletar_feed(page)

        # 2. estimar
        inicio, fim = estimar_intervalo(df, page)

        # 3. filtrar
        filtrar_2025(df, page, inicio, fim)


if __name__ == "__main__":
    main()