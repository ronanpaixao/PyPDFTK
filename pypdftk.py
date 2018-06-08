#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The Python PDF Toolkit
Copyright ©2016 Ronan Paixão
Licensed under the terms of the MIT License.

See LICENSE.txt for details.

@author: Ronan Paixão
"""

from __future__ import division, unicode_literals, print_function

import sys
import os
import os.path as osp
import uuid
try:
    from cStringIO import StringIO as BytesIO
except ModuleNotFoundError:  # Py3
    from io import BytesIO
import subprocess
from decimal import Decimal, InvalidOperation
import copy
import ctypes
import traceback


#%% Setup PyQt's v2 APIs
import sip
API_NAMES = ["QDate", "QDateTime", "QString", "QTextStream", "QTime", "QUrl",
             "QVariant"]
API_VERSION = 2
for name in API_NAMES:
    sip.setapi(name, API_VERSION)
#%%
from qtpy import QtCore, QtGui, QtWidgets, uic

import PyPDF2 as pdf
from PIL import Image

import pdf_images

# Need to import promoted qt classes, to make py2exe process them.
import dragdroplist
import six

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

#%% PyInstaller Utilities
def frozen(filename):
    """Returns the filename for a frozen file (program file which may be
    included inside the executable created by PyInstaller).
    """
    if getattr(sys, 'frozen', False):
        return osp.join(sys._MEIPASS, filename)
    else:
        return filename

#%%
class Page(object):
    def __init__(self):
        self.tmp = BytesIO()
        self.uuid = uuid.uuid4()
        self.obj = None
        self.transforms = ""
        self._numbers = []
        self._basename = "Invalid Page"

    def reload_from_buffer(self):
        self.tmp.seek(0)
        reader = pdf.PdfFileReader(self.tmp, strict=False)
        self.obj = reader.getPage(0)

    @classmethod
    def from_file(cls, filename):
        pages = []
        with open(filename, 'rb') as f:
            reader = pdf.PdfFileReader(f, strict=False)
            total_pages = reader.getNumPages()
            for page_number in range(total_pages):
                page = Page()
                output = pdf.PdfFileWriter()
                output.addPage(reader.getPage(page_number))
                output.write(page.tmp)
                page.reload_from_buffer()
                page._numbers = [str(page_number + 1)]
                page._basename = osp.basename(filename)
                pages.append(page)
        return pages

    @classmethod
    def from_image(cls, filename, page_size_cm):
        page = Page()
        page.tmp = pdf_images.image_to_pdf(filename, page_size_cm)
        page.reload_from_buffer()
        page._basename = osp.basename(filename)
        page._numbers = ["I"]
        return page

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


class WndMain(QtWidgets.QMainWindow):
    ######################
    ### Initialization ###
    ######################
    def __init__(self, *args, **kwargs):
        super(WndMain, self).__init__(*args, **kwargs)
        self.initUI()
        self.pages = {}

    def initUI(self):
        ui_file = frozen(osp.join('data', 'wndmain.ui'))
        uic.loadUi(ui_file, self)
        self.supported_files = self.tr("Supported files (*.pdf *.jpg *.jpeg"
                                       " *.bmp *.gif *.j2p *.jpx *.png *.tiff)"
                                       ";;PDF file (*.pdf)"
                                       ";;Image file (*.jpg *.jpeg *.bmp *.gif"
                                       " *.j2p *.jpx *.png *.tiff)"
                                       ";;All files (*.*)")
        validator = QtGui.QDoubleValidator()
        self.lineStampX.setValidator(validator)
        self.lineStampY.setValidator(validator)
        self.lineFileDPI.setValidator(validator)

        self.show()

    def open_file(self, filename):
        filename = filename.replace("/", osp.sep)
        if not osp.exists(filename):
            errormsg = self.tr("File <{}> doesn't exist.").format(filename)
            QtWidgets.QMessageBox.warning(self, self.tr("Error"), errormsg)
            return
        item = QtWidgets.QListWidgetItem(osp.basename(filename))
        item.setData(QtCore.Qt.ToolTipRole, filename)
        self.listFiles.addItem(item)

    def load_pages(self, filename):
        pages = []
        try:
            image_exts = ['.jpg', '.jpeg', '.bmp', '.gif', '.j2p', '.jpx',
                          '.png', '.tiff']
            basefile, ext = osp.splitext(filename.lower())
            if ext == '.pdf':
                pages = Page.from_file(filename)
            elif ext in image_exts:
                img_size = Image.open(filename).size
                try:
                    dpi = float(self.lineFileDPI.text())
                except:
                    dpi = float(self.lineFileDPI.placeholderText())
                img_size = (img_size[0]/dpi*2.54, img_size[1]/dpi*2.54)
                pages.append(Page.from_image(filename, img_size))
        except Exception as e:
            errormsg = (self.tr("Could not load <{}>:\n{}")
                            .format(filename, traceback.format_exc()))
            QtWidgets.QMessageBox.warning(self, self.tr("Error"), errormsg)
        return pages

    def on_listFiles_dropped(self, links):
        print("filesDropped:", links)

        for link in links:
            self.open_file(link)

    @QtCore.Slot()
    def on_btnFileAdd_clicked(self):
        filenames = QtWidgets.QFileDialog.getOpenFileNames(self,
                                                       self.tr('Open file'),
                                                       "",
                                                       self.supported_files)[0]
        for filename in filenames:
            self.open_file(filename)

    @QtCore.Slot()
    def on_btnFileRem_clicked(self):
        for item in self.listFiles.selectedItems():
            self.listFiles.takeItem(self.listFiles.row(item))

    @QtCore.Slot()
    def on_btnFileTop_clicked(self):
        rows = [self.listFiles.row(item) for item in self.listFiles.selectedItems()]
        rows.sort(reverse=True)
        for item in [self.listFiles.item(row) for row in rows]:
            row = self.listFiles.row(item)
            self.listFiles.insertItem(0, self.listFiles.takeItem(row))
        for row in range(len(rows)):
            self.listFiles.setCurrentRow(row, QtCore.QItemSelectionModel.Select)

    @QtCore.Slot()
    def on_btnFileUp_clicked(self):
        rows = [self.listFiles.row(item) for item in self.listFiles.selectedItems()]
        rows.sort()
        # Ignore rows already on top
        first_rows = []
        first_row = 0
        for row in rows[:]:
            if row == first_row:
                first_rows.append(row)
                rows.remove(row)
                first_row += 1
        for item in [self.listFiles.item(row) for row in rows]:
            row = self.listFiles.row(item)
            self.listFiles.insertItem(row-1, self.listFiles.takeItem(row))
        sys.stdout.flush()
        for row in first_rows + list(map(lambda r: r-1, rows)):
            self.listFiles.setCurrentRow(row, QtCore.QItemSelectionModel.Select)

    @QtCore.Slot()
    def on_btnFileDown_clicked(self):
        rows = [self.listFiles.row(item) for item in self.listFiles.selectedItems()]
        rows.sort(reverse=True)
        # Ignore rows already on top
        last_rows = []
        last_row = self.listFiles.count() - 1
        for row in rows[:]:
            if row == last_row:
                last_rows.append(row)
                rows.remove(row)
                last_row -= 1
        for item in [self.listFiles.item(row) for row in rows]:
            row = self.listFiles.row(item)
            self.listFiles.insertItem(row+1, self.listFiles.takeItem(row))
        sys.stdout.flush()
        for row in last_rows + list(map(lambda r: r+1, rows)):
            self.listFiles.setCurrentRow(row, QtCore.QItemSelectionModel.Select)

    @QtCore.Slot()
    def on_btnFileBottom_clicked(self):
        rows = [self.listFiles.row(item) for item in self.listFiles.selectedItems()]
        rows.sort()
        last = self.listFiles.count() - 1
        for item in [self.listFiles.item(row) for row in rows]:
            row = self.listFiles.row(item)
            self.listFiles.insertItem(last, self.listFiles.takeItem(row))
        for row in range(len(rows)):
            self.listFiles.setCurrentRow(last-row, QtCore.QItemSelectionModel.Select)

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
                pitem = QtWidgets.QListWidgetItem(page.name)
                pitem.setData(QtCore.Qt.UserRole, page.uuid)
                if self.radioFileLoadEnd.isChecked():
                    self.listPages.addItem(pitem)
                else:
                    self.listPages.insertItem(to_row, pitem)
                    to_row += 1
                pitems.append(pitem)
        return pitems


    @QtCore.Slot()
    def on_btnFileLoad_clicked(self):
        # sort by row, otherwise it's selection order
        rows = [self.listFiles.row(item) for item in self.listFiles.selectedItems()]
        rows.sort()
        pitems = self.load_pages_from_rows(rows)
        self.listPages.selectionModel().clear()
        for item in pitems:
            item.setSelected(True)


    @QtCore.Slot()
    def on_btnFileLoadAll_clicked(self):
        rows = range(self.listFiles.count())
        pitems = self.load_pages_from_rows(rows)
        self.listPages.selectionModel().clear()
        for item in pitems:
            item.setSelected(True)

    @QtCore.Slot()
    def on_btnFileSortAsc_clicked(self):
        self.listFiles.sortItems(QtCore.Qt.AscendingOrder)

    @QtCore.Slot()
    def on_btnFileSortDesc_clicked(self):
        self.listFiles.sortItems(QtCore.Qt.DescendingOrder)

    @QtCore.Slot()
    def on_btnFilesClear_clicked(self):
        self.listFiles.clear()

    @QtCore.Slot()
    def on_btnFileOpenLoc_clicked(self):
        filename = self.listFiles.currentItem().data(QtCore.Qt.ToolTipRole)
        show_file(filename)

    @QtCore.Slot()
    def on_btnPageRem_clicked(self):
        for item in self.listPages.selectedItems():
            page_uuid = item.data(QtCore.Qt.UserRole)
            del self.pages[page_uuid]
            self.listPages.takeItem(self.listPages.row(item))

    @QtCore.Slot()
    def on_btnPageClear_clicked(self):
        self.listPages.clear()
        self.pages = {}

    @QtCore.Slot()
    def on_btnPageSortAsc_clicked(self):
        self.listPages.sortItems(QtCore.Qt.AscendingOrder)

    @QtCore.Slot()
    def on_btnPageSortDesc_clicked(self):
        self.listPages.sortItems(QtCore.Qt.DescendingOrder)

    @QtCore.Slot()
    def on_btnPageTop_clicked(self):
        rows = [self.listPages.row(item) for item in self.listPages.selectedItems()]
        rows.sort(reverse=True)
        for item in [self.listPages.item(row) for row in rows]:
            row = self.listPages.row(item)
            self.listPages.insertItem(0, self.listPages.takeItem(row))
            item.setSelected(True)

    @QtCore.Slot()
    def on_btnPageUp_clicked(self):
        rows = [self.listPages.row(item) for item in self.listPages.selectedItems()]
        rows.sort()
        # Ignore rows already on top
        first_rows = []
        first_row = 0
        for row in rows[:]:
            if row == first_row:
                first_rows.append(row)
                rows.remove(row)
                first_row += 1
        for item in [self.listPages.item(row) for row in rows]:
            row = self.listPages.row(item)
            self.listPages.insertItem(row-1, self.listPages.takeItem(row))
            item.setSelected(True)

    @QtCore.Slot()
    def on_btnPageDown_clicked(self):
        rows = [self.listPages.row(item) for item in self.listPages.selectedItems()]
        rows.sort(reverse=True)
        # Ignore rows already on top
        last_rows = []
        last_row = self.listPages.count() - 1
        for row in rows[:]:
            if row == last_row:
                last_rows.append(row)
                rows.remove(row)
                last_row -= 1
        for item in [self.listPages.item(row) for row in rows]:
            row = self.listPages.row(item)
            self.listPages.insertItem(row+1, self.listPages.takeItem(row))
            item.setSelected(True)

    @QtCore.Slot()
    def on_btnPageBottom_clicked(self):
        rows = [self.listPages.row(item) for item in self.listPages.selectedItems()]
        rows.sort()
        last = self.listPages.count() - 1
        for item in [self.listPages.item(row) for row in rows]:
            row = self.listPages.row(item)
            self.listPages.insertItem(last, self.listPages.takeItem(row))
            item.setSelected(True)

    @QtCore.Slot()
    def on_btnPageRotLeft_clicked(self):
        for item in self.listPages.selectedItems():
            page_uuid = item.data(QtCore.Qt.UserRole)
            page = self.pages[page_uuid]
            page.rotateLeft()
            item.setText(page.name)

    @QtCore.Slot()
    def on_btnPageRotRight_clicked(self):
        for item in self.listPages.selectedItems():
            page_uuid = item.data(QtCore.Qt.UserRole)
            page = self.pages[page_uuid]
            page.rotateRight()
            item.setText(page.name)

    @QtCore.Slot()
    def on_btnPageMerge_clicked(self):
        rows = [self.listPages.row(item) for item in self.listPages.selectedItems()]
        rows.sort()
        if len(rows)<2:
            QtWidgets.QMessageBox.warning(self, self.tr("Warning"),
                                       self.tr("You must select at least "
                                               "two pages to merge."))
            return
        first_item = self.listPages.item(rows[0])
        variant = first_item.data(QtCore.Qt.UserRole)
        first_page = self.pages[variant]
        for item in [self.listPages.item(row) for row in rows[1:]]:
            row = self.listPages.row(item)
            merged_page_uuid = item.data(QtCore.Qt.UserRole)
            first_page.merge(self.pages[merged_page_uuid])
            del self.pages[merged_page_uuid]
            self.listPages.takeItem(row)
            first_item.setText(first_page.name)

    @QtCore.Slot()
    def on_btnPageStamp_clicked(self):
        if len(self.listPages.selectedItems()) == 0:
            QtWidgets.QMessageBox.warning(self, self.tr("Warning"),
                                       self.tr("You must select at least "
                                               "one page to stamp."))
            return
        try:
            tx = Decimal(self.lineStampX.text() or 0)
            ty = Decimal(self.lineStampY.text() or 0)
        except InvalidOperation:
            QtWidgets.QMessageBox.critical(self, self.tr("Error"),
                                       self.tr("x and y must be numbers."))
            return
        # 1 PDF unit = 1/72 inches
        if self.radioStampCm.isChecked():
            mult = 72/Decimal(2.54)
        else:
            mult = 72/Decimal(1.0)
        filename = QtWidgets.QFileDialog.getOpenFileName(self,
                                                     self.tr('Open file'),
                                                     "",
                                                     self.supported_files)[0]
        page2 = self.load_pages(filename)[0]  # Always first page
        sys.stdout.flush()
        for item in self.listPages.selectedItems():
            page1 = self.pages[item.data(QtCore.Qt.UserRole)]
            page1.merge(page2, tx*mult, ty*mult, "stamp")
            item.setText(page1.name)

    @QtCore.Slot()
    def on_btnPageBackground_clicked(self):
        if len(self.listPages.selectedItems()) == 0:
            QtWidgets.QMessageBox.warning(self, self.tr("Warning"),
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
            QtWidgets.QMessageBox.critical(self, self.tr("Error"),
                                       self.tr("x and y must be numbers."))
            return

        filename = QtWidgets.QFileDialog.getOpenFileName(self,
                                                     self.tr('Open file'),
                                                     "",
                                                     self.supported_files)[0]
        page2 = self.load_pages(filename)[0]  # Always first page
        for item in self.listPages.selectedItems():
            page1 = self.pages[item.data(QtCore.Qt.UserRole)]
            page1.merge(page2, tx*mult, ty*mult, "background")
            item.setText(page1.name)

    @QtCore.Slot()
    def on_btnPageSelectAll_clicked(self):
        self.listPages.selectAll()

    @QtCore.Slot()
    def on_btnWriteSingle_clicked(self):
        if self.listPages.count() == 0:
            QtWidgets.QMessageBox.critical(self, self.tr("Error"),
                                       self.tr("No pages to save!"))
            return
        supported_files = self.tr("PDF file (*.pdf)")
        filename = QtWidgets.QFileDialog.getSaveFileName(self,
                                                     self.tr('Save file'),
                                                     "",
                                                     supported_files)[0]
        if filename:
            filename = filename.replace("/", osp.sep)
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
                QtWidgets.QMessageBox.critical(self, self.tr("Error"), errmsg)

    @QtCore.Slot()
    def on_btnWriteMulti_clicked(self):
        if self.listPages.count() == 0:
            QtWidgets.QMessageBox.critical(self, self.tr("Error"),
                                       self.tr("No pages to save!"))
            return
        supported_files = self.tr("PDF file (*.pdf)")
        filename = QtWidgets.QFileDialog.getSaveFileName(self,
                                                     self.tr('Save file'),
                                                     "",
                                                     supported_files)[0]
        if filename:
            filename = filename.replace("/", osp.sep)
            fileprefix = osp.splitext(filename)[0]
            rows = range(self.listPages.count())
            # pre-check filenames to see if we're overwriting something
            for i in rows:
                filename_i = "{}{:04}.pdf".format(fileprefix, i)
                if osp.exists(filename_i):
                    errmsg = self.tr("File {} already exists!\nWe don't want "
                        "to overwrite it. Aborting.").format(filename_i)
                    QtWidgets.QMessageBox.critical(self, self.tr("Error"),
                                               errmsg)
                    return
            for i, item in enumerate([self.listPages.item(row) for row in rows]):
                filename_i = "{}{:04}.pdf".format(fileprefix, i)
                output_pdf = pdf.PdfFileWriter()
                page_uuid = item.data(QtCore.Qt.UserRole)
                output_pdf.addPage(self.pages[page_uuid].obj)
                with open(filename_i, 'wb') as f:
                    output_pdf.write(f)
                if self.chkOpenOnSave.isChecked():
                    open_default_program(filename_i)

    @QtCore.Slot()
    def on_btnExtractImages_clicked(self):
        if self.listPages.count() == 0:
            QtWidgets.QMessageBox.critical(self, self.tr("Error"),
                                       self.tr("No pages to look for images!"))
            return
        supported_files = self.tr("Image file prefix (*.*)")
        filename = QtWidgets.QFileDialog.getSaveFileName(self,
                                                     self.tr('Save file'),
                                                     "",
                                                     supported_files)[0]
        if filename:
            fileprefix, ext = osp.splitext(filename)
            rows = range(self.listPages.count())
            i = 0
            for item in [self.listPages.item(row) for row in rows]:
                page_uuid = item.data(QtCore.Qt.UserRole)
                i = pdf_images.extract_images(self.pages[page_uuid].obj, filename, i)

    @QtCore.Slot()
    def on_btnCredits_clicked(self):
        ui_file = frozen(osp.join('data', 'about.ui'))
        dialog = QtWidgets.QDialog()
        uic.loadUi(ui_file, dialog)
        dialog.exec_()


#%%
if __name__ == '__main__':
    myappid = u'br.com.dapaixao.pypdftk.1.0'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    existing = QtWidgets.qApp.instance()
    if existing:
        app = existing
    else:
        app = QtWidgets.QApplication(sys.argv)
    wnd = WndMain()
    if existing:
        self = wnd
    else:
        sys.exit(app.exec_())
