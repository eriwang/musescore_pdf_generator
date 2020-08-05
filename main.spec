# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['src/main.py'],
             pathex=['/mnt/e/Projects/musescore_pdf_generator'],
             binaries=[],
             datas=[('venv/lib/python3.8/site-packages/google_api_python_client-1.10.0.dist-info', 'google_api_python_client-1.10.0.dist-info')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='main',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
