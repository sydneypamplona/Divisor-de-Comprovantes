# -*- mode: python ; coding: utf-8 -*-

import sys
sys.setrecursionlimit(sys.getrecursionlimit() * 5)  # SOLUÇÃO PARA O RECURSION ERROR

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs
import os

block_cipher = None

# Configurações otimizadas para o PyMuPDF (fitz)
def get_fitz_data():
    fitz_data = collect_data_files('fitz')
    
    # Adiciona DLLs específicas do PyMuPDF
    fitz_dlls = [
        'libcrypto-1_1-x64.dll',
        'libssl-1_1-x64.dll'
    ]
    
    for dll in fitz_dlls:
        dll_path = os.path.join(sys._MEIPASS, dll) if getattr(sys, 'frozen', False) else dll
        if os.path.exists(dll_path):
            fitz_data.append((dll_path, '.'))
    
    return fitz_data

a = Analysis(
    ['divisor_de_comprovantes.py'],
    pathex=[os.getcwd()],  # Adiciona o diretório atual ao path
    binaries=[
        *get_fitz_data(),
        # Incluir outras DLLs necessárias
        ('C:/Windows/System32/vcomp140.dll', '.'),
    ],
    datas=[
        ('assets/app.ico', 'assets'),
        *collect_data_files('PIL'),
        *collect_data_files('tkinterdnd2'),  # Adicionado especificamente para tkinterdnd2
    ],
    hiddenimports=[
        'tkinter',
        'fitz',
        'pkg_resources.py2_warn',
        'PIL',
        'pandas._libs.tslibs.timedeltas',  # Importante para pandas
        'pandas._libs.tslibs.np_datetime',  # Importante para pandas
        'pandas._libs.tslibs.base',  # Importante para pandas
        'tkinterdnd2',  # Adicionado explicitamente
        'numpy',  # Necessário para pandas
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['cv2', 'pdf2image'],  # Removidos se não estiver usando
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Configuração otimizada para o PYZ
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
    optimize=2  # Otimização adicional
)

# Configuração da EXE com parâmetros otimizados
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
    console=False,
    icon=os.path.join('assets', 'app.ico'),
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Configuração COLLECT simplificada
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
