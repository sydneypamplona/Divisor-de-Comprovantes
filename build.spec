# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs
import os

block_cipher = None

# Configurações para o Tesseract OCR
def get_tesseract_binaries():
    tesseract_binaries = []
    
    # Verifica se o tesseract.exe está no caminho esperado
    tesseract_exe = os.path.join('tesseract', 'tesseract.exe')
    if os.path.exists(tesseract_exe):
        tesseract_binaries.append((tesseract_exe, 'tesseract'))
    
    # Adiciona DLLs necessárias
    required_dlls = [
        'gomp-1.dll',
        'leptonica-1.82.0.dll',
        'libtesseract-5.dll',
        'lz4.dll',
        'zlib1.dll'
    ]
    
    for dll in required_dlls:
        if os.path.exists(dll):
            tesseract_binaries.append((dll, '.'))
    
    return tesseract_binaries

# Configurações para o PyMuPDF (fitz)
def get_fitz_data():
    fitz_data = collect_data_files('fitz')
    
    # Adiciona DLLs específicas do PyMuPDF
    fitz_dlls = [
        'libcrypto-1_1-x64.dll',
        'libssl-1_1-x64.dll'
    ]
    
    for dll in fitz_dlls:
        if os.path.exists(dll):
            fitz_data.append((dll, '.'))
    
    return fitz_data

a = Analysis(
    ['divisor_de_comprovantes.py'],
    pathex=[],
    binaries=[
        *get_tesseract_binaries(),
        *get_fitz_data(),
        # Incluir outras DLLs necessárias
        ('C:/Windows/System32/vcomp140.dll', '.'),
    ],
    datas=[
        ('tessdata/*', 'tessdata'),
        ('assets/app.ico', 'assets'),
        *collect_data_files('pytesseract'),
        *collect_data_files('PIL'),
        *collect_data_files('cv2'),
    ],
    hiddenimports=[
        'tkinter',
        'pytesseract',
        'fitz',
        'pkg_resources.py2_warn',
        'PIL._imagingtk',
        'PIL._imagingft',
        'PIL._imaging',
        'pytesseract.pytesseract',
        'cv2',
        'numpy',
        'pdf2image',
        'pandas',  # Caso esteja usando em algum lugar
        'datetime',  # Para manipulação de datas
        'sqlite3',  # Para bancos de dados embutidos
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DivisorComprovantes',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Mude para True durante o desenvolvimento
    icon=os.path.join('assets', 'app.ico'),
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DivisorComprovantes',
)
