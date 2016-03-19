# -*- coding: utf-8 -*-
"""
Created on Thu Mar 17 12:11:22 2016

@author: Ronan Paixão
"""

from __future__ import division, unicode_literals, print_function

import sys
import os
import os.path as osp
import uuid
from cStringIO import StringIO
import subprocess
from decimal import Decimal, InvalidOperation
import copy

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
    def open_default_program(path):
        subprocess.Popen(['start', path])
elif sys.platform == 'linux2':
    def show_file(path):
        subprocess.Popen(['xdg-open', '--', path])
    def open_default_program(path):
        subprocess.Popen(['xdg-open', path])
elif sys.platform == 'win32':
    def show_file(path):
        subprocess.Popen(['explorer', '/select,', path])
    open_default_program = os.startfile


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

    @classmethod
    def merge_pageobjs(cls, page1, page2, tx, ty):
        rotation = int(page2.get("/Rotate") or 0) % 360
        scale = Decimal(1.)
        # rotation is clockwise. tx, ty in page1 coordinates: x = right; y = up
        if rotation == 90:
#            tx += 0
            ty += page1.mediaBox.getHeight()
        elif rotation == 180:
            tx += page2.mediaBox.getWidth()*scale
            ty += page1.mediaBox.getHeight()
        elif rotation == 270:
            tx += page2.mediaBox.getHeight()*scale
            ty += page1.mediaBox.getHeight() - page2.mediaBox.getWidth()*scale
        page1.mergeRotatedScaledTranslatedPage(page2, -rotation, scale, tx, ty)

    def merge(self, page, tx=0.0, ty=0.0, op="merge"):
        """op in ['merge', 'stamp', 'background']"""
        assert(op in ["merge", "stamp", "background"])
        if op == "background":
            page0 = pdf.pdf.PageObject.createBlankPage(self.tmp,
                self.obj.mediaBox.getWidth(), self.obj.mediaBox.getHeight())
            Page.merge_pageobjs(page0, page.obj, tx, ty)
            tx = ty = 0
            page2 = self.obj
            self.obj = page0
        else:
            page2 = page.obj
        self.merge_pageobjs(self.obj, page2, tx, ty)
        # Adjust name
        if op == "merge":
            if self._basename == page._basename:
                self._numbers.append(','.join(page._numbers))
            else:
                self._numbers.append(u"{0}<{1}>".format(page._basename,
                                     ','.join(page._numbers)))
            self.transforms += "M"
        elif op == "stamp":
            self.transforms += "⊙"
        elif op == "background":
            self.uuid = page.uuid
            self._numbers = page._numbers
            self.transforms = page.transforms + "▣"
            self._basename = page._basename

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
        self.supported_files = self.tr("Supported files (*.pdf *.jpg *.jpeg)"
                                       ";;PDF file (*.pdf)"
                                       ";;JPEG file (*.jpg *.jpeg)"
                                       ";;All files (*.*)")
        validator = QtGui.QDoubleValidator()
        self.lineStampX.setValidator(validator)
        self.lineStampY.setValidator(validator)
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
        pages = []
        try:
            if filename.lower().endswith('.pdf'):
                with open(filename, 'rb') as f:
                    reader = pdf.PdfFileReader(f, strict=False)
                    total_pages = reader.getNumPages()
                    for i in range(total_pages):
                        page = Page(reader, i, filename)
                        pages.append(page)
        except Exception as e:
            errormsg = (self.tr("Could not load <{}>:\n{}")
                        .format(filename, e.strerror))
            QtGui.QMessageBox.warning(self, self.tr("Error"), errormsg)
        return pages

    def on_listFiles_dropped(self, links):
        print("filesDropped:", links)

        for link in links:
            self.open_file(link)

    @QtCore.pyqtSlot()
    def on_btnFileAdd_clicked(self):
        print("on_btnFileAdd_clicked")
        filenames = QtGui.QFileDialog.getOpenFileNames(self,
                                                       self.tr('Open file'),
                                                       "",
                                                       self.supported_files)
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

    def load_pages_from_rows(self, rows):
        pitems = []
        try:
            if self.radioFileLoadSelBef.isChecked():
                to_row = self.listPages.row(self.listPages.selectedItems()[0])
            elif self.radioFileLoadSelAft.isChecked():
                to_row = self.listPages.row(self.listPages.selectedItems()[-1])+1
            else:
                to_row = self.listPages.count()
        except:
            to_row = self.listPages.count()
        for fitem in [self.listFiles.item(row) for row in rows]:
            filename = fitem.data(QtCore.Qt.ToolTipRole)
            pages = self.load_pages(filename)
            for page in pages:
                self.pages[page.uuid] = page
                pitem = QtGui.QListWidgetItem(page.name)
                pitem.setData(QtCore.Qt.UserRole, page.uuid)
                if self.radioFileLoadEnd.isChecked():
                    self.listPages.addItem(pitem)
                else:
                    self.listPages.insertItem(to_row, pitem)
                    to_row += 1
                pitems.append(pitem)
        return pitems


    @QtCore.pyqtSlot()
    def on_btnFileLoad_clicked(self):
        # sort by row, otherwise it's selection order
        rows = [self.listFiles.row(item) for item in self.listFiles.selectedItems()]
        rows.sort()
        pitems = self.load_pages_from_rows(rows)
        self.listPages.selectionModel().clear()
        for item in pitems:
            item.setSelected(True)


    @QtCore.pyqtSlot()
    def on_btnFileLoadAll_clicked(self):
        rows = range(self.listFiles.count())
        pitems = self.load_pages_from_rows(rows)
        self.listPages.selectionModel().clear()
        for item in pitems:
            item.setSelected(True)

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
            item.setSelected(True)

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
            item.setSelected(True)

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
            item.setSelected(True)

    @QtCore.pyqtSlot()
    def on_btnPageBottom_clicked(self):
        rows = [self.listPages.row(item) for item in self.listPages.selectedItems()]
        rows.sort()
        last = self.listPages.count() - 1
        for item in [self.listPages.item(row) for row in rows]:
            row = self.listPages.row(item)
            self.listPages.insertItem(last, self.listPages.takeItem(row))
            item.setSelected(True)

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
            QtGui.QMessageBox.warning(self, self.tr("Warning"),
                                       self.tr("You must select at least "
                                               "two pages to merge."))
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
    def on_btnPageStamp_clicked(self):
        if len(self.listPages.selectedItems()) == 0:
            QtGui.QMessageBox.warning(self, self.tr("Warning"),
                                       self.tr("You must select at least "
                                               "one page to stamp."))
            return
        try:
            tx = Decimal(self.lineStampX.text() or 0)
            ty = Decimal(self.lineStampY.text() or 0)
        except InvalidOperation:
            QtGui.QMessageBox.critical(self, self.tr("Error"),
                                       self.tr("x and y must be numbers."))
            return
        # 1 PDF unit = 1/72 inches
        if self.radioStampCm.isChecked():
            mult = 72/Decimal(2.54)
        else:
            mult = 72/Decimal(1.0)
        filename = QtGui.QFileDialog.getOpenFileName(self,
                                                     self.tr('Open file'),
                                                     "",
                                                     self.supported_files)
        print("Stamp:", filename, mult, tx, ty, len(self.listPages.selectedItems()))
        page2 = self.load_pages(filename)[0]  # Always first page
        print(page2)
        sys.stdout.flush()
        for item in self.listPages.selectedItems():
            page1 = self.pages[item.data(QtCore.Qt.UserRole)]
            page1.merge(page2, tx*mult, ty*mult, "stamp")
            item.setText(page1.name)

    @QtCore.pyqtSlot()
    def on_btnPageBackground_clicked(self):
        if len(self.listPages.selectedItems()) == 0:
            QtGui.QMessageBox.warning(self, self.tr("Warning"),
                                       self.tr("You must select at least "
                                               "one page to apply background."))
            return
        try:
            if self.chkBackgroundStampLoc.isChecked():
                tx = Decimal(self.lineStampX.text() or 0)
                ty = Decimal(self.lineStampY.text() or 0)        # 1 PDF unit = 1/72 inches
                if self.radioStampCm.isChecked():
                    mult = 72/Decimal(2.54)
                else:
                    mult = 72/Decimal(1.0)
            else:
                tx = ty = Decimal(0)
                mult = Decimal(1)
        except InvalidOperation:
            QtGui.QMessageBox.critical(self, self.tr("Error"),
                                       self.tr("x and y must be numbers."))
            return

        filename = QtGui.QFileDialog.getOpenFileName(self,
                                                     self.tr('Open file'),
                                                     "",
                                                     self.supported_files)
        page2 = self.load_pages(filename)[0]  # Always first page
        for item in self.listPages.selectedItems():
            page1 = self.pages[item.data(QtCore.Qt.UserRole)]
            page1.merge(page2, tx*mult, ty*mult, "background")
            item.setText(page1.name)

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
