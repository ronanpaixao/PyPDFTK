# -*- coding: utf-8 -*-
"""
Created on Thu Mar 17 12:11:22 2016

@author: Ronan Paixão
"""

from __future__ import division, unicode_literals, print_function

import sys
import os.path as osp
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

    def open_file(self, filename):
        filename = filename.replace("/", osp.sep)
        if not osp.exists(filename):
            print("File doesn't exist!?")
            return
        item = QtGui.QListWidgetItem(osp.basename(filename))
        item.setData(QtCore.Qt.ToolTipRole, filename)
        self.listFiles.addItem(item)
        if filename.endswith('.pdf'):
#            reader = pdf.PdfFileReader(dumpfile)
            print(filename, osp.exists(filename))

    def on_listFiles_dropped(self, links):
        print("filesDropped:", links)

        for link in links:
            self.open_file(link)

    @QtCore.pyqtSlot()
    def on_btnFileAdd_clicked(self):
        print("on_btnFileAdd_clicked")
        supported_files = self.tr("Supported files (*.pdf *.jpg *.jpeg)"
                                  ";;PDF file (*.pdf)"
                                  ";;JPEG file (*.jpg *.jpeg)"
                                  ";;All files (*.*)")
        filenames = QtGui.QFileDialog.getOpenFileNames(self,
                                                       self.tr('Open file'),
                                                       "",
                                                       supported_files)
        for filename in filenames:
            self.open_file(filename)

    @QtCore.pyqtSlot()
    def on_btnFileRem_clicked(self):
        for item in self.listFiles.selectedItems():
            self.listFiles.takeItem(self.listFiles.row(item))

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
