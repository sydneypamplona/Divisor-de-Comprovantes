# -*- coding: utf-8 -*-

import os
import sys
import fitz  # PyMuPDF
import re
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import cv2
import numpy as np

def corrigir_caminho(caminho):
    """
    Tenta corrigir problemas com separadores de caminho e verifica a existência do arquivo.
    Retorna o caminho corrigido se bem-sucedido, ou o original caso contrário.
    """
    if not caminho:
        return caminho

    # Verifica se o caminho já existe
    if os.path.exists(caminho):
        return caminho

    # Tenta várias combinações de separadores
    tentativas = [
        caminho,
        caminho.replace('/', '\\'),
        caminho.replace('\\', '/'),
        os.path.normpath(caminho),
        os.path.abspath(caminho)
    ]

    # Remove duplicados mantendo a ordem
    tentativas = list(dict.fromkeys(tentativas))

    for tentativa in tentativas:
        try:
            if os.path.exists(tentativa):
                return tentativa
        except (TypeError, ValueError):
            continue

    # Se nenhuma tentativa funcionar, retorna o original
    return caminho

def resource_path(relative_path):
    """Obtém o caminho absoluto para recursos, funciona para desenvolvimento e para PyInstaller"""
    try:
        base_path = sys._MEIPASS  # Pasta temporária quando empacotado
    except Exception:
        base_path = os.path.abspath(".")  # Pasta atual em desenvolvimento

    return os.path.join(base_path, relative_path)

class PDFProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Divisor de Comprovantes PDF")
        self.root.geometry("800x600")

        # Configuração do ícone
        try:
            self.root.iconbitmap(corrigir_caminho(resource_path(os.path.join('assets', 'app.ico'))))
        except:
            pass

        # Configuração do Tesseract
        tessdata_dir = resource_path('tessdata')
        os.environ['TESSDATA_PREFIX'] = tessdata_dir

        # Configura o caminho do Tesseract
        if getattr(sys, 'frozen', False):
            pytesseract.pytesseract.tesseract_cmd = corrigir_caminho(resource_path('tesseract.exe'))
        else:
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

        self.setup_ui()

    def setup_ui(self):
        # Frame principal
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Título
        tk.Label(main_frame, text="Divisor de Comprovantes PDF", font=("Arial", 16, "bold")).pack(pady=10)

        # Frame de entrada
        input_frame = tk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=10)

        tk.Label(input_frame, text="Arquivo PDF:").pack(side=tk.LEFT)
        self.file_entry = tk.Entry(input_frame, width=50)
        self.file_entry.pack(side=tk.LEFT, padx=5)

        browse_btn = tk.Button(input_frame, text="Procurar", command=self.browse_file)
        browse_btn.pack(side=tk.LEFT)

        # Frame de opções
        options_frame = tk.Frame(main_frame)
        options_frame.pack(fill=tk.X, pady=10)

        tk.Label(options_frame, text="Opções:").pack(anchor=tk.W)

        self.ocr_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Usar OCR quando necessário", variable=self.ocr_var).pack(anchor=tk.W)

        # Área de log
        tk.Label(main_frame, text="Log de Processamento:").pack(anchor=tk.W)
        self.log_text = tk.Text(main_frame, height=15, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)

        # Barra de progresso
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(fill=tk.X, pady=5)

        # Botão de processamento
        process_btn = tk.Button(main_frame, text="Processar PDF", command=self.process_pdf, height=2, width=20)
        process_btn.pack(pady=10)

        # Status com crédito
        self.status_var = tk.StringVar(value="Pronto - Criado por Sydney Pamplona")
        tk.Label(main_frame, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W).pack(fill=tk.X)

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, corrigir_caminho(file_path))

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
            processed_img = self.preprocess_image_for_ocr(images[0])

            custom_config = r'--oem 3 --psm 6 -l por+eng'
            texto = pytesseract.image_to_string(processed_img, config=custom_config)

            return texto
        except Exception as e:
            self.log_message(f"Erro no OCR (página {page_num+1}): {str(e)}")
            return ""

    def contem_4_cpfs(self, texto):
        """Verifica se o texto contém pelo menos 4 CPFs no formato XXX.XXX.XXX-XX"""
        cpfs = re.findall(r"\d{3}\.\d{3}\.\d{3}-\d{2}", texto)
        return len(cpfs) >= 4

    def extrair_beneficiario(self, texto, tentativa_ocr=False):
        # 1. Casos especiais (DARF, CAGEPA)
        if "PAGAMENTO DE DARF" in texto.upper():
            return "DARF"
        if "CAGEPA" in texto.upper():
            return "CAGEPA"

        # 2. Padrão para "Salário" ou "SALARIOS" (adicionado conforme solicitado)
        if "salário" in texto.lower() or "salarios" in texto.lower():
            return "FOLHA"

        # 3. Padrão para "Nome social" (adicionado conforme solicitado)
        if "Nome social:" in texto:
            linhas = texto.split('\n')
            for i, linha in enumerate(linhas):
                if "Nome social:" in linha and i + 1 < len(linhas):
                    beneficiario = linhas[i + 1].strip()
                    if beneficiario and beneficiario.lower() not in ['nome', '']:
                        return beneficiario[:25]

        # 4. Padrão para "Convenio" (adicionado conforme solicitado)
        if "Convenio" in texto:
            partes = texto.split("Convenio")
            if len(partes) > 1:
                beneficiario = partes[1].split('\n')[0].strip()
                if beneficiario:
                    return beneficiario[:25]

        # 5. Novo padrão para Itaú - nome do recebedor
        if "nome do recebedor:" in texto.lower():
            partes = texto.split("nome do recebedor:")
            if len(partes) > 1:
                beneficiario = partes[1].split('\n')[0].strip()
                if beneficiario:
                    return beneficiario[:25]

        # 6. Padrão para "Nome Fantasia:"
        if "Nome Fantasia:" in texto:
            match = re.search(r"Nome Fantasia:\s*(.*?)(?:\n|$)", texto)
            if match:
                beneficiario = match.group(1).strip()
                if beneficiario:
                    return beneficiario[:25]

            linhas = texto.split('\n')
            for i, linha in enumerate(linhas):
                if "Nome Fantasia:" in linha and i+1 < len(linhas):
                    beneficiario = linhas[i+1].strip()
                    if beneficiario:
                        return beneficiario[:25]

        # 7. Solução para boletos Santander
        if "Santander" in texto and "Dados do Beneficiário Original" in texto:
            padrao_santander = re.compile(
                r"Dados do Beneficiário Original.*?Razão Social:\s*([^\n]+)",
                re.DOTALL
            )
            match = padrao_santander.search(texto)
            if match:
                beneficiario = match.group(1).strip()
                beneficiario = re.sub(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', '', beneficiario).strip()
                if beneficiario:
                    return beneficiario[:25]

            linhas = [linha.strip() for linha in texto.split('\n') if linha.strip()]
            for i, linha in enumerate(linhas):
                if "Dados do Beneficiário Original" in linha and i+3 < len(linhas):
                    if re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', linhas[i+1]):
                        beneficiario = linhas[i+3]
                        if not re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', beneficiario):
                            return beneficiario[:25]

        # 8. Padrões genéricos
        padroes = [
            r"Favorecida:\s*(.+)",
            r"PAGO\s+PARA:?\s*(.+)",
            r"FAVORECIDO:?\s*(.+)",
            r"BENEFICI[ÁA]RIO:?\s*(.+)",
            r"NOME:?\s*(.+)",
            r"nome do recebedor:?\s*(.+)",
            r"creditada:\s*Nome:?\s*(.+)",
            r"Beneficiário:?\s*(.+)",
            r"Tipo de compromisso:?\s*(.+)",
            r"Dados do recebedor\s*\n\s*Para\s*(.+)",
            r"Favorecido\s*\n\s*Nome:?\s*(.+)",
        ]

        for padrao in padroes:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                nome = match.group(1).split("CNPJ")[0].strip().split("\n")[0]
                nome = re.sub(r"[^\w\s]", "", nome).strip()

                if "do pagador" in nome.lower() or "fantasia" in nome.lower():
                    return "beneficiário indefinido"

                if "beneficiário original" in texto.lower() and nome.lower() == "original":
                    continue

                if nome.lower() == "nome":
                    linhas = texto.splitlines()
                    for i, linha in enumerate(linhas):
                        if linha.strip().lower() == "nome:" and i + 1 < len(linhas):
                            nome = linhas[i + 1].strip()
                            break

                return nome[:25] if nome else "beneficiário indefinido"

        return "beneficiário indefinido"

    def extrair_valor(self, texto, tentativa_ocr=False):
        # Novo padrão para valor após CNPJ (adicionado conforme solicitado)
        padrao_cnpj_valor = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}[^\d]*([\d]{1,3}(?:\.?\d{3})*,\d{2})', texto)
        if padrao_cnpj_valor:
            valor = padrao_cnpj_valor.group(1).replace('.', '').replace(',', '_')
            self.log_message("Valor identificado após CNPJ")
            return valor

        # Padrões originais (mantidos conforme solicitado)
        padroes = [
            r"\(=\)\s*Valor\s*do\s*pagamento\s*\(R\$\):\s*([\d\.,]+)",
            r"\(=\)\s*Valor\s*do\s*pagamento\s*\(R\$\):\s*\n\s*([\d\.,]+)",
            r"VALOR\s+DO\s+DOCUMENTO[:\s]*R?\$?\s*([\d\.,]+)",
            r"VALOR[:\s]*R?\$?\s*([\d\.,]+)",
            r"valor\s*:\s*R?\$?\s*([\d\.,]+)",
            r"Valor da TED[:\s]*R?\$?\s*([\d\.,]+)",
            r"Valor do pagamento \(R\$\):?\s*([\d\.,]+)",
            r"Valor total pago[:\s]*R?\$?\s*([\d\.,]+)",
            r"Valor Total[:\s]*R?\$?\s*([\d\.,]+)",
            r"Valor Atualizado:?\s*R?\$?\s*([\d\.,]+)",
        ]
        
        for padrao in padroes:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                valor = match.group(1).replace(".", "").replace(",", "_")
                return valor
                
        return "valor_indefinido"

    def process_pdf(self):
        pdf_path = corrigir_caminho(self.file_entry.get())
        if not pdf_path:
            messagebox.showerror("Erro", "Por favor, selecione um arquivo PDF")
            return

        try:
            # Verifica se o arquivo existe após correção
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"Arquivo não encontrado: {pdf_path}")

            self.status_var.set("Processando...")
            self.progress["value"] = 0
            self.log_message(f"Iniciando processamento do arquivo: {os.path.basename(pdf_path)}")

            output_dir = os.path.join(os.path.dirname(pdf_path), "comprovantes_processados")
            os.makedirs(output_dir, exist_ok=True)

            doc = fitz.open(pdf_path)
            reader = PdfReader(pdf_path)
            total_pages = len(doc)
            processos = []
            i = 0

            while i < total_pages:
                self.progress["value"] = (i / total_pages) * 100
                self.status_var.set(f"Processando página {i+1}/{total_pages}")
                self.root.update()

                texto = doc.load_page(i).get_text()
                nome = self.extrair_beneficiario(texto)
                valor = self.extrair_valor(texto)

                if self.ocr_var.get() and ("indefinido" in nome.lower() or "indefinido" in valor.lower()):
                    self.log_message(f"Página {i+1}: usando OCR para extração alternativa...")
                    texto_ocr = self.extrair_texto_com_ocr(pdf_path, i)

                    if "indefinido" in nome.lower():
                        novo_nome = self.extrair_beneficiario(texto_ocr, tentativa_ocr=True)
                        if novo_nome != "beneficiário indefinido":
                            nome = novo_nome
                            self.log_message(f"Página {i+1}: Nome corrigido via OCR: {nome}")

                    if "indefinido" in valor.lower():
                        novo_valor = self.extrair_valor(texto_ocr, tentativa_ocr=True)
                        if novo_valor != "valor_indefinido":
                            valor = novo_valor
                            self.log_message(f"Página {i+1}: Valor corrigido via OCR: {valor}")

                if nome == "FOLHA":
                    writer = PdfWriter()
                    writer.add_page(reader.pages[i])

                    j = i + 1
                    while j < total_pages:
                        texto_pagina = doc.load_page(j).get_text()
                        if self.contem_4_cpfs(texto_pagina):
                            writer.add_page(reader.pages[j])
                            j += 1
                        else:
                            break

                    nome_arquivo = f"{i+1:02d}_{nome}_{valor}.pdf"
                    path_out = os.path.join(output_dir, nome_arquivo)
                    with open(path_out, "wb") as f:
                        writer.write(f)
                    processos.append(path_out)
                    i = j
                else:
                    nome_arquivo = f"{i+1:02d}_{nome}_{valor}.pdf"
                    path_out = os.path.join(output_dir, nome_arquivo)
                    writer = PdfWriter()
                    writer.add_page(reader.pages[i])
                    with open(path_out, "wb") as f:
                        writer.write(f)
                    processos.append(path_out)
                    i += 1

            zip_name = os.path.join(os.path.dirname(pdf_path), "comprovantes_divididos.zip")
            with zipfile.ZipFile(zip_name, 'w') as z:
                for arq in processos:
                    z.write(arq, os.path.basename(arq))

            self.progress["value"] = 100
            self.status_var.set("Processamento concluído - Criado por Sydney Pamplona")
            self.log_message(f"\n✅ Processo finalizado! Arquivos salvos em: {output_dir}")
            self.log_message(f"Arquivo ZIP criado: {zip_name}")

            messagebox.showinfo("Sucesso", "Processamento concluído com sucesso!")

        except Exception as e:
            self.log_message(f"\n❌ Erro durante o processamento: {str(e)}")
            self.status_var.set("Erro no processamento")
            messagebox.showerror("Erro", f"Ocorreu um erro durante o processamento:\n{str(e)}")
        finally:
            if 'doc' in locals():
                doc.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFProcessorApp(root)
    root.mainloop()