# 💼 Divisor de Comprovantes PDF

Um programa portátil simples e bastante útil para **dividir, renomear e organizar comprovantes de pagamento em PDF** automaticamente. Ideal para profissionais de controladoria e financeiro, que estão em processo de auditoria e lidam com uma grande quantidade de documentos.

---

## ✨ Funcionalidades

- Divide comprovantes de pagamento em arquivos separados.
- Renomeia os PDFs com base no favorecido e valor.
- Detecta automaticamente beneficiários usando OCR (quando necessário).
- Compacta todos os arquivos em um único `.zip`.
- Mescla PDFs.
- **Layouts testados:** Santander, BB, Itaú, BTG e Caixa (menos testado).

---

## 🖼️ Prévia do Programa

<p align="center">

<img src="https://github.com/user-attachments/assets/142ded85-a43d-4473-8ff8-4e3e30e693da" width="700">

<img src="https://github.com/user-attachments/assets/9207771f-cfc2-4042-8018-6714d8ceb1e2" width="700">

</p>

---

## 📦 Como Usar

1. **Execute o programa** (não precisa instalar).
2. Selecione um arquivo `.pdf` com múltiplos comprovantes.
3. Clique em **"Processar"**.
4. Os comprovantes processados serão salvos na pasta `comprovantes_divididos` junto com um `.zip`.
5. **Não identifica em casos de:** Termos que não foram inseridos no script (haverá melhorias futuras) e Caso o documento PDF não seja selecionável.

---

## 💡 Requisitos

- Testado em Windows 10+

- Para utilizar o programa através do executável (.exe) não precisa de instalações.

- Para compilar no seu computador pela primeira vez, é necessário instalar as bibliotecas necessárias antes:
      `pip install pyinstaller pymupdf PyPDF2 pdf2image pytesseract pillow opencv-python numpy`

- Após isso, obedecendo a estrutura de arquivos abaixo, basta realizar o compilamento:
      `pyinstaller build.spec`

OBS.: Foi utilizado o .exe da versão mais recente do tesseract. Para inserir os pacotes de idiomas, basta consultar em: 
      https://github.com/tesseract-ocr/tessdata

---

## 📁 Estrutura de arquivo

![image](https://github.com/user-attachments/assets/1136532c-ccea-48f8-98dd-e2b6301c5795)

---

## 🙌 Apoie este projeto

Este programa é gratuito, mas você pode ajudar o autor com uma doação — qualquer valor já serve para um café!

### 💳 Pix / Paypal

sydneypamplona@gmail.com

---

## 📬 Contato

Para sugestões, bugs ou ideias: mesmo e-mail acima.

---

## 🧑‍💻 Licença

Este projeto é distribuído gratuitamente para uso pessoal. Venda ou redistribuição não autorizada é proibida.

---

## Aviso

Foi utilizado ferramentas de IA durante o processo de criação.
