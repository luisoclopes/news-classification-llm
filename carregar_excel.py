import pandas as pd

# caminho do arquivo
arquivo1 = "dataset_instagram-post-scraper_2026-03-11_16-31-48-149.xlsx"
arquivo2 = "dataset_instagram-post-scraper_2026-03-11_14-26-12-252.xlsx"
arquivo3 = "dataset_instagram-post-scraper_2026-03-11_16-42-24-303.xlsx"

# carregar excel
df1 = pd.read_excel(arquivo1)
df2 = pd.read_excel(arquivo2)
df3 = pd.read_excel(arquivo3)

for noticia in df1["caption"]:
    print(noticia)
    print()

for noticia in df2["caption"]:
    print(noticia)
    print()

for noticia in df3["caption"]:
    print(noticia)
    print()