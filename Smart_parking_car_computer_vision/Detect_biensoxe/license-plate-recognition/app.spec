# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],  # Change this to your main Python file
    pathex=[],
    binaries=[],
    datas=[
        ('function', 'function'),  # Include function directory
        ('assets', 'assets'),      # Include assets if you have any
        ('config.yaml', '.'),      # Include YAML config
    ],
    hiddenimports=[
        'sqlalchemy',
        'sqlalchemy.ext.declarative',
        'sqlalchemy.orm',
        'pandas',
        'paho.mqtt.client',
        'yaml',
        'PIL',
        'cv2',
        'torch',
        'function.utils_rotate',
        'function.helper'
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

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='your_app_name',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True if you want to see console output
    icon='app.ico'  # Add your icon file here if you have one
)