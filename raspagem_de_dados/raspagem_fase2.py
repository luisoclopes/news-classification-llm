import pandas as pd
import time
import os
from datetime import datetime
from playwright.sync_api import sync_playwright

ARQUIVO_INPUT = "urls_folha.xlsx"
ARQUIVO_OUTPUT = "posts_folha_2025.xlsx"
ARQUIVO_CONTROLE = "urls_processadas.txt"  # 🔥 NOVO

DATA_INICIO = datetime(2025, 1, 1)
DATA_FIM = datetime(2025, 12, 31)


# =========================
# CARREGAR PROGRESSO (2025)
# =========================
def carregar_progresso():
    if os.path.exists(ARQUIVO_OUTPUT):
        df = pd.read_excel(ARQUIVO_OUTPUT)
        print(f"♻️ Retomando dados: {len(df)} já salvos")
        return df.to_dict("records")
    return []


# =========================
# CONTROLE DE URLs (TODOS)
# =========================
def carregar_urls_processadas():
    if os.path.exists(ARQUIVO_CONTROLE):
        with open(ARQUIVO_CONTROLE, "r") as f:
            urls = set(f.read().splitlines())
            print(f"♻️ URLs já processadas: {len(urls)}")
            return urls
    return set()


def salvar_url_processada(url):
    with open(ARQUIVO_CONTROLE, "a") as f:
        f.write(url + "\n")


# =========================
# EXTRAIR DATA
# =========================
def extrair_data(page):
    try:
        t = page.locator("time").first.get_attribute("datetime")
        if not t:
            return None

        data = datetime.fromisoformat(t.replace("Z", ""))
        return data.replace(tzinfo=None)

    except:
        return None


# =========================
# EXTRAIR TEXTO + MÉTRICAS
# =========================
def extrair_og_data(page):
    try:
        content = page.locator("meta[property='og:description']").get_attribute("content")

        if not content:
            return "", None, None, None

        partes = content.split(" - ", 1)

        if len(partes) < 2:
            return content, None, None, None

        metricas = partes[0]
        texto = partes[1]

        # likes e comentários
        likes = None
        comentarios = None

        try:
            if "likes" in metricas:
                likes = int(metricas.split("likes")[0].replace(",", "").strip())

            if "comments" in metricas:
                comentarios = int(
                    metricas.split("comments")[0]
                    .split(",")[-1]
                    .replace(",", "")
                    .strip()
                )
        except:
            pass

        return texto.strip(), likes, comentarios, "folhadespaulo"

    except:
        return "", None, None, "folhadespaulo"


# =========================
# LIMPAR TEXTO
# =========================
def limpar_texto(texto):
    try:
        if ": " in texto:
            texto = texto.split(": ", 1)[1]

        return texto.strip().strip('"')

    except:
        return texto


# =========================
# MAIN
# =========================
def main():

    dados = carregar_progresso()
    urls_processadas = carregar_urls_processadas()

    df_urls = pd.read_excel(ARQUIVO_INPUT)

    total = len(df_urls)
    inicio_tempo = time.time()

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

            # 🔥 PULAR QUALQUER URL JÁ PROCESSADA
            if link in urls_processadas:
                continue

            print(f"\n🔎 {link}")

            try:
                page.goto(link, timeout=60000)
                page.wait_for_load_state("domcontentloaded")

                # 🔥 MARCA COMO PROCESSADO (ANTES DE TUDO)
                salvar_url_processada(link)
                urls_processadas.add(link)

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

                # EXTRAÇÃO
                caption, curtidas, comentarios, usuario = extrair_og_data(page)

                if not caption:
                    print("⚠️ Sem caption")
                    continue

                caption = limpar_texto(caption)

                dados.append({
                    "pagina": usuario,
                    "url": link,
                    "caption": caption,
                    "data": data.strftime("%Y-%m-%d"),
                    "curtidas": curtidas,
                    "comentarios": comentarios
                })

                print(f"✅ SALVO | 👍 {curtidas} | 💬 {comentarios}")

                # 📊 PROGRESSO + ETA
                processados = i + 1
                tempo_passado = time.time() - inicio_tempo

                if processados > 0:
                    media = tempo_passado / processados
                    restante = (total - processados) * media

                    print(f"📊 {processados}/{total} | ⏱️ ETA: {int(restante/60)} min")

                # 💾 salvamento
                if len(dados) % 20 == 0:
                    pd.DataFrame(dados).to_excel(ARQUIVO_OUTPUT, index=False)
                    print("💾 Salvamento parcial")

                time.sleep(0.4)

            except Exception as e:
                print(f"⚠️ Erro: {e}")
                continue

        pd.DataFrame(dados).to_excel(ARQUIVO_OUTPUT, index=False)

        print("\n🎯 FINALIZADO")


if __name__ == "__main__":
    main()