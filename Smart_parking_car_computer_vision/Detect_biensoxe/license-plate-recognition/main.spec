# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('rfid_management.py', '.'),  # Bao gồm tệp rfid_management.py
        ('webcam.py', '.'),           # Bao gồm tệp webcam.py
        ('mqtt_handler.py', '.'),     # Bao gồm tệp mqtt_handler.py
        ('doanh_thu.py', '.'),        # Bao gồm tệp doanh_thu.py
	('create_database.py', '.'),
	('lp_image.py', '.'),
    ],
    hiddenimports=['sqlalchemy', 'cv2', 'PyQt6'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main',
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
)
