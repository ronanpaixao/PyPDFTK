# -*- mode: python -*-

block_cipher = None #pyi_crypto.PyiBlockCipher(key='fookey')

single_file = True

a = Analysis(['pypdftk.py'],
             pathex=['D:\\workspace\\PyPDFTK'],
             binaries=None,
             datas=[('wndmain.ui', '.'),
                    ('logo.png', '.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=['rthook.py'],
             excludes=['PyQt4.QtWebKit'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

if single_file:
    exe_files = [
          a.binaries,
          a.zipfiles,
          a.datas]
else:
    exe_files = []

exe = EXE(pyz,
          a.scripts,
          *exe_files,
          #exclude_binaries=True,
          name='pypdftk',
          debug=False,
          #strip=True,
          upx=True,
          #console=False,
          icon='logo128x128.ico',)

if not single_file:
    coll = COLLECT(exe,
                   a.binaries,
                   a.zipfiles,
                   a.datas,
                   strip=False,
                   upx=True,
                   name='pydftk')
