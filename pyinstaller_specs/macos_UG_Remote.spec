# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['../UG_Remote.py'],
             pathex=['../.'],
             binaries=[],
             datas=[
                ('../icon.png','.'),
             ],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=True)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='UG_Remote',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               upx_exclude=[],
               name='UG_Remote')
app = BUNDLE(coll,
             name='UG_Remote.app',
             icon='../icon.icns',
             bundle_identifier='ca.junhao.ugremote',
             version='5.0.2')
