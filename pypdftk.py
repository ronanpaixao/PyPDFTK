# -*- coding: utf-8 -*-
"""
Created on Thu Mar 17 12:11:22 2016

@author: Ronan Paixão
"""

from __future__ import division, unicode_literals, print_function

import sys
import os.path as osp
from PyQt4 import QtCore, QtGui, uic, Qt
import PyPDF2 as pdf
import uuid


class WndMain(QtGui.QMainWindow):
    ######################
    ### Initialization ###
    ######################
    def __init__(self, *args, **kwargs):
        super(WndMain, self).__init__(*args, **kwargs)
        self.initUI()
        self.pages = {}

    def initUI(self):
        uic.loadUi('wndmain.ui', self)
#        QtCore.QMetaObject.connectSlotsByName(self)
        self.show()

    def open_file(self, filename):
        filename = filename.replace("/", osp.sep)
        if not osp.exists(filename):
            errormsg = self.tr("File <{}> doesn't exist.").format(filename)
            QtGui.QMessageBox.warning(self, self.tr("Error"), errormsg)
            return
        item = QtGui.QListWidgetItem(osp.basename(filename))
        item.setData(QtCore.Qt.ToolTipRole, filename)
        self.listFiles.addItem(item)

    def load_pages(self, filename):
        print("load_pages", filename)
        if not osp.exists(filename):
            errormsg = self.tr("File <{}> doesn't exist.").format(filename)
            QtGui.QMessageBox.warning(self, self.tr("Error"), errormsg)
            return
        if filename.lower().endswith('.pdf'):
            print(filename, osp.exists(filename))
            with open(filename, 'rb') as f:
                reader = pdf.PdfFileReader(f, strict=False)
                total_pages = reader.getNumPages()
                for i in range(total_pages):
                    page_uuid = uuid.uuid4()
                    self.pages[page_uuid] = reader.getPage(i)
                    item = QtGui.QListWidgetItem("{0}<{1}>".format(
                        osp.basename(filename),
                        i+1))
                    item.setData(QtCore.Qt.UserRole, page_uuid)
                    self.listPages.addItem(item)


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

    @QtCore.pyqtSlot()
    def on_btnFileLoad_clicked(self):
        # sort by row, otherwise it's selection order
        rows = [self.listFiles.row(item) for item in self.listFiles.selectedItems()]
        rows.sort()
        for item in [self.listFiles.item(row) for row in rows]:
            filename = item.data(QtCore.Qt.ToolTipRole)
            print(filename)
            sys.stdout.flush()
            self.load_pages(filename)

    @QtCore.pyqtSlot()
    def on_btnFileLoadAll_clicked(self):
        rows = range(self.listFiles.count())
        for item in [self.listFiles.item(row) for row in rows]:
            filename = item.data(QtCore.Qt.ToolTipRole)
            self.load_pages(filename)

    @QtCore.pyqtSlot()
    def on_btnFileSortAsc_clicked(self):
        self.listFiles.sortItems(QtCore.Qt.AscendingOrder)

    @QtCore.pyqtSlot()
    def on_btnFileSortDesc_clicked(self):
        self.listFiles.sortItems(QtCore.Qt.DescendingOrder)

    @QtCore.pyqtSlot()
    def on_btnFilesClear_clicked(self):
        self.listFiles.clear()

    @QtCore.pyqtSlot()
    def on_btnPageRem_clicked(self):
        for item in self.listPages.selectedItems():
            page_uuid = item.data(QtCore.Qt.UserRole)
            del self.pages[page_uuid]
            self.listPages.takeItem(self.listPages.row(item))

    @QtCore.pyqtSlot()
    def on_btnPageClear_clicked(self):
        self.listPages.clear()
        self.pages = {}

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
