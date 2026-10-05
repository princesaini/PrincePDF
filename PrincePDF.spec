# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

excluded_modules = [
    # Machine Learning, Data Science, and Heavy Libraries
    'torch', 'torchvision', 'torchaudio', 'transformers', 'tokenizers',
    'sentence_transformers', 'sentencepiece', 'scipy', 'pandas', 'matplotlib',
    'cv2', 'opencv_python', 'opencv_python_headless', 'onnxruntime',
    'rapidocr_onnxruntime', 'nltk', 'sympy', 'sklearn', 'scikit_learn',
    'playwright', 'sqlalchemy', 'redis', 'qdrant_client', 'pinecone',
    'pymilvus', 'pymongo', 'psycopg2', 'openpyxl', 'jinja2', 'notebook',
    'jupyter', 'IPython', 'pytest', 'lxml', 'fontTools', 'yaml', 'psutil',
    'charset_normalizer', 'pydantic', 'pydantic_core', 'pydantic_settings',
    'pypdf', 'PyPDF2', 'reportlab', 'fitz_old', 'shapely', 'soundfile',
    'unstructured', 'tqdm', 'rich', 'alembic', 'botocore', 'boto3',
    'google', 'grpc', 'fastapi', 'starlette', 'uvicorn', 'websockets',
    'peewee', 'PIL', 'Pillow', 'pyarrow', 'pyarrow.parquet',
    # Unused PyQt6 submodules
    'PyQt6.QtQuick', 'PyQt6.QtQuickWidgets', 'PyQt6.QtQuick3D',
    'PyQt6.QtQml', 'PyQt6.QtNetwork', 'PyQt6.QtSql', 'PyQt6.QtTest',
    'PyQt6.QtXml', 'PyQt6.QtPdf', 'PyQt6.QtPdfWidgets',
    'PyQt6.QtOpenGL', 'PyQt6.QtOpenGLWidgets',
    'PyQt6.QtMultimedia', 'PyQt6.QtMultimediaWidgets',
    'PyQt6.QtSpatialAudio', 'PyQt6.QtWebEngine', 'PyQt6.QtWebEngineCore',
    'PyQt6.QtWebEngineWidgets', 'PyQt6.QtSvg', 'PyQt6.QtSvgWidgets',
    'PyQt6.QtBluetooth', 'PyQt6.QtNfc', 'PyQt6.QtSensors',
    'PyQt6.QtPositioning', 'PyQt6.QtRemoteObjects', 'PyQt6.QtSerialPort',
    'PyQt6.QtWebSockets', 'PyQt6.QtTextToSpeech', 'PyQt6.QtDBus',
    'PyQt6.QtDesigner', 'PyQt6.QtHelp', 'PyQt6.QAxContainer',
    'PyQt6.QtStateMachine', 'PyQt6.QtWebChannel',
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
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtPrintSupport',
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

# Aggressive binary filtering to keep only essential Qt6 DLLs and platform plugins
unwanted_binary_patterns = [
    'qt6network', 'qt6qml', 'qt6quick', 'qt6sql', 'qt6test', 'qt6xml',
    'qt6pdf', 'qt6opengl', 'qt6multimedia', 'qt6spatialaudio', 'qt6svg',
    'qt6bluetooth', 'qt6nfc', 'qt6sensors', 'qt6positioning', 'qt6remoteobjects',
    'qt6serialport', 'qt6websockets', 'qt6texttospeech', 'qt6virtualkeyboard',
    'qt6dbus', 'qt6designer', 'qt6help', 'qt6shadertools', 'qt6labs',
    'qt6statemachine', 'qt6webchannel',
    'd3dcompiler', 'opengl32sw', 'tls', 'networkinformation', 'sqldrivers',
    'generic', 'multimedia', 'avcodec', 'avformat', 'avutil', 'swresample', 'swscale',
    'qjpeg', 'qgif', 'qwebp', 'qtiff', 'qwbmp',
    'numpy', 'pyarrow', 'parquet', 'arrow', 'lxml', 'fonttools', 'yaml',
    'pil', 'pillow', 'torch', 'scipy', 'pandas', 'cv2', 'onnxruntime', 'psutil',
    'charset_normalizer'
]

filtered_binaries = []
for item in a.binaries:
    name_lower = os.path.basename(item[0]).lower()
    full_lower = item[0].lower().replace('\\', '/')
    # Always keep essential Qt DLLs and platform plugin
    if any(essential in name_lower for essential in [
        'qt6core', 'qt6gui', 'qt6widgets', 'qt6printsupport',
        'qwindows.dll', 'windowsprintersupport.dll', 'qwindowsvistastyle.dll', 'qico.dll'
    ]):
        filtered_binaries.append(item)
    elif any(unwanted in name_lower or unwanted in full_lower for unwanted in unwanted_binary_patterns):
        continue
    else:
        filtered_binaries.append(item)

a.binaries = filtered_binaries

# Filter out bulky data files like Qt translations
filtered_datas = []
for item in a.datas:
    path_lower = item[0].lower().replace('\\', '/')
    if 'translations' in path_lower or 'qml' in path_lower:
        continue
    filtered_datas.append(item)

a.datas = filtered_datas

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Single Executable (onefile)
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
    upx=False,
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

