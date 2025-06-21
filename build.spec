# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['divisor_de_comprovantes.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('tessdata/*', 'tessdata'),
        ('tesseract.exe', '.'),
        ('assets/app.ico', 'assets')
    ],
    hiddenimports=[
        'pytesseract',
        'fitz',
        'pkg_resources.py2_warn',
        'PIL._imagingtk',
        'PIL._imagingft',
        'PIL._imaging'
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
    console=False,
    icon=os.path.join('assets', 'app.ico'),
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)