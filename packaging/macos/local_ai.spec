# Local AI — PyInstaller (macOS .app)
# Build with: bash packaging/macos/build.sh

block_cipher = None

a = Analysis(
    ['../../src/local_ai/__main__.py'],
    pathex=['../../src'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PySide6',
        'httpx',
        'numpy',
        'pypdf',
        'docx',
        'markdown_it',
        'platformdirs',
        'pydantic',
        'pydantic_settings',
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
    [],
    exclude_binaries=True,
    name='LocalAI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
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
    name='LocalAI',
)

app = BUNDLE(
    coll,
    name='LocalAI.app',
    icon=None,
    bundle_identifier='com.lucaverduyn.localai',
    info_plist={
        'NSHighResolutionCapable': True,
        'CFBundleDisplayName': 'Local AI',
        'CFBundleName': 'Local AI',
        'CFBundleShortVersionString': '1.0.0',
    },
)
