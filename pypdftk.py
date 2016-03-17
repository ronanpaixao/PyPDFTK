# -*- coding: utf-8 -*-
"""
Created on Thu Mar 17 12:11:22 2016

@author: Ronan Paixão
"""

from __future__ import division, unicode_literals, print_function

import sys
from PyQt4 import QtCore, QtGui, uic, Qt

class WndMain(QtGui.QMainWindow):
    ######################
    ### Initialization ###
    ######################
    def __init__(self, *args, **kwargs):
        super(WndMain, self).__init__(*args, **kwargs)
        self.initUI()

    def initUI(self):
        uic.loadUi('wndmain.ui', self)
#        QtCore.QMetaObject.connectSlotsByName(self)
        self.show()

#%%
if __name__ == '__main__':
    existing = QtGui.qApp.instance()
    if existing:
        app = existing
    else:
        app = QtGui.QApplication(sys.argv)
    print(app.font().exactMatch())
    wnd = WndMain()
    if existing:
        self = wnd
    else:
        sys.exit(app.exec_())
