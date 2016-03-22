# -*- mode: python -*-

block_cipher = None #pyi_crypto.PyiBlockCipher(key='fookey')

single_file = True

# Compiling to EXE requires setuptools 19.2
# > conda remove setuptools
# > conda install setuptools=19.2

import os.path as osp
st_path = r'build\pypdftk\setuptools-19.2-py2.7.egg'
if osp.exists(st_path):
    import shutil
    shutil.rmtree(st_path)

# Convert logo PNG to ICO
png_filename = r'logo.png'
#icon_sizes = [(16,16), (32, 32), (48, 48), (64,64), (128,128)]
from PIL import Image
ico_img = Image.open(png_filename)
ico_img.save('build/logo.ico')

a = Analysis(['pypdftk.py'],
             pathex=['D:\\workspace\\PyPDFTK'],
             binaries=None,
             datas=[('wndmain.ui', '.'),
                    ('build/logo.ico', '.'),
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
          exclude_binaries=not single_file,
          name='pypdftk',
          debug=False,
          #strip=True,
          upx=True,
          #console=False,
          icon='build/logo.ico')

if not single_file:
    coll = COLLECT(exe,
                   a.binaries,
                   a.zipfiles,
                   a.datas,
                   strip=False,
                   upx=True,
                   name='pypdftk')
