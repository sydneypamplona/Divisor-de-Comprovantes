# 💼 Divisor de Comprovantes PDF

Um programa portátil simples e bastante útil para **dividir, renomear e organizar comprovantes de pagamento em PDF** automaticamente. Ideal para profissionais de controladoria e financeiro, que estão em processo de auditoria e lidam com uma grande quantidade de documentos.

---

## ✨ Funcionalidades

- Divide comprovantes de pagamento em arquivos separados.
- RRenomeia os PDFs com base no beneficiário final e valor final.
- Gera um relatório em Excel e também compacta todos os arquivos em .zip
- Mescla PDFs.
- Layouts mais testados: Santander, BB, Itaú e BTG.
- Layouts menos testados: Caixa e Bradesco.

---

## 🖼️ Prévia do Programa

<p align="center">

<img src="https://github.com/user-attachments/assets/6c74a336-03eb-4649-a10d-28da84f0ae50" width="700">

<img src="https://github.com/user-attachments/assets/de1555e6-75c1-4c01-a8e9-c7f1f93ad637" width="700">

</p>

---

## 📦 Como Usar

1. **Execute o programa** (não precisa instalar).
2. Selecione um arquivo `.pdf` com múltiplos comprovantes.
3. Clique em **"Processar"**.
4. Os comprovantes processados serão salvos na pasta comprovantes_divididos junto com um .zip ou .xlsx.
5. **Não identifica em casos de:** Termos que não foram inseridos no script (haverá melhorias futuras) e Caso o documento PDF não seja selecionável.

---

## 💡 Requisitos

- Testado em Windows 10+

- Para utilizar o programa através do executável (.exe) não precisa de instalações.

- Tamanho 670 MB.

- Funciona tanto online quanto offline.

- Para compilar no seu computador pela primeira vez, é necessário instalar as bibliotecas necessárias antes:
      `pip install pyinstaller pymupdf PyPDF2 pdf2image pytesseract pillow opencv-python numpy`

- Após isso, obedecendo a estrutura de arquivos abaixo, basta realizar o compilamento:
      `pyinstaller build.spec`

---

## 📁 Estrutura de arquivo

<img width="269" height="106" alt="image" src="https://github.com/user-attachments/assets/7f53a2af-8dcc-45ab-ba7c-dd69b9caa530" />

---

## 🙌 Apoie este projeto

Este programa é código aberto para vocês, mas você pode ajudar o autor com uma doação ou comprando o software (.exe) no payhip (https://payhip.com/b/jKiwB)

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
