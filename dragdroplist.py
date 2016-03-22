# -*- coding: utf-8 -*-
"""
The Python PDF Toolkit
Copyright ©2016 Ronan Paixão
Licensed under the terms of the MIT License.

See LICENSE.txt for details.

@author: Ronan Paixão
"""

from __future__ import division, unicode_literals, print_function

from PyQt4 import QtCore, QtGui


class DragDropList(QtGui.QListWidget):

    dropped = QtCore.pyqtSignal(list)

    def __init__(self, type, parent=None):
        super(DragDropList, self).__init__(parent)
        self.setDragDropMode(self.InternalMove)
        self.setAcceptDrops(True)
        self.setIconSize(QtCore.QSize(72, 72))
#        self.addItems(["Foo","Bar","Spam"])

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super(DragDropList, self).dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            super(DragDropList, self).dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
            links = []
            for url in event.mimeData().urls():
                links.append(str(url.toLocalFile()))
            self.dropped.emit(links)
        else:
            super(DragDropList, self).dropEvent(event)