# -*- coding: utf-8 -*-
"""
Created on Thu Mar 17 12:11:22 2016

@author: Ronan Paixão
"""

from __future__ import division, unicode_literals, print_function

import sys
import os.path as osp
import uuid
from cStringIO import StringIO
import subprocess
from decimal import Decimal

# Setup PyQt's v2 APIs
import sip
API_NAMES = ["QDate", "QDateTime", "QString", "QTextStream", "QTime", "QUrl",
             "QVariant"]
API_VERSION = 2
for name in API_NAMES:
    sip.setapi(name, API_VERSION)
from PyQt4 import QtCore, QtGui, uic, Qt

import PyPDF2 as pdf


if sys.platform == 'darwin':
    def show_file(path):
        subprocess.Popen(['open', '--', path])
elif sys.platform == 'linux2':
    def show_file(path):
        subprocess.Popen(['xdg-open', '--', path])
elif sys.platform == 'win32':
    def show_file(path):
        subprocess.Popen(['explorer', '/select,', path])


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

    def merge(self, page):
        page2 = page.obj
        rotation = int(page2.get("/Rotate") or 0) % 360
        scale = Decimal(1.)
        # rotation is clockwise. tx, ty in page1 coordinates: x = right; y = up
        if rotation == 0:
            tx = 0
            ty = 0
        elif rotation == 90:
            tx = 0
            ty = self.obj.mediaBox.getHeight()
        elif rotation == 180:
            tx = -page2.mediaBox.getWidth()*scale
            ty = self.obj.mediaBox.getHeight()
        elif rotation == 270:
            tx = -page2.mediaBox.getHeight()*scale
            ty = self.obj.mediaBox.getHeight() - page2.mediaBox.getWidth()*scale
        self.obj.mergeRotatedScaledTranslatedPage(page2, -rotation, scale, -tx, ty)
        # Adjust name
        if self._basename == page._basename:
            self._numbers.append(','.join(page._numbers))
        else:
            self._numbers.append(u"{0}<{1}>".format(page._basename,
                                 ','.join(page._numbers)))
        self.transforms += "M"

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
    def on_btnFileTop_clicked(self):
        rows = [self.listFiles.row(item) for item in self.listFiles.selectedItems()]
        rows.sort(reverse=True)
        for item in [self.listFiles.item(row) for row in rows]:
            row = self.listFiles.row(item)
            self.listFiles.insertItem(0, self.listFiles.takeItem(row))
        for row in range(len(rows)):
            self.listFiles.setCurrentRow(row, QtGui.QItemSelectionModel.Select)

    @QtCore.pyqtSlot()
    def on_btnFileUp_clicked(self):
        rows = [self.listFiles.row(item) for item in self.listFiles.selectedItems()]
        rows.sort()
        # Ignore rows already on top
        first_rows = []
        first_row = 0
        print(rows)
        for row in rows[:]:
            if row == first_row:
                first_rows.append(row)
                rows.remove(row)
                first_row += 1
        for item in [self.listFiles.item(row) for row in rows]:
            row = self.listFiles.row(item)
            self.listFiles.insertItem(row-1, self.listFiles.takeItem(row))
        print(first_rows,rows)
        sys.stdout.flush()
        for row in first_rows + map(lambda r: r-1, rows):
            self.listFiles.setCurrentRow(row, QtGui.QItemSelectionModel.Select)

    @QtCore.pyqtSlot()
    def on_btnFileDown_clicked(self):
        rows = [self.listFiles.row(item) for item in self.listFiles.selectedItems()]
        rows.sort(reverse=True)
        # Ignore rows already on top
        last_rows = []
        last_row = self.listFiles.count() - 1
        print(rows)
        for row in rows[:]:
            if row == last_row:
                last_rows.append(row)
                rows.remove(row)
                last_row -= 1
        for item in [self.listFiles.item(row) for row in rows]:
            row = self.listFiles.row(item)
            self.listFiles.insertItem(row+1, self.listFiles.takeItem(row))
        print(last_rows,rows)
        sys.stdout.flush()
        for row in last_rows + map(lambda r: r+1, rows):
            self.listFiles.setCurrentRow(row, QtGui.QItemSelectionModel.Select)

    @QtCore.pyqtSlot()
    def on_btnFileBottom_clicked(self):
        rows = [self.listFiles.row(item) for item in self.listFiles.selectedItems()]
        rows.sort()
        last = self.listFiles.count() - 1
        for item in [self.listFiles.item(row) for row in rows]:
            row = self.listFiles.row(item)
            self.listFiles.insertItem(last, self.listFiles.takeItem(row))
        for row in range(len(rows)):
            self.listFiles.setCurrentRow(last-row, QtGui.QItemSelectionModel.Select)

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
    def on_btnFileOpenLoc_clicked(self):
        filename = self.listFiles.currentItem().data(QtCore.Qt.ToolTipRole)
        show_file(filename)

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
    def on_btnPageTop_clicked(self):
        rows = [self.listPages.row(item) for item in self.listPages.selectedItems()]
        rows.sort(reverse=True)
        for item in [self.listPages.item(row) for row in rows]:
            row = self.listPages.row(item)
            self.listPages.insertItem(0, self.listPages.takeItem(row))
        for row in range(len(rows)):
            self.listPages.setCurrentRow(row, QtGui.QItemSelectionModel.Select)

    @QtCore.pyqtSlot()
    def on_btnPageUp_clicked(self):
        rows = [self.listPages.row(item) for item in self.listPages.selectedItems()]
        rows.sort()
        # Ignore rows already on top
        first_rows = []
        first_row = 0
        print(rows)
        for row in rows[:]:
            if row == first_row:
                first_rows.append(row)
                rows.remove(row)
                first_row += 1
        for item in [self.listPages.item(row) for row in rows]:
            row = self.listPages.row(item)
            self.listPages.insertItem(row-1, self.listPages.takeItem(row))
        print(first_rows,rows)
        sys.stdout.flush()
        for row in first_rows + map(lambda r: r-1, rows):
            self.listPages.setCurrentRow(row, QtGui.QItemSelectionModel.Select)

    @QtCore.pyqtSlot()
    def on_btnPageDown_clicked(self):
        rows = [self.listPages.row(item) for item in self.listPages.selectedItems()]
        rows.sort(reverse=True)
        # Ignore rows already on top
        last_rows = []
        last_row = self.listPages.count() - 1
        print(rows)
        for row in rows[:]:
            if row == last_row:
                last_rows.append(row)
                rows.remove(row)
                last_row -= 1
        for item in [self.listPages.item(row) for row in rows]:
            row = self.listPages.row(item)
            self.listPages.insertItem(row+1, self.listPages.takeItem(row))
        print(last_rows,rows)
        sys.stdout.flush()
        for row in last_rows + map(lambda r: r+1, rows):
            self.listPages.setCurrentRow(row, QtGui.QItemSelectionModel.Select)

    @QtCore.pyqtSlot()
    def on_btnPageBottom_clicked(self):
        rows = [self.listPages.row(item) for item in self.listPages.selectedItems()]
        rows.sort()
        last = self.listPages.count() - 1
        for item in [self.listPages.item(row) for row in rows]:
            row = self.listPages.row(item)
            self.listPages.insertItem(last, self.listPages.takeItem(row))
        for row in range(len(rows)):
            self.listPages.setCurrentRow(last-row, QtGui.QItemSelectionModel.Select)

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
    def on_btnPageMerge_clicked(self):
        rows = [self.listPages.row(item) for item in self.listPages.selectedItems()]
        rows.sort()
        if len(rows)<2:
            return
        first_item = self.listPages.item(rows[0])
        variant = first_item.data(QtCore.Qt.UserRole)
        first_page = self.pages[variant]
        for item in [self.listPages.item(row) for row in rows[1:]]:
            row = self.listPages.row(item)
            merged_page_uuid = item.data(QtCore.Qt.UserRole)
#            print("merging", first_page.name, 'to', self.pages[merged_page_uuid].name)
            first_page.merge(self.pages[merged_page_uuid])
            del self.pages[merged_page_uuid]
            self.listPages.takeItem(row)
            first_item.setText(first_page.name)

    @QtCore.pyqtSlot()
    def on_btnPageSelectAll_clicked(self):
        self.listPages.selectAll()

    @QtCore.pyqtSlot()
    def on_btnWriteSingle_clicked(self):
        if self.listPages.count() == 0:
            QtGui.QMessageBox.critical(self, self.tr("Error"),
                                       self.tr("No pages to save!"))
            return
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
            try:
                with open(filename, 'wb') as f:
                    output_pdf.write(f)
                if self.chkOpenOnSave.isChecked():
                    open_default_program(filename)
            except IOError as e:
                errmsg = self.tr("I/O error({0}): {1}\n"
                    "Please check if the file is open in another program."
                    ).format(e.errno, e.strerror)
                QtGui.QMessageBox.critical(self, self.tr("Error"), errmsg)

    @QtCore.pyqtSlot()
    def on_btnWriteMulti_clicked(self):
        if self.listPages.count() == 0:
            QtGui.QMessageBox.critical(self, self.tr("Error"),
                                       self.tr("No pages to save!"))
            return
        supported_files = self.tr("PDF file (*.pdf)")
        filename = QtGui.QFileDialog.getSaveFileName(self,
                                                     self.tr('Save file'),
                                                     "",
                                                     supported_files)
        if filename:
            fileprefix = osp.splitext(filename)[0]
            rows = range(self.listPages.count())
            # pre-check filenames to see if we're overwriting something
            for i in rows:
                filename_i = "{}{:04}.pdf".format(fileprefix, i)
                if osp.exists(filename_i):
                    errmsg = self.tr("File {} already exists!\nWe don't want "
                        "to overwrite it. Aborting.").format(filename_i)
                    QtGui.QMessageBox.critical(self, self.tr("Error"),
                                               errmsg)
            for i, item in enumerate([self.listPages.item(row) for row in rows]):
                filename_i = "{}{:04}.pdf".format(fileprefix, i)
                output_pdf = pdf.PdfFileWriter()
                page_uuid = item.data(QtCore.Qt.UserRole)
                output_pdf.addPage(self.pages[page_uuid].obj)
                with open(filename_i, 'wb') as f:
                    output_pdf.write(f)
                if self.chkOpenOnSave.isChecked():
                    open_default_program(filename)



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
