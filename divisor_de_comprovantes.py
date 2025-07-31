# -*- coding: utf-8 -*-

import os
import sys
import fitz  # PyMuPDF
import re
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import cv2
import numpy as np
import shutil
from tkinterdnd2 import TkinterDnD as tkDnD, DND_FILES

def corrigir_caminho(caminho):
    """Corrige problemas com separadores de caminho e verifica existência do arquivo."""
    if not caminho:
        return caminho

    if os.path.exists(caminho):
        return caminho

    tentativas = [
        caminho,
        caminho.replace('/', '\\'),
        caminho.replace('\\', '/'),
        os.path.normpath(caminho),
        os.path.abspath(caminho)
    ]

    tentativas = list(dict.fromkeys(tentativas))

    for tentativa in tentativas:
        try:
            if os.path.exists(tentativa):
                return tentativa
        except (TypeError, ValueError):
            continue

    return caminho

def resource_path(relative_path):
    """Obtém caminho absoluto para recursos."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class FileListbox(tk.Listbox):
    """Listbox com suporte a seleção múltipla e reordenação."""
    def __init__(self, master, **kw):
        kw['selectmode'] = tk.EXTENDED
        super().__init__(master, **kw)
        self.bind('<Button-1>', self.set_current)
        self.bind('<B1-Motion>', self.shift_selection)
        self.curIndex = None

    def set_current(self, event):
        self.curIndex = self.nearest(event.y)

    def shift_selection(self, event):
        i = self.nearest(event.y)
        if i < self.curIndex:
            x = self.get(i)
            self.delete(i)
            self.insert(i+1, x)
            self.curIndex = i
        elif i > self.curIndex:
            x = self.get(i)
            self.delete(i)
            self.insert(i-1, x)
            self.curIndex = i

class DragDropListbox(FileListbox):
    """Listbox com suporte a drag and drop de arquivos usando tkinterdnd2"""
    def __init__(self, master, app, **kw):
        super().__init__(master, **kw)
        self.app = app
        self.configure(
            bg='white',
            relief=tk.SUNKEN,
            borderwidth=2,
            highlightbackground='blue',
            highlightthickness=0
        )
        
        # Configuração do drag and drop
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.handle_drop)
        
        # Configura eventos visuais
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        
    def on_enter(self, event):
        self['highlightthickness'] = 2
        self['highlightbackground'] = 'blue'
        
    def on_leave(self, event):
        self['highlightthickness'] = 0
        
    def handle_drop(self, event):
        files = self.app.root.tk.splitlist(event.data)
        for f in files:
            if f.lower().endswith('.pdf'):
                clean_path = f.strip('{}')  # Remove chaves no Windows
                corrected_path = corrigir_caminho(clean_path)
                if corrected_path not in self.get(0, tk.END):
                    self.insert(tk.END, corrected_path)
                    self.app.log_message(f"Arquivo adicionado: {os.path.basename(corrected_path)}")

class PDFProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Divisor de Comprovantes PDF")
        self.root.geometry("900x750")

        try:
            self.root.iconbitmap(corrigir_caminho(resource_path(os.path.join('assets', 'app.ico'))))
        except:
            pass

        # Configuração do Tesseract
        try:
            if getattr(sys, 'frozen', False):
                pytesseract.pytesseract.tesseract_cmd = corrigir_caminho(resource_path('tesseract.exe'))
            else:
                pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        except:
            pass

        self.setup_ui()
        self.undefined_count = 0  # Contador para documentos indefinidos

    def setup_ui(self):
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text="Divisor de Comprovantes PDF", font=("Arial", 16, "bold")).pack(pady=10)

        # Área de arquivos
        self.drop_area = tk.LabelFrame(main_frame, text="Arquivos PDF (Arraste para adicionar)", padx=5, pady=5)
        self.drop_area.pack(fill=tk.X, pady=10)
        
        self.file_listbox = DragDropListbox(self.drop_area, self, height=4)
        self.file_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        button_frame = tk.Frame(self.drop_area)
        button_frame.pack(fill=tk.X, pady=5)

        browse_btn = tk.Button(button_frame, text="Adicionar Arquivos", command=self.browse_files)
        browse_btn.pack(side=tk.LEFT, padx=5)

        clear_btn = tk.Button(button_frame, text="Limpar Lista", command=self.clear_file_list)
        clear_btn.pack(side=tk.LEFT)

        # Frame de opções
        options_frame = tk.Frame(main_frame)
        options_frame.pack(fill=tk.X, pady=10)

        # Opção de mesclagem
        self.merge_var = tk.BooleanVar(value=False)
        merge_cb = tk.Checkbutton(options_frame, text="Mesclar arquivos selecionados", 
                                variable=self.merge_var, command=self.toggle_merge_mode)
        merge_cb.pack(anchor=tk.W)
        
        # Separador visual
        ttk.Separator(options_frame, orient='horizontal').pack(fill='x', pady=5)

        self.ocr_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Usar OCR quando necessário", variable=self.ocr_var).pack(anchor=tk.W)

        self.zip_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Gerar arquivo ZIP", variable=self.zip_var).pack(anchor=tk.W)

        # Área de log
        tk.Label(main_frame, text="Log de Processamento:").pack(anchor=tk.W)
        self.log_text = tk.Text(main_frame, height=15, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)

        # Barra de progresso
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(fill=tk.X, pady=5)

        # Botões de processamento
        button_frame_bottom = tk.Frame(main_frame)
        button_frame_bottom.pack(pady=10)

        process_btn = tk.Button(button_frame_bottom, text="Processar PDF(s)", command=self.process_pdfs, height=2, width=20)
        process_btn.pack(side=tk.LEFT, padx=5)

        rename_btn = tk.Button(button_frame_bottom, text="Renomear PDF(s)", command=self.rename_pdfs, height=2, width=20)
        rename_btn.pack(side=tk.LEFT)

        # Status
        self.status_var = tk.StringVar(value="Pronto - Criado por Sydney Pamplona")
        tk.Label(main_frame, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W).pack(fill=tk.X)

    def toggle_merge_mode(self):
        """Alterna o modo de mesclagem e desativa outras opções"""
        if self.merge_var.get():
            self.ocr_var.set(False)
            self.zip_var.set(False)
            # Seleciona automaticamente todos os arquivos quando a opção de mesclagem é ativada
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(0, tk.END)

    def browse_files(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
        for file_path in file_paths:
            if file_path not in self.file_listbox.get(0, tk.END):
                self.file_listbox.insert(tk.END, corrigir_caminho(file_path))
                self.log_message(f"Arquivo adicionado: {os.path.basename(file_path)}")

    def clear_file_list(self):
        self.file_listbox.delete(0, tk.END)
        self.log_message("Lista de arquivos limpa")

    def log_message(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update()

    def preprocess_image_for_ocr(self, image):
        """Melhora a qualidade da imagem para OCR"""
        img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
        img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        img = cv2.medianBlur(img, 3)
        return Image.fromarray(img)

    def extrair_texto_com_ocr(self, pdf_path, page_num):
        """Extrai texto de PDF não selecionável usando OCR."""
        try:
            pdf_path = corrigir_caminho(pdf_path)
            images = convert_from_path(pdf_path, first_page=page_num+1, last_page=page_num+1, dpi=300)
            
            if not images:
                self.log_message(f"Página {page_num+1}: Não foi possível converter para imagem")
                return ""
                
            processed_img = self.preprocess_image_for_ocr(images[0])
            custom_config = r'--oem 3 --psm 6 -l por+eng'
            texto = pytesseract.image_to_string(processed_img, config=custom_config)
            
            return texto if texto else ""
            
        except Exception as e:
            self.log_message(f"Erro no OCR (página {page_num+1}): {str(e)}")
            return ""

    def contem_4_cpfs(self, texto):
        """Verifica se o texto contém pelo menos 4 CPFs no formato XXX.XXX.XXX-XX"""
        if texto is None:
            return False
            
        cpfs = re.findall(r"\d{3}\.\d{3}\.\d{3}-\d{2}", texto)
        return len(cpfs) >= 4

    def extrair_beneficiario(self, texto, tentativa_ocr=False):
        """Extrai o nome do beneficiário do texto com tratamento para None"""
        if texto is None or texto.strip() == "":
            return "BENEFICIÁRIO_INDEFINIDO"
        
        texto = str(texto).upper()  # Converter todo o texto para maiúsculas

        # Novo critério para FGTS
        if "FGTS GRF" in texto:
            return "FGTS"

        # Novo critério para Santander - Convenio de Arrecadacao
        if "CONVENIO DE ARRECADACAO" in texto:
            match = re.search(r"PM\s+([^\n]+)", texto)
            if match:
                return match.group(1).strip()[:25]

        # Caso especial para "DA EMPRESA"
        if "DA EMPRESA" in texto:
            # Padrão 1: "NOME:" seguido de quebra de linha e depois o nome real
            padrao_nome = re.compile(r'NOME:\s*\n\s*([^\n]+)')
            match = padrao_nome.search(texto)
            if match:
                beneficiario = match.group(1).strip()
                if beneficiario and beneficiario not in ['', 'NOME']:
                    return beneficiario[:25]
            
            # Padrão 2: "NOME:" seguido do nome na mesma linha
            padrao_nome_linha = re.compile(r'NOME:\s*([^\n]+)')
            match = padrao_nome_linha.search(texto)
            if match:
                beneficiario = match.group(1).strip()
                # Remove possíveis informações adicionais após o nome
                beneficiario = re.split(r'\s{2,}|CNPJ|CPF|$', beneficiario)[0]
                if beneficiario and beneficiario not in ['', 'NOME']:
                    return beneficiario[:25]

        # 1. Caso especial para "DA EMPRESA" - busca após "NOME:"
        if texto.startswith("DA EMPRESA"):
            # Procura por "NOME:" seguido de espaços e quebras de linha
            match = re.search(r"NOME:\s*(\S.*?)(?:\n|$)", texto, re.IGNORECASE)
            if match:
                beneficiario = match.group(1).strip()
                if beneficiario and beneficiario.upper() not in ['', 'NOME']:
                    return beneficiario.upper()[:25]
        
        # 2. Casos especiais (DARF, CAGEPA)
        if "PAGAMENTO DE DARF" in texto:
            return "DARF"
        if "CAGEPA" in texto:
            return "CAGEPA"

        # 3. Padrão para "SALÁRIO" ou "SALARIOS"
        if "SALÁRIO" in texto or "SALARIOS" in texto:
            return "FOLHA"

        # 4. Padrão para Banco do Brasil - múltiplos CLIENTE:
        clientes = [m.start() for m in re.finditer("CLIENTE:", texto)]
        if len(clientes) >= 2:
            # Pega o texto após o último CLIENTE:
            ultimo_cliente_pos = clientes[-1]
            texto_apos = texto[ultimo_cliente_pos+8:]  # +8 para pular "CLIENTE:"
            beneficiario = texto_apos.split('\n')[0].strip()
            if beneficiario:
                return beneficiario.upper()[:25]
        
        # 5. Padrão para Banco do Brasil - único CLIENTE: depois FAVORECIDO:
        if "CLIENTE:" in texto and "FAVORECIDO:" in texto:
            partes = texto.split("FAVORECIDO:")
            if len(partes) > 1:
                beneficiario = partes[1].split('\n')[0].strip()
                if beneficiario:
                    return beneficiario.upper()[:25]

        # 6. Padrão para "NOME SOCIAL"
        if "NOME SOCIAL:" in texto:
            linhas = texto.split('\n')
            for i, linha in enumerate(linhas):
                if "NOME SOCIAL:" in linha and i + 1 < len(linhas):
                    beneficiario = linhas[i + 1].strip()
                    if beneficiario and beneficiario.upper() not in ['NOME', '']:
                        return beneficiario.upper()[:25]

        # 7. Padrão para "CONVENIO"
        if "CONVENIO" in texto:
            partes = texto.split("CONVENIO")
            if len(partes) > 1:
                beneficiario = partes[1].split('\n')[0].strip()
                if beneficiario:
                    return beneficiario.upper()[:25]

        # 8. Padrão para Itaú - NOME DO RECEBEDOR
        if "NOME DO RECEBEDOR:" in texto:
            partes = texto.split("NOME DO RECEBEDOR:")
            if len(partes) > 1:
                beneficiario = partes[1].split('\n')[0].strip()
                if beneficiario:
                    return beneficiario.upper()[:25]

        # 9. Padrão para "NOME FANTASIA:"
        if "NOME FANTASIA:" in texto:
            match = re.search(r"NOME FANTASIA:\s*(.*?)(?:\n|$)", texto)
            if match:
                beneficiario = match.group(1).strip()
                if beneficiario:
                    return beneficiario.upper()[:25]

            linhas = texto.split('\n')
            for i, linha in enumerate(linhas):
                if "NOME FANTASIA:" in linha and i+1 < len(linhas):
                    beneficiario = linhas[i+1].strip()
                    if beneficiario:
                        return beneficiario.upper()[:25]

        # 10. Solução para boletos Santander
        if "SANTANDER" in texto and "DADOS DO BENEFICIÁRIO ORIGINAL" in texto:
            padrao_santander = re.compile(
                r"DADOS DO BENEFICIÁRIO ORIGINAL.*?RAZÃO SOCIAL:\s*([^\n]+)",
                re.IGNORECASE | re.DOTALL
            )
            match = padrao_santander.search(texto)
            if match:
                beneficiario = match.group(1).strip()
                beneficiario = re.sub(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', '', beneficiario).strip()
                if beneficiario:
                    return beneficiario.upper()[:25]

            linhas = [linha.strip() for linha in texto.split('\n') if linha.strip()]
            for i, linha in enumerate(linhas):
                if "DADOS DO BENEFICIÁRIO ORIGINAL" in linha and i+3 < len(linhas):
                    if re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', linhas[i+1]):
                        beneficiario = linhas[i+3]
                        if not re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', beneficiario):
                            return beneficiario.upper()[:25]

        # 11. Padrões genéricos
        padroes = [
            r"FAVORECIDA:\s*(.+)",
            r"PAGO\s+PARA:?\s*(.+)",
            r"FAVORECIDO:?\s*(.+)",
            r"BENEFICI[ÁA]RIO:?\s*(.+)",
            r"NOME:?\s*(.+)",
            r"NOME DO RECEBEDOR:?\s*(.+)",
            r"CREDITADA:\s*NOME:?\s*(.+)",
            r"BENEFICIÁRIO:?\s*(.+)",
            r"TIPO DE COMPROMISSO:?\s*(.+)",
            r"DADOS DO RECEBEDOR\s*\n\s*PARA\s*(.+)",
            r"FAVORECIDO\s*\n\s*NOME:?\s*(.+)",
        ]

        for padrao in padroes:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                nome = match.group(1).split("CNPJ")[0].strip().split("\n")[0]
                nome = re.sub(r"[^\w\s]", "", nome).strip()

                if "DO PAGADOR" in nome or "FANTASIA" in nome:
                    return "BENEFICIÁRIO_INDEFINIDO"

                if "BENEFICIÁRIO ORIGINAL" in texto and nome == "ORIGINAL":
                    continue

                if nome == "NOME":
                    linhas = texto.splitlines()
                    for i, linha in enumerate(linhas):
                        if linha.strip() == "NOME:" and i + 1 < len(linhas):
                            nome = linhas[i + 1].strip()
                            break

                return nome.upper()[:25] if nome else "BENEFICIÁRIO_INDEFINIDO"

        return "BENEFICIÁRIO_INDEFINIDO"

    def extrair_valor(self, texto, tentativa_ocr=False):
        """Extrai valor do texto com tratamento para None"""
        if texto is None or texto.strip() == "":
            return "VALOR_INDEFINIDO"
            
        texto = str(texto).upper()  # Converter todo o texto para maiúsculas

        # Novo critério para "Valor Recolhido:"
        if "VALOR RECOLHIDO:" in texto:
            match = re.search(r"VALOR RECOLHIDO:\s*R?\$?\s*([\d\.,]+)", texto)
            if match:
                valor = match.group(1).replace('.', '').replace(',', '_')
                return valor.upper()

        # Novo critério para Santander - Convenio de Arrecadacao
        if "CONVENIO DE ARRECADACAO" in texto:
            match = re.search(r"R\$\s*([\d\.,]+)", texto)
            if match:
                valor = match.group(1).replace('.', '').replace(',', '_')
                return valor.upper()

        # 1. Padrão específico para Itaú - valor após CNPJ
        padrao_cnpj_valor = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}[^\d]*([\d]{1,3}(?:\.?\d{3})*,\d{2})', texto)
        if padrao_cnpj_valor:
            valor = padrao_cnpj_valor.group(1).replace('.', '').replace(',', '_')
            self.log_message("Valor identificado após CNPJ")
            return valor.upper()

        # 2. Padrão específico para Itaú - valor na linha abaixo de "(=) VALOR DO PAGAMENTO:"
        if "(=) VALOR DO PAGAMENTO:" in texto:
            linhas = texto.split('\n')
            for i, linha in enumerate(linhas):
                if "(=) VALOR DO PAGAMENTO:" in linha and i+1 < len(linhas):
                    valor_linha = linhas[i+1].strip()
                    match = re.search(r'[\d]{1,3}(?:\.?\d{3})*,\d{2}', valor_linha)
                    if match:
                        valor = match.group(0).replace('.', '').replace(',', '_')
                        return valor.upper()

        # 3. Padrão para "VALOR DA TRANSAÇÃO:"
        if "VALOR DA TRANSAÇÃO:" in texto:
            partes = texto.split("VALOR DA TRANSAÇÃO:")
            if len(partes) > 1:
                valor_part = partes[1].split('\n')[0].strip()
                match = re.search(r'[\d]{1,3}(?:\.?\d{3})*,\d{2}', valor_part)
                if match:
                    valor = match.group(0).replace('.', '').replace(',', '_')
                    return valor.upper()

        # 4. Padrões genéricos
        padroes = [
            r"\(=\)\s*VALOR\s*DO\s*PAGAMENTO\s*\(R\$\):\s*([\d\.,]+)",
            r"\(=\)\s*VALOR\s*DO\s*PAGAMENTO\s*\(R\$\):\s*\n\s*([\d\.,]+)",
            r"VALOR\s+DO\s+DOCUMENTO[:\s]*R?\$?\s*([\d\.,]+)",
            r"VALOR[:\s]*R?\$?\s*([\d\.,]+)",
            r"VALOR\s*:\s*R?\$?\s*([\d\.,]+)",
            r"VALOR DA TED[:\s]*R?\$?\s*([\d\.,]+)",
            r"VALOR DO PAGAMENTO \(R\$\):?\s*([\d\.,]+)",
            r"VALOR TOTAL PAGO[:\s]*R?\$?\s*([\d\.,]+)",
            r"VALOR TOTAL[:\s]*R?\$?\s*([\d\.,]+)",
            r"VALOR ATUALIZADO:?\s*R?\$?\s*([\d\.,]+)",
        ]
        
        for padrao in padroes:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                valor = match.group(1).replace(".", "").replace(",", "_")
                return valor.upper()
                
        return "VALOR_INDEFINIDO"

    def remove_numbering_from_filenames(self, output_dir):
        """Remove os 4 primeiros caracteres (numeração) dos nomes dos arquivos"""
        try:
            files = os.listdir(output_dir)
            renamed_count = 0
            
            for filename in files:
                if len(filename) > 4 and filename.lower().endswith('.pdf'):
                    new_name = filename[4:]
                    old_path = os.path.join(output_dir, filename)
                    new_path = os.path.join(output_dir, new_name)
                    
                    # Evita sobrescrever arquivos existentes
                    counter = 1
                    while os.path.exists(new_path):
                        name, ext = os.path.splitext(new_name)
                        new_path = os.path.join(output_dir, f"{name}_{counter}{ext}")
                        counter += 1
                    
                    os.rename(old_path, new_path)
                    renamed_count += 1
            
            self.log_message(f"✅ Numeração removida de {renamed_count} arquivos em: {output_dir}")
            return True
        except Exception as e:
            self.log_message(f"❌ Erro ao remover numeração: {str(e)}")
            return False

    def rename_pdfs(self):
        """Renomeia os PDFs selecionados com base no beneficiário e valor da primeira página"""
        if self.file_listbox.size() == 0:
            messagebox.showerror("Erro", "Por favor, adicione pelo menos um arquivo PDF")
            return

        try:
            self.status_var.set("Renomeando arquivos...")
            self.progress["value"] = 0
            self.log_message("\nIniciando renomeação de arquivos...")

            total_files = self.file_listbox.size()
            processed_files = 0

            for i in range(total_files):
                pdf_path = self.file_listbox.get(i)
                pdf_path = corrigir_caminho(pdf_path)
                
                if not os.path.exists(pdf_path):
                    self.log_message(f"Arquivo não encontrado: {os.path.basename(pdf_path)}")
                    continue

                try:
                    # Extrai o texto sem manter o arquivo aberto
                    texto = None
                    with fitz.open(pdf_path) as doc:
                        if len(doc) == 0:
                            self.log_message(f"Arquivo vazio: {os.path.basename(pdf_path)}")
                            continue
                        
                        # Extrai texto da primeira página
                        texto = doc.load_page(0).get_text()
                        
                        if (texto is None or texto.strip() == "") and self.ocr_var.get():
                            texto = self.extrair_texto_com_ocr(pdf_path, 0)
                    
                    # Fecha o arquivo antes de renomear
                    if texto is None or texto.strip() == "":
                        nome = "BENEFICIÁRIO_INDEFINIDO"
                        valor = "VALOR_INDEFINIDO"
                    else:
                        nome = self.extrair_beneficiario(texto)
                        valor = self.extrair_valor(texto)
                        
                        if self.ocr_var.get() and ("INDEFINIDO" in nome or "INDEFINIDO" in valor):
                            texto_ocr = self.extrair_texto_com_ocr(pdf_path, 0)
                            if texto_ocr:
                                if "INDEFINIDO" in nome:
                                    novo_nome = self.extrair_beneficiario(texto_ocr, True)
                                    if novo_nome != "BENEFICIÁRIO INDEFINIDO":
                                        nome = novo_nome
                                if "INDEFINIDO" in valor:
                                    novo_valor = self.extrair_valor(texto_ocr, True)
                                    if novo_valor != "VALOR_INDEFINIDO":
                                        valor = novo_valor

                    # Cria novo nome
                    dir_path = os.path.dirname(pdf_path)
                    base_name = os.path.basename(pdf_path)
                    name, ext = os.path.splitext(base_name)
                    new_name = f"{nome}_{valor}{ext}"
                    new_path = os.path.join(dir_path, new_name)
                    
                    # Evita sobrescrever arquivos existentes
                    counter = 1
                    while os.path.exists(new_path):
                        new_name = f"{nome}_{valor}_{counter}{ext}"
                        new_path = os.path.join(dir_path, new_name)
                        counter += 1
                    
                    # Renomeia o arquivo
                    os.rename(pdf_path, new_path)
                    self.log_message(f"Renomeado: {base_name} -> {new_name}")
                    processed_files += 1
                    self.progress["value"] = (processed_files / total_files) * 100
                    self.status_var.set(f"Renomeando arquivos {processed_files}/{total_files}")
                    self.root.update()

                except Exception as e:
                    self.log_message(f"Erro ao processar {os.path.basename(pdf_path)}: {str(e)}")

            self.progress["value"] = 100
            self.status_var.set("Renomeação concluída - Criado por Sydney Pamplona")
            messagebox.showinfo("Sucesso", "Renomeação concluída com sucesso!")

        except Exception as e:
            self.log_message(f"\n❌ Erro durante a renomeação: {str(e)}")
            self.status_var.set("Erro na renomeação")
            messagebox.showerror("Erro", f"Ocorreu um erro durante a renomeação:\n{str(e)}")

    def process_pdfs(self):
        """Processa todos os PDFs na lista"""
        if self.file_listbox.size() == 0:
            messagebox.showerror("Erro", "Por favor, adicione pelo menos um arquivo PDF")
            return

        try:
            self.status_var.set("Processando...")
            self.progress["value"] = 0
            self.log_message("Iniciando processamento...")
            self.undefined_count = 0  # Resetar contador de indefinidos

            if self.merge_var.get():
                self.merge_selected_files()
            else:
                total_files = self.file_listbox.size()
                processed_files = 0

                for i in range(total_files):
                    pdf_path = self.file_listbox.get(i)
                    self.process_single_pdf(pdf_path)
                    processed_files += 1
                    self.progress["value"] = (processed_files / total_files) * 100
                    self.status_var.set(f"Processando arquivo {processed_files}/{total_files}")
                    self.root.update()

            # Mostra resumo de documentos indefinidos
            self.log_message(f"\nRESUMO: {self.undefined_count} documento(s) com beneficiário/valor indefinido")

            self.progress["value"] = 100
            self.status_var.set("Processamento concluído - Criado por Sydney Pamplona")
            
            # Pergunta se deseja remover a numeração
            if not self.merge_var.get() and processed_files > 0:
                answer = messagebox.askyesno("Opção de Renomeação", 
                                           "Deseja remover a numeração dos nomes dos arquivos?")
                if answer:
                    output_dir = os.path.join(os.path.dirname(self.file_listbox.get(0)), "comprovantes_processados")
                    if os.path.exists(output_dir):
                        self.remove_numbering_from_filenames(output_dir)

        except Exception as e:
            self.log_message(f"\n❌ Erro durante o processamento: {str(e)}")
            self.status_var.set("Erro no processamento")
            messagebox.showerror("Erro", f"Ocorreu um erro durante o processamento:\n{str(e)}")

    def merge_selected_files(self):
        """Mescla os arquivos PDF selecionados em um único arquivo"""
        selected_indices = self.file_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Nenhum arquivo selecionado", "Por favor, selecione os arquivos para mesclar")
            return

        # Pergunta ao usuário onde salvar o arquivo mesclado
        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Salvar arquivo mesclado como"
        )
        
        if not output_path:  # Usuário cancelou
            return

        try:
            merger = PdfMerger()
            file_paths = []

            for i in selected_indices:
                pdf_path = self.file_listbox.get(i)
                try:
                    if os.path.exists(pdf_path):
                        with open(pdf_path, 'rb') as f:
                            merger.append(f)
                        file_paths.append(pdf_path)
                        self.log_message(f"Adicionado para mesclagem: {os.path.basename(pdf_path)}")
                    else:
                        self.log_message(f"Arquivo não encontrado: {os.path.basename(pdf_path)}")
                except Exception as e:
                    self.log_message(f"Erro ao adicionar {os.path.basename(pdf_path)}: {str(e)}")

            if len(file_paths) > 0:
                try:
                    with open(output_path, "wb") as f:
                        merger.write(f)
                    self.log_message(f"✅ Arquivos mesclados com sucesso em: {output_path}")
                    messagebox.showinfo("Sucesso", f"Arquivos mesclados com sucesso em:\n{output_path}")
                except Exception as e:
                    self.log_message(f"❌ Erro ao mesclar arquivos: {str(e)}")
                    messagebox.showerror("Erro", f"Ocorreu um erro ao mesclar os arquivos:\n{str(e)}")
                finally:
                    merger.close()
            else:
                self.log_message("Nenhum arquivo válido foi selecionado para mesclagem")
                messagebox.showwarning("Aviso", "Nenhum arquivo válido foi selecionado para mesclagem")
        except Exception as e:
            self.log_message(f"❌ Erro inesperado: {str(e)}")
            messagebox.showerror("Erro", f"Ocorreu um erro inesperado:\n{str(e)}")

    def process_single_pdf(self, pdf_path):
        """Processa um único arquivo PDF com lógica de agrupamento consistente"""
        pdf_path = corrigir_caminho(pdf_path)
        if not pdf_path:
            return

        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"Arquivo não encontrado: {pdf_path}")

            self.log_message(f"\nProcessando arquivo: {os.path.basename(pdf_path)}")

            output_dir = os.path.join(os.path.dirname(pdf_path), "comprovantes_processados")
            os.makedirs(output_dir, exist_ok=True)

            doc = fitz.open(pdf_path)
            reader = PdfReader(pdf_path)
            total_pages = len(doc)
            processos = []
            
            # Dicionário para controlar nomes duplicados
            contador_nomes = {}
            
            # Primeira passada: analisar todas as páginas
            paginas_analisadas = []
            for i in range(total_pages):
                try:
                    texto = doc.load_page(i).get_text()
                    
                    if (texto is None or texto.strip() == "") and self.ocr_var.get():
                        texto = self.extrair_texto_com_ocr(pdf_path, i)
                    
                    if texto is None or texto.strip() == "":
                        nome = "BENEFICIÁRIO_INDEFINIDO"
                        valor = "VALOR_INDEFINIDO"
                        folha = False
                        self.undefined_count += 1
                    else:
                        nome = self.extrair_beneficiario(texto)
                        valor = self.extrair_valor(texto)
                        folha = (nome == "FOLHA")
                        
                        if "INDEFINIDO" in nome or "INDEFINIDO" in valor:
                            self.undefined_count += 1
                        
                        if self.ocr_var.get() and ("INDEFINIDO" in nome or "INDEFINIDO" in valor):
                            texto_ocr = self.extrair_texto_com_ocr(pdf_path, i)
                            if texto_ocr:
                                if "INDEFINIDO" in nome:
                                    novo_nome = self.extrair_beneficiario(texto_ocr, True)
                                    if novo_nome != "BENEFICIÁRIO INDEFINIDO":
                                        nome = novo_nome
                                        self.undefined_count -= 1
                                if "INDEFINIDO" in valor:
                                    novo_valor = self.extrair_valor(texto_ocr, True)
                                    if novo_valor != "VALOR_INDEFINIDO":
                                        valor = novo_valor
                                        self.undefined_count -= 1

                    paginas_analisadas.append({
                        'numero': i + 1,
                        'nome': nome,
                        'valor': valor,
                        'folha': folha,
                        'texto': texto
                    })

                except Exception as e:
                    self.log_message(f"Erro ao analisar página {i+1}: {str(e)}")
                    paginas_analisadas.append({
                        'numero': i + 1,
                        'nome': "BENEFICIÁRIO_INDEFINIDO",
                        'valor': "VALOR_INDEFINIDO",
                        'folha': False,
                        'texto': None
                    })
                    self.undefined_count += 1

            # Segunda passada: gerar os arquivos agrupados corretamente
            i = 0
            contador = 1
            while i < total_pages:
                pagina = paginas_analisadas[i]
                
                if pagina['folha']:
                    # Agrupa páginas de folha de pagamento
                    writer = PdfWriter()
                    writer.add_page(reader.pages[i])
                    
                    # Adiciona páginas seguintes que têm 4+ CPFs
                    j = i + 1
                    while j < total_pages:
                        texto_pagina = paginas_analisadas[j]['texto']
                        if texto_pagina and self.contem_4_cpfs(texto_pagina):
                            writer.add_page(reader.pages[j])
                            j += 1
                        else:
                            break
                    
                    # Define o nome do arquivo
                    nome_arquivo = f"{contador:03d}_FOLHA_{pagina['valor']}.pdf"
                    path_out = os.path.join(output_dir, nome_arquivo)
                    
                    with open(path_out, "wb") as f:
                        writer.write(f)
                    processos.append(path_out)
                    contador += 1
                    
                    i = j  # Pula para a próxima página não processada
                else:
                    # Página individual normal
                    writer = PdfWriter()
                    writer.add_page(reader.pages[i])
                    
                    # Gera um nome único baseado no conteúdo
                    chave = f"{pagina['nome']}_{pagina['valor']}"
                    contador_nomes[chave] = contador_nomes.get(chave, 0) + 1
                    
                    nome_arquivo = f"{contador:03d}_{pagina['nome']}_{pagina['valor']}.pdf"
                    
                    path_out = os.path.join(output_dir, nome_arquivo)
                    
                    with open(path_out, "wb") as f:
                        writer.write(f)
                    processos.append(path_out)
                    contador += 1
                    
                    i += 1  # Vai para a próxima página

            if self.zip_var.get() and processos:
                zip_name = os.path.join(os.path.dirname(pdf_path), 
                                    f"comprovantes_divididos_{os.path.splitext(os.path.basename(pdf_path))[0]}.zip")
                with zipfile.ZipFile(zip_name, 'w') as z:
                    for arq in processos:
                        z.write(arq, os.path.basename(arq))
                self.log_message(f"Arquivo ZIP criado: {zip_name}")

            self.log_message(f"✅ Processo finalizado para {os.path.basename(pdf_path)}! Arquivos salvos em: {output_dir}")
            self.log_message(f"Total de arquivos gerados: {len(processos)}")

        except Exception as e:
            self.log_message(f"❌ Erro ao processar {os.path.basename(pdf_path)}: {str(e)}")
            raise
        finally:
            if 'doc' in locals():
                doc.close()

if __name__ == "__main__":
    root = tkDnD.Tk()
    app = PDFProcessorApp(root)
    root.mainloop()
