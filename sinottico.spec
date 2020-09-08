from os.path import join
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['main.py'],
             pathex=['.'],
             binaries=[],
             datas=[
                 (join(join('Sinottico', 'assets'), 'send.png'), '.'),
                 (join(join('Sinottico', 'assets'), 'loading.gif'), '.'),
		 (join(join('Sinottico', 'assets'), 'road.png'), '.'),
		 (join(join('Sinottico', 'assets'), 'gauge.png'), '.'),
             ],
             hiddenimports=['openpyxl'],
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
          name='sinottico',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          icon="rm.ico",
          console=False)
