# -*- coding: utf-8 -*-
from PyQt4.QtGui import *
from PyQt4.QtCore import *


class QGISOptionSetSettings(QDialog):
    def __init__(self, name, dir, parent=None):
        QDialog.__init__(self, parent)

        self.lo = QVBoxLayout(self)

        self.gridLayout = QGridLayout()
        self.lo.addLayout(self.gridLayout)
        self.gridLayout.setAlignment(Qt.AlignTop)

        self.gridLayout.addWidget( QLabel(self.tr("QGIS Options set name")), 0, 0)
        self.leOptionsSetName = QLineEdit()
        self.gridLayout.addWidget( self.leOptionsSetName, 0, 1 )

        self.gridLayout.addWidget( QLabel(self.tr("QGIS Options set dir")), 1, 0)
        self.leOptionsSetDir = QLineEdit()
        self.gridLayout.addWidget( self.leOptionsSetDir, 1, 1 )

        self.pbOptionsSetDir = QPushButton(self.tr("Choose"))
        self.pbOptionsSetDir.clicked.connect(self.__chooseDir)
        self.gridLayout.addWidget( self.pbOptionsSetDir, 1, 2 )

        self.name = name
        self.dir = dir

        self.leOptionsSetName.setText(self.name)
        self.leOptionsSetDir.setText(self.dir)

        self.bbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.bbox.accepted.connect(self.accept)
        self.bbox.rejected.connect(self.reject)
        self.lo.addWidget( self.bbox )

    def accept(self):
        self.name = self.leOptionsSetName.text()
        self.dir = self.leOptionsSetDir.text()

        QDialog.accept(self)

    def __chooseDir(self):
        dirPath = QFileDialog.getExistingDirectory(
                    self,
                    self.tr("Select qgis options directory"))

        if not dirPath.isNull():
            file_info = QFileInfo(dirPath)
            self.leOptionsSetDir.setText(dirPath)


class QGISOptions(QWidget):
    def __init__(self, option, title, parent=None):
        QWidget.__init__(self, parent)

        self.__option = option
        self.__option.changed.connect(self.__showOptionsSettings)

        if type(title) == QString:
            self._title = unicode(title.toUtf8(), encoding="UTF-8")
        else:
            self._title = title

        self.vlo = QVBoxLayout(self)
        self.vlo.addWidget(QLabel(self.tr("QGIS Options sets") + ":"))

        self.qlw = QListWidget(self)
        self.qlw.currentRowChanged.connect(self.__selectedItem)
        self.vlo.addWidget(self.qlw)

        self.hlo = QHBoxLayout()
        self.vlo.addLayout(self.hlo)
        self.pbAddOptionsSet = QPushButton(self.tr("Add"), self)
        self.pbAddOptionsSet.clicked.connect(self.__addQGISOptionsSet)
        self.hlo.addWidget(self.pbAddOptionsSet)

        self.pbEditOptionsSet = QPushButton(self.tr("Edit"), self)
        self.pbEditOptionsSet.clicked.connect(self.__editQGISOptionsSet)
        self.pbEditOptionsSet.setEnabled(False)
        self.hlo.addWidget(self.pbEditOptionsSet)

        self.pbDelOptionsSet = QPushButton(self.tr("Del"), self)
        self.pbDelOptionsSet.clicked.connect(self.__delQGISOptionsSet)
        self.pbDelOptionsSet.setEnabled(False)
        self.hlo.addWidget(self.pbDelOptionsSet)

        self.__max_sets_count = 2

    def __showOptionsSettings(self):
        self.qlw.clear()
        if self.__option.value is None:
            return

        for option_set_name in self.__option.value.keys():
            item = QListWidgetItem()
            item.setData(Qt.DisplayRole, "%s [%s]" % (
                        option_set_name,
                        self.__option.value[option_set_name]))
            item.setData(Qt.UserRole, option_set_name)
            self.qlw.addItem(item)

        if self.qlw.count() == self.__max_sets_count:
            self.pbAddOptionsSet.setEnabled(False)
            self.pbAddOptionsSet.setText("%s (%s:%d)" % (
                        self.tr("Add"),
                        self.tr("max"), self.__max_sets_count))

        elif self.qlw.count() < self.__max_sets_count:
            self.pbAddOptionsSet.setText(self.tr("Add"))
            self.pbAddOptionsSet.setEnabled(True)

    def __selectedItem(self, row):
        if row == -1:
            self.pbEditOptionsSet.setEnabled(False)
            self.pbDelOptionsSet.setEnabled(False)
        else:
            self.pbEditOptionsSet.setEnabled(True)
            self.pbDelOptionsSet.setEnabled(True)

    def __addQGISOptionsSet(self):
        dlg = QGISOptionSetSettings("", "", self)
        if dlg.exec_():
            name = unicode(dlg.name.toUtf8(), encoding="UTF-8")
            dir = unicode(dlg.dir.toUtf8(), encoding="UTF-8")
            opt_set = {name: dir}

            new_value = {}
            if self.__option.value is not None:
                new_value.update(self.__option.value)

            new_value.update({name:dir})
            self.__option.value = new_value

    def __editQGISOptionsSet(self):
        item = self.qlw.currentItem()
        opt_set_name = item.data(Qt.UserRole).toPyObject()
        opt_set_name = unicode(opt_set_name.toUtf8(), encoding="UTF-8")

        dlg = QGISOptionSetSettings(opt_set_name, self.__option.value[opt_set_name], self)
        if dlg.exec_():
            name = unicode(dlg.name.toUtf8(), encoding="UTF-8")
            dir = unicode(dlg.dir.toUtf8(), encoding="UTF-8")
            opt_set = {name: dir}

            new_value = {}
            if self.__option.value is not None:
                self.__option.value.pop(opt_set_name)
                new_value.update(self.__option.value)

            new_value.update({name:dir})
            self.__option.value = new_value

    def __delQGISOptionsSet(self):
        item = self.qlw.currentItem()
        opt_set_name = item.data(Qt.UserRole).toPyObject()
        opt_set_name = unicode(opt_set_name.toUtf8(), encoding="UTF-8")

        new_value = {}
        if self.__option.value is not None:
            self.__option.value.pop(opt_set_name)
            new_value.update(self.__option.value)
        self.__option.value = new_value
