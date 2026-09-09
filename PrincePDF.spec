# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

excluded_modules = [
    'torch', 'torchvision', 'torchaudio', 'transformers', 'tokenizers',
    'sentence_transformers', 'scipy', 'pandas', 'matplotlib', 'cv2',
    'opencv_python', 'onnxruntime', 'nltk', 'sympy', 'sklearn',
    'scikit_learn', 'playwright', 'sqlalchemy', 'redis', 'qdrant_client',
    'pinecone', 'pymilvus', 'pymongo', 'psycopg2', 'openpyxl',
    'jinja2', 'notebook', 'jupyter', 'IPython', 'pytest'
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('resources', 'resources'),
    ],
    hiddenimports=[
        'fitz',
        'fitz_old',
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtPrintSupport',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excluded_modules,
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
    name='PrincePDF',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/app_icon.ico',
)
