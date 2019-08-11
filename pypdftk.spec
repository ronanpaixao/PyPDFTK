# -*- mode: python -*-

single_file = True
name = "PyPDFTK"

import sys
import os.path as osp

# Convert logo PNG to ICO
png_filename = osp.join('data', 'logo.png')
#icon_sizes = [(16,16), (32, 32), (48, 48), (64,64), (128,128)]
from PIL import Image
ico_img = Image.open(png_filename)
ico_img.save('build/logo.ico')

block_cipher = None #pyi_crypto.PyiBlockCipher(key='fookey')

# All files from "data" directory
datas = []
for r, d, fs in os.walk("data"):
    datas.extend([(osp.join(r, f), r) for f in fs])
datas.append(('build/logo.ico', '.'))

a = Analysis(['pypdftk.py'],
             pathex=[],
             binaries=[],
             datas=datas,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=['rthook.py'],
             excludes=[  # Comment if you use these modules
                       'PyQt5.QtDBus',
                       'PyQt5.QtWebKit',
                       'PyQt5.QtNetwork',
                       'PyQt5.QtOpenGL',
                       'PyQt5.QtSvg',
                       'PyQt5.QtTest',
                       'PyQt5.QtXml',
                      ],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exclude_binaries = (
    'qt5_plugins',
    '_cffi',
    '_hashlib',
    '_ssl',
    '_tkinter',
    '_win32',
    'bz2',
    'libssl',
    'mfc',
    'msvcm90',
    'msvcr90',
    'msvcp90',
    'PyQt5.QtSql',
    'Qt5DBus',
    'Qt5Network',
    'Qt5Qml',
    'Qt5Quick',
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
    'PyQt5\\Qt\\bin\\d3dcompiler',
    'PyQt5\\Qt\\bin\\libEGL',
    'PyQt5\\Qt\\bin\\libGLES',
    'PyQt5\\Qt\\bin\\opengl',
    'PyQt5\\Qt\\plugins\\platforms\\qoffscreen',
    'libcrypto',
    'libGLES',
)
a.binaries = [binary for binary in a.binaries if
              not binary[0].startswith(exclude_binaries)]

exclude_datas = (
    r'tcl\encoding',
    r'tcl\tzdata',
    r'tcl\msgs',
    r'tk\images',
    r'tk\msgs',
)
a.datas = [data for data in a.datas if not data[0].startswith(exclude_datas)]

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
          name=name,
          debug=False,
          bootloader_ignore_signals=False,
          #strip=True,
          upx=True,
          console=False,
          icon=osp.join('build', 'logo.ico'))

if not single_file:
    coll = COLLECT(exe,
                   a.binaries,
                   a.zipfiles,
                   a.datas,
                   strip=False,
                   upx=True,
                   upx_exclude=[],
                   name=name)
