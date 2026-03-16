import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox

# Carregar arquivos Excel
arquivo1 = "dataset_instagram-post-scraper_2026-03-11_16-31-48-149.xlsx"
arquivo2 = "dataset_instagram-post-scraper_2026-03-11_14-26-12-252.xlsx"
arquivo3 = "dataset_instagram-post-scraper_2026-03-11_16-42-24-303.xlsx"

df1 = pd.read_excel(arquivo1)
df2 = pd.read_excel(arquivo2)
df3 = pd.read_excel(arquivo3)

noticias1 = df1["caption"].dropna().tolist()
noticias2 = df2["caption"].dropna().tolist()
noticias3 = df3["caption"].dropna().tolist()

# Criar janela principal
root = tk.Tk()
root.title("Visualizador de Notícias")
root.geometry("1000x600")

# Criar Notebook (abas)
notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

def criar_aba(notebook, noticias, nome_arquivo):
    """Cria uma aba com lista de notícias"""
    frame_aba = ttk.Frame(notebook)
    notebook.add(frame_aba, text=nome_arquivo)
    
    # Frame superior com informações
    frame_info = ttk.Frame(frame_aba)
    frame_info.pack(fill=tk.X, padx=10, pady=10)
    
    ttk.Label(frame_info, text="Notícia:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
    label_contador = ttk.Label(frame_info, text=f"1 de {len(noticias)}", font=("Arial", 10))
    label_contador.pack(side=tk.LEFT, padx=5)
    
    # Frame com Listbox (lista de notícias)
    frame_lista = ttk.Frame(frame_aba)
    frame_lista.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    ttk.Label(frame_lista, text="Lista de Notícias:", font=("Arial", 10, "bold")).pack()
    
    listbox = tk.Listbox(frame_lista, height=25, width=40)
    listbox.pack(fill=tk.BOTH, expand=True)
    
    scrollbar = ttk.Scrollbar(frame_lista, orient=tk.VERTICAL, command=listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    listbox.config(yscrollcommand=scrollbar.set)
    
    # Preencher Listbox com notícias
    for idx, noticia in enumerate(noticias):
        preview = noticia[:60] + "..." if len(noticia) > 60 else noticia
        listbox.insert(tk.END, preview)
    
    # Frame direito com texto completo
    frame_texto = ttk.Frame(frame_aba)
    frame_texto.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    ttk.Label(frame_texto, text="Conteúdo Completo:", font=("Arial", 10, "bold")).pack()
    
    text_widget = tk.Text(frame_texto, wrap=tk.WORD, height=25)
    text_widget.pack(fill=tk.BOTH, expand=True)
    
    scrollbar_text = ttk.Scrollbar(frame_texto, orient=tk.VERTICAL, command=text_widget.yview)
    scrollbar_text.pack(side=tk.RIGHT, fill=tk.Y)
    text_widget.config(yscrollcommand=scrollbar_text.set)
    
    # Variável para rastrear notícia atual
    noticia_atual = [0]
    
    def atualizar_visualizacao(index):
        """Atualiza o texto exibido quando seleciona uma notícia"""
        noticia_atual[0] = index
        text_widget.config(state=tk.NORMAL)
        text_widget.delete("1.0", tk.END)
        text_widget.insert("1.0", noticias[index])
        text_widget.config(state=tk.DISABLED)
        label_contador.config(text=f"{index + 1} de {len(noticias)}")
        listbox.see(index)
        listbox.selection_clear(0, tk.END)
        listbox.selection_set(index)
    
    def on_listbox_select(event):
        """Callback quando seleciona item na Listbox"""
        selection = listbox.curselection()
        if selection:
            atualizar_visualizacao(selection[0])
    
    def proxima_noticia():
        """Vai para próxima notícia"""
        if noticia_atual[0] < len(noticias) - 1:
            atualizar_visualizacao(noticia_atual[0] + 1)
    
    def noticia_anterior():
        """Volta para notícia anterior"""
        if noticia_atual[0] > 0:
            atualizar_visualizacao(noticia_atual[0] - 1)
    
    # Vincular seleção da Listbox
    listbox.bind("<<ListboxSelect>>", on_listbox_select)
    
    # Frame inferior com botões
    frame_botoes = ttk.Frame(frame_aba)
    frame_botoes.pack(fill=tk.X, padx=10, pady=10)
    
    ttk.Button(frame_botoes, text="◄ Anterior", command=noticia_anterior).pack(side=tk.LEFT, padx=5)
    ttk.Button(frame_botoes, text="Próxima ►", command=proxima_noticia).pack(side=tk.LEFT, padx=5)
    
    # Carregar primeira notícia
    if len(noticias) > 0:
        atualizar_visualizacao(0)

# Criar abas para cada arquivo
criar_aba(notebook, noticias1, f"Arquivo 1 ({len(noticias1)} notícias)")
criar_aba(notebook, noticias2, f"Arquivo 2 ({len(noticias2)} notícias)")
criar_aba(notebook, noticias3, f"Arquivo 3 ({len(noticias3)} notícias)")

root.mainloop()