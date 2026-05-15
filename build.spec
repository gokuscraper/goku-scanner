# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 需要打包的数据文件
datas = [
    ('core', 'core'),
    ('data', 'data'),
    ('logo.svg', '.'),
    ('Logo.png', '.'),
    ('gzh.jpg', '.'),
    ('github-logo.png', '.'),
    ('nmap-mac-prefixes.txt', '.'),
    ('framework_settings.json', '.'),
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'nicegui',
        'mac_vendor_lookup',
        'zai',
        'openai',
        'httpx',
        'webview',
        'ctypes',
        'socket',
        'ipaddress',
        'concurrent.futures',
        'urllib',
        're',
        'html',
        'csv',
        'json',
        'base64',
        'pathlib',
        'functools',
        'typing',
        'asyncio',
        'datetime',
        'subprocess',
        'os',
        'sys',
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
    name='悟空局域网侦探',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 窗口模式，不显示黑窗口
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='悟空局域网侦探',
)
