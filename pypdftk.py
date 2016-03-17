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
from cStringIO import StringIO


class Page(object):
    def __init__(self, reader, page_number, filename):
        self.tmp = StringIO()
        output = pdf.PdfFileWriter()
        output.addPage(reader.getPage(page_number))
        output.write(self.tmp)
        self.tmp.seek(0)
        reader = pdf.PdfFileReader(self.tmp, strict=False)
        self.uuid = uuid.uuid4()
        self.obj = reader.getPage(0)
        self._numbers = [str(page_number + 1)]
        self.transforms = ""
        self._basename = osp.basename(filename)

    def rotateLeft(self):
        self.obj.rotateCounterClockwise(90)
        self.transforms += '↺'
        if self.transforms.endswith('↻↺'):
            self.transforms = self.transforms[:-2]
        if self.transforms.endswith('↺↺↺'):
            self.transforms = self.transforms[:-3]+'↻'

    def rotateRight(self):
        self.obj.rotateClockwise(90)
        self.transforms += '↻'
        if self.transforms.endswith('↺↻'):
            self.transforms = self.transforms[:-2]
        if self.transforms.endswith('↻↻↻'):
            self.transforms = self.transforms[:-3]+'↺'

    @property
    def name(self):
        return u"{0}<{1}>[{2}]".format(self._basename,
                                       ','.join(self._numbers),
                                       self.transforms)


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
                    page = Page(reader, i, filename)
                    self.pages[page.uuid] = page
                    item = QtGui.QListWidgetItem(page.name)
                    item.setData(QtCore.Qt.UserRole, page.uuid)
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

    @QtCore.pyqtSlot()
    def on_btnPageSortAsc_clicked(self):
        self.listPages.sortItems(QtCore.Qt.AscendingOrder)

    @QtCore.pyqtSlot()
    def on_btnPageSortDesc_clicked(self):
        self.listPages.sortItems(QtCore.Qt.DescendingOrder)

    @QtCore.pyqtSlot()
    def on_btnPageRotLeft_clicked(self):
        for item in self.listPages.selectedItems():
            page_uuid = item.data(QtCore.Qt.UserRole)
            page = self.pages[page_uuid]
            page.rotateLeft()
            item.setText(page.name)

    @QtCore.pyqtSlot()
    def on_btnPageRotRight_clicked(self):
        for item in self.listPages.selectedItems():
            page_uuid = item.data(QtCore.Qt.UserRole)
            page = self.pages[page_uuid]
            page.rotateRight()
            item.setText(page.name)

    @QtCore.pyqtSlot()
    def on_btnWriteSingle_clicked(self):
        supported_files = self.tr("PDF file (*.pdf)")
        filename = QtGui.QFileDialog.getSaveFileName(self,
                                                     self.tr('Save file'),
                                                     "",
                                                     supported_files)
        if filename:
            output_pdf = pdf.PdfFileWriter()
            rows = range(self.listPages.count())
            for item in [self.listPages.item(row) for row in rows]:
                page_uuid = item.data(QtCore.Qt.UserRole)
                output_pdf.addPage(self.pages[page_uuid].obj)
            with open(filename, 'wb') as f:
                output_pdf.write(f)



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
