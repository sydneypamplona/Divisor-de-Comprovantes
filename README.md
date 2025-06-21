# 💼 Divisor de Comprovantes PDF

Um programa portátil simples e bastante útil para **dividir, renomear e organizar comprovantes de pagamento em PDF** automaticamente. Ideal para profissionais de controladoria e financeiro, que estão em processo de auditoria e lidam com uma grande quantidade de documentos.

---

## ✨ Funcionalidades

- Divide comprovantes de pagamento em arquivos separados.
- Renomeia os PDFs com base no favorecido e valor.
- Detecta automaticamente beneficiários usando OCR (quando necessário).
- Compacta todos os arquivos em um único `.zip`.
- **Layouts testados:** Santander, BB, Itaú, BTG e Caixa (menos testado).

---

## 🖼️ Prévia do Programa

<p align="center">

  ![image](https://github.com/user-attachments/assets/854704fc-3cae-48a4-bd06-28d18cfe4f34)

  ![image](https://github.com/user-attachments/assets/2bc6ef2d-527b-47e1-9257-e7b235d8219d)

</p>

---

## 📦 Como Usar

1. **Execute o programa** (não precisa instalar).
2. Selecione um arquivo `.pdf` com múltiplos comprovantes.
3. Clique em **"Processar"**.
4. Os comprovantes processados serão salvos na pasta `comprovantes_divididos` junto com um `.zip`.
5. **Não identifica em casos de:** Termos que não foram inseridos no script (haverá melhorias futuras) e Caso o documento PDF não seja selecionável.
6. Link para download: https://bit.ly/DivisorComprovantes

---

## 💡 Requisitos

- Testado em Windows 10+

- Para utilizar o programa através do executável (.exe) não precisa de instalações.

- Para compilar no seu computador pela primeira vez, é necessário instalar as bibliotecas necessárias antes:
      `pip install pyinstaller pymupdf PyPDF2 pdf2image pytesseract pillow opencv-python numpy`

- Após isso, obedecendo a estrutura de arquivos abaixo, basta realizar o compilamento:
      `pyinstaller build.spec --onefile --noconsole`

OBS.: Foi utilizado o .exe da versão mais recente do tesseract. Para inserir os pacotes de idiomas, basta consultar em: 
      https://github.com/tesseract-ocr/tessdata

---

## 📁 Estrutura de arquivo

![image](https://github.com/user-attachments/assets/1136532c-ccea-48f8-98dd-e2b6301c5795)

---

## 🙌 Apoie este projeto

Este programa é gratuito, mas você pode ajudar o autor com uma doação — qualquer valor já serve para um café!

### 💳 Pix

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
