# -*- coding: utf-8 -*-
"""
Created on Sat Mar 19 16:31:43 2016

@author: Ronan Paixão
"""

from distutils.core import setup
import py2exe, sys, os
import site

# Convert logo PNG to ICO
from PyQt4 import QtGui
app = QtGui.QApplication([])
png_filename = r'logo.png'
icon_sizes = [(16,16), (32, 32), (48, 48), (64,64), (128,128)]
icon = QtGui.QIcon(png_filename)
icon_resources = []
for i, size in enumerate(icon_sizes):
    filename = "{0}{1}x{2}.ico".format(os.path.splitext(png_filename)[0], *size)
    icon.pixmap(*size).save(filename, 'ico')
    icon_resources.append((i+1, filename))

sys.argv.append('py2exe')

data_files = [('.', ['wndmain.ui', 'logo.png'])]

suffix = r'\Library\plugins\imageformats\qico4.dll'
for path in site.getsitepackages():
    filename = path + suffix
    if os.path.exists(filename):
        data_files.append(('imageformats', [filename]))
        break
assert(len(data_files)==2)

# Workaround py2exe icon bug
import tempfile
tf = tempfile.NamedTemporaryFile(delete=False)
tf.close()
setup(
    windows = [{
        'script': tf.name,
        "icon_resources":[(1, "logo128x128.ico")],
        "dest_base" : "pypdftk"}]
)
os.remove(tf.name)

setup_dict = dict(
    data_files = data_files,
    options = {'py2exe': {
        'bundle_files': 3,  # py2exe doesn't support bundling on py_win64
        'compressed': True,
        "includes" : ["sip", ],
        "excludes": ["PyQt4.uic.port_v3",
                     '_ssl',  # Exclude _ssl
                     'pyreadline', 'difflib', 'doctest', 'locale',
                     'optparse', 'pickle', 'calendar'],  # Exclude standard library
        }},
    windows = [{'script': "pypdftk.py",
                "icon_resources": icon_resources}],
    zipfile = None,
)

setup(**setup_dict)
setup(**setup_dict)
