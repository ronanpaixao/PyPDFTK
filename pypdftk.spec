# -*- mode: python -*-

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

block_cipher = None #pyi_crypto.PyiBlockCipher(key='fookey')

a = Analysis(['pypdftk.py'],
             pathex=['D:\\workspace\\PyPDFTK'],
             binaries=None,
             datas=[('wndmain.ui', '.'),
                    ('about.ui', '.'),
                    ('build/logo.ico', '.'),
                    ('logo.png', '.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=['rthook.py'],
             excludes=['PyQt4.QtWebKit',
                       'PyQt4.QtNetwork',
                       'PyQt4.QtOpenGL',
                       'PyQt4.QtSvg',
                       'PyQt4.QtTest',
                       'PyQt4.QtXml',
                      ],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exclude_starts = [
    'qt4_plugins',
    '_cffi',
    #'_ctypes',
    '_hashlib',
    '_ssl',
    '_tkinter',
    '_win32',
    'bz2',
    'mfc',
    'msvcm90',
    'msvcr90',
    'msvcp90',
    'PyQt4.QtSql',
    'QtOpenGL',
    'QtSql',
    'QtSvg',
    'QtXml',
    'tcl85',
    'tk85',
    'unicodedata',
    'win32evtlog',
    'win32pipe',
    'win32trace',
    'win32wnet',
    'win32ui',
    'select',
]
def include_binary(binary):
    for start in exclude_starts:
        if binary.startswith(start):
            return False
    return True

a.binaries = [binary for binary in a.binaries if include_binary(binary[0])]

exclude_datas = [
    r'tcl\encoding',
    r'tcl\tzdata',
    r'tcl\msgs',
    r'tk\images',
    r'tk\msgs',
]
def include_data(data):
    for start in exclude_datas:
        if data.startswith(start):
            return False
    return True

a.datas = [data for data in a.datas if include_data(data[0])]

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
          console=False,
          icon='build/logo.ico')

if not single_file:
    coll = COLLECT(exe,
                   a.binaries,
                   a.zipfiles,
                   a.datas,
                   strip=False,
                   upx=True,
                   name='pypdftk')
