# -*- coding: utf-8 -*-
import os

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtSvg import *
from PyQt4.QtNetwork import *

from logger import *


class StringOption(QWidget):
    def __init__(self, option, title, parent):
        QWidget.__init__(self, parent)

        self.__option = option
        self.__option.changed.connect(self.__setOptionValue)

        self.layout = QHBoxLayout(self)

        self.l = QLabel("%s:" % title)
        self.layout.addWidget(self.l)

        self.le = QLineEdit()
        self.__setOptionValue()
        self.le.editingFinished.connect(self.__saveValue)
        self.layout.addWidget(self.le)

    def __setOptionValue(self):
        if self.__option.value is not None:
            self.le.setText(self.__option.value)

    def __saveValue(self):
        self.__option.value = unicode(self.le.text().toUtf8(), encoding = "UTF-8").replace(u'"',u'\'')


class FileOptionBase(QWidget):
    def __init__(self, title, parent=None):
        QWidget.__init__(self, parent)

        if type(title) == QString:
            self._title = unicode(title.toUtf8(), encoding="UTF-8")
        else:
            self._title = title

        self._filter = ""

    def setFilter(self, filter):
        self._filter = filter

    def selectFile(self):
        settings = QSettings()
        prev_dir = settings.value(
                            u'prev_option_file',
                            defaultValue=unicode(),
                            type=unicode)

        fileName = QFileDialog.getOpenFileName(
                           self,
                           "%s %s" % (self.tr("Select"), self._title.lower()),
                           prev_dir,
                           self._filter)

        if fileName.isNull() == False:
            fileName = unicode(fileName.toUtf8(), encoding="UTF-8")
            settings.setValue(u'prev_option_file', os.path.dirname(fileName))
            return fileName
        else:
            return None

    def selectDir(self):
        settings = QSettings()
        prev_dir = settings.value(
                        u'prev_option_file',
                        defaultValue=unicode(),
                        type=unicode)

        dirName = QFileDialog.getExistingDirectory(
                           self,
                           "%s %s" % (self.tr("Select"), self._title.lower()),
                           prev_dir)

        if dirName.isNull() == False:
            dirName = unicode(dirName.toUtf8(), encoding="UTF-8")
            settings.setValue(u'prev_option_file', dirName)
            return dirName
        else:
            return None


class ImageOption(FileOptionBase):
    def __init__(self, option, title, parent=None):
        FileOptionBase.__init__(self, title, parent)

        self.__option = option
        self.__option.changed.connect(self.__showImage)

        self.layout = QHBoxLayout(self)

        self.l = QLabel("%s:" % self._title)
        self.layout.addWidget(self.l)

        self.l_image = QLabel()
        self.layout.addWidget(self.l_image)
        self.__showImage()

        self.pb = QPushButton(self.tr(u"Choose"))
        self.pb.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.pb.clicked.connect(self.__chooseImage)
        self.layout.addWidget(self.pb)

    def __chooseImage(self):
        filename = self.selectFile()
        if filename is not None:
            self.__option.value = filename
            self.__showImage()

    def __showImage(self):
        if self.__option.value is None:
            self.l_image.setText( self.tr(u'Image not selected') )
            return

        f_info = QFileInfo(QString(self.__option.value))
        if f_info.exists() == False:
            self.l_image.setText( "Image (%s) not found"%self.__option.value )
            return

        pm = QPixmap(self.__option.value)
        pm = pm.scaledToHeight(min(32,pm.size().height()), Qt.SmoothTransformation)
        self.l_image.setPixmap( pm )


class FileOption(FileOptionBase):
    def __init__(self, option, title, dir_or_file=u'file',  parent=None):
        FileOptionBase.__init__(self, title, parent)

        self.__option = option
        self.__option.changed.connect(self.__showOption)

        self.__dir_or_file = dir_or_file

        self.layout = QHBoxLayout(self)

        self.l = QLabel("%s:" % self._title)
        self.layout.addWidget(self.l)

        self.le_file = QLineEdit()
        self.le_file.setReadOnly(True)

        self.__showOption()

        self.layout.addWidget(self.le_file)

        self.pb = QPushButton(self.tr(u"Choose"))
        self.pb.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.pb.clicked.connect(self.chooseFile)
        self.layout.addWidget(self.pb)

    def modelChangeHandle(self):
        self.__showOption()

    def chooseFile(self):
        if self.__dir_or_file == u'file':
            filename = self.selectFile()
            if filename is not None:
                self.__option.value = filename
        elif self.__dir_or_file == u'dir':
            self.__option.value = self.selectDir()
        self.__showOption()

    def __showOption(self):
        if self.__option.value is None:
            self.le_file.setText("")
            return

        f_info = QFileInfo(QString(self.__option.value))
        if f_info.exists() == False:
            self.le_file.setText("")
            return

        self.le_file.setText(self.__option.value)

"""class QGISOptionsExt(QWidget):
    def __init__(self, option, title, parent=None):
        QWidget.__init__(self, parent)

        self.__option = option
        self.__option.changed.connect(self.__showOption)

        if type(title) == QString:
            self._title = unicode(title.toUtf8(), encoding="UTF-8")
        else:
            self._title = title

        self.vlo = QVBoxLayout(self)

        self.gb = QGroupBox(title, self)
        self.vlo.addWidget(self.gb)

        self.glo = QGridLayout(self.gb)

        self.l_first_option_set_name = QLabel(self.tr(u'First option set name:'))
        self.glo.addWidget(self.l_first_option_set_name, 0, 0)
        self.le_first_option_set_name = QLineEdit()
        self.le_first_option_set_name.editingFinished.connect(self.__saveCustomizationOption)
        self.glo.addWidget(self.le_first_option_set_name, 0, 1)

        self.l_first_option_set_dir = QLabel(self.tr(u'First option set dir:'))
        self.glo.addWidget(self.l_first_option_set_dir, 1, 0)
        self.le_first_option_set_dir = QLineEdit()
        self.glo.addWidget(self.le_first_option_set_dir, 1, 1)
        self.pb_first_option_set_dir = QPushButton(self.tr(u'Choose...'))
        self.pb_first_option_set_dir.clicked.connect(self.chooseFirstOptionsSetDir)
        self.glo.addWidget(self.pb_first_option_set_dir, 1, 2)

        self.l_second_option_set_name = QLabel(self.tr(u'Second option set name:'))
        self.glo.addWidget(self.l_second_option_set_name, 3, 0)
        self.le_second_option_set_name = QLineEdit()
        self.le_second_option_set_name.editingFinished.connect(self.__saveCustomizationOption)
        self.glo.addWidget(self.le_second_option_set_name, 3, 1)

        self.l_second_option_set_dir = QLabel(self.tr(u'Second option set dir:'))
        self.glo.addWidget(self.l_second_option_set_dir, 4, 0)
        self.le_second_option_set_dir = QLineEdit()
        self.glo.addWidget(self.le_second_option_set_dir, 4, 1)
        self.pb_second_option_set_dir = QPushButton(self.tr(u'Choose...'))
        self.pb_second_option_set_dir.clicked.connect(self.chooseSecondOptionsSetDir)
        self.glo.addWidget(self.pb_second_option_set_dir, 4, 2)

    def __selectDir(self):
        settings = QSettings()
        prev_dir = settings.value(u'prev_qgis_options_dir', defaultValue = unicode(), type=unicode)

        dirName = QFileDialog.getExistingDirectory(self,
                                               "%s %s"%(self.tr(u'Select QGIS option dir'), self._title.lower()),
                                               prev_dir
                                              )
        if dirName.isNull() == False:
            dirName = unicode(dirName.toUtf8(), encoding="UTF-8")
            settings.setValue(u'prev_qgis_options_dir', os.path.dirname(dirName) )
            return dirName
        else:
            return None

    def chooseFirstOptionsSetDir(self):
        dir = self.__selectDir()
        if dir is not None:
            self.le_first_option_set_dir.setText(dir)
        self.__saveCustomizationOption()

    def chooseSecondOptionsSetDir(self):
        dir = self.__selectDir()
        if dir is not None:
            self.le_second_option_set_dir.setText(dir)
        self.__saveCustomizationOption()

    def __saveCustomizationOption(self):
        val = {}
        if not self.le_first_option_set_name.text().isEmpty() and \
            not self.le_first_option_set_dir.text().isEmpty():
            name = unicode(self.le_first_option_set_name.text().toUtf8(), encoding="UTF-8")
            dir = unicode(self.le_first_option_set_dir.text().toUtf8(), encoding="UTF-8")
            val[name] = dir

        if not self.le_second_option_set_name.text().isEmpty() and \
            not self.le_second_option_set_dir.text().isEmpty():
            name = unicode(self.le_second_option_set_name.text().toUtf8(), encoding="UTF-8")
            dir = unicode(self.le_second_option_set_dir.text().toUtf8(), encoding="UTF-8")
            val[name] = dir

        self.__option.value = val

    def __showOption(self):
        self.le_first_option_set_name.setText("")
        self.le_first_option_set_dir.setText("")
        self.le_second_option_set_name.setText("")
        self.le_second_option_set_dir.setText("")

        if self.__option.value is None:
            return
        if len(self.__option.value) == 0:
            return

        if len(self.__option.value) > 0:
            opts_set = self.__option.value.items()[0]
            self.le_first_option_set_name.setText(opts_set[0])
            self.le_first_option_set_dir.setText(opts_set[1])

        if len(self.__option.value) > 1:
            opts_set = self.__option.value.items()[1]
            self.le_second_option_set_name.setText(opts_set[0])
            self.le_second_option_set_dir.setText(opts_set[1])"""

from ui.ui_about_pages_manager import Ui_Form as Ui_AboutPagesManagerForm
from ngq_about_page_settings import AboutPageSettings

class AboutPagesManagerOption(QWidget, Ui_AboutPagesManagerForm):
    DATA_ROLE_STATE = Qt.UserRole+1
    DATA_ROLE_VISIBLE = Qt.UserRole+2
    DATA_ROLE_PAGE_NAME_EN = Qt.UserRole+3
    DATA_ROLE_PAGE_NAME_TR = Qt.UserRole+4
    DATA_ROLE_PAGE_FILE = Qt.UserRole+5

    def __init__(self, option, parent=None):
        QWidget.__init__(self, parent)
        self.setupUi(self)

        self.__option = option
        self.__option.changed.connect(self.modelChangeHandle)

        self.listWidget.clear()

        self.addConstItem(u"О программе")
        self.addConstItem(u"Что нового")
        self.addConstItem(u"Источники")
        self.addConstItem(u"Разработчики")
        self.addConstItem(u"Участники")
        self.addConstItem(u"Developers Map")
        self.addConstItem(u"Переводы")
        self.addConstItem(u"Доноры")
        self.addConstItem(u"Лицензия")


        self.listWidget.itemDoubleClicked.connect(self.clickByItem)
        self.listWidget.currentItemChanged.connect(self.currentItemChangedHandle)

        self.pbAddPage.clicked.connect(self.addPage)
        self.pbEditPage.clicked.connect(self.editPage)
        self.pbDeletePage.clicked.connect(self.deletePage)

        self.saveValue()

        self.setButtonsStatus()

    def addConstItem(self, name):
        lwi = QListWidgetItem(name)
        lwi.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable)
        f = lwi.font()
        f.setItalic(True)
        lwi.setFont(f)
        lwi.setData(self.DATA_ROLE_STATE, True)
        lwi.setData(self.DATA_ROLE_VISIBLE, True)
        self.listWidget.addItem(lwi)

    def addFreeItem(self, name_en, name_tr, filename, index = None):
        lwi = QListWidgetItem("%s [%s]"%(name_tr, filename))
        lwi.setData(self.DATA_ROLE_STATE, False)
        lwi.setData(self.DATA_ROLE_VISIBLE, True)
        lwi.setData(self.DATA_ROLE_PAGE_NAME_EN, name_en)
        lwi.setData(self.DATA_ROLE_PAGE_NAME_TR, name_tr)
        lwi.setData(self.DATA_ROLE_PAGE_FILE, filename)
        #self.listWidget.addItem(lwi)
        if index is None:
            self.listWidget.insertItem(self.listWidget.currentRow(), lwi)
        else:
            self.listWidget.insertItem(index, lwi)

    def clickByItem(self, lwi):
        if lwi.data(self.DATA_ROLE_STATE) == True:
            f = lwi.font()
            if lwi.data(self.DATA_ROLE_VISIBLE) == True:
                lwi.setData(self.DATA_ROLE_VISIBLE, False)
                f.setStrikeOut(True)
            else:
                lwi.setData(self.DATA_ROLE_VISIBLE, True)
                f.setStrikeOut(False)
            lwi.setFont(f)

            self.saveValue()

    def setButtonsStatus(self):
        lwi = self.listWidget.currentItem()

        if lwi is None:
            self.pbEditPage.setEnabled(False)
            self.pbDeletePage.setEnabled(False)
            return

        if lwi.data(self.DATA_ROLE_STATE) == False:
            self.pbEditPage.setEnabled(True)
            self.pbDeletePage.setEnabled(True)
        else:
            self.pbEditPage.setEnabled(False)
            self.pbDeletePage.setEnabled(False)

    def currentItemChangedHandle(self, current, previous):
        self.setButtonsStatus()

    def addPage(self):
        dlg = AboutPageSettings((u"",u"",u""), self)
        if dlg.exec_():
            values = dlg.getValues()
            self.addFreeItem(values[0], values[1], values[2])

        self.saveValue()

    def editPage(self):
        lwi = self.listWidget.currentItem()
        dlg = AboutPageSettings(
            (
                unicode(lwi.data(self.DATA_ROLE_PAGE_NAME_EN).toPyObject()),
                unicode(lwi.data(self.DATA_ROLE_PAGE_NAME_TR).toPyObject()),
                unicode(lwi.data(self.DATA_ROLE_PAGE_FILE).toPyObject())
            ),
            self)

        if dlg.exec_():
            values = dlg.getValues()

            self.listWidget.currentItem().setText("%s [%s]"%(values[1],values[2]))
            self.listWidget.currentItem().setData(self.DATA_ROLE_PAGE_NAME_EN, values[0])
            self.listWidget.currentItem().setData(self.DATA_ROLE_PAGE_NAME_TR, values[1])
            self.listWidget.currentItem().setData(self.DATA_ROLE_PAGE_FILE, values[2])

        self.saveValue()

    def deletePage(self):
        self.listWidget.takeItem(self.listWidget.currentRow())
        self.saveValue()

    def modelChangeHandle(self):
        self.listWidget.clear()

        self.addConstItem(u"О программе")
        self.addConstItem(u"Что нового")
        self.addConstItem(u"Источники")
        self.addConstItem(u"Разработчики")
        self.addConstItem(u"Участники")
        self.addConstItem(u"Developers Map")
        self.addConstItem(u"Переводы")
        self.addConstItem(u"Доноры")
        self.addConstItem(u"Лицензия")

        pages_configs = self.__option.value
        if pages_configs is not None:
            for page_index in range(0, len(pages_configs)):
                if pages_configs[page_index].has_key(u'name'):
                    self.addFreeItem(
                        pages_configs[page_index][u'name'][0],
                        pages_configs[page_index][u'name'][1],
                        pages_configs[page_index][u'content_file'],
                        page_index)
                else:
                    if pages_configs[page_index][u'visible'] == False:
                        lwi = self.listWidget.item(page_index)
                        f = lwi.font()
                        if lwi.data(self.DATA_ROLE_VISIBLE) == True:
                            lwi.setData(self.DATA_ROLE_VISIBLE, False)
                            f.setStrikeOut(True)
                        else:
                            lwi.setData(self.DATA_ROLE_VISIBLE, True)
                            f.setStrikeOut(False)
                        lwi.setFont(f)

    def event(self, e):
        if e.type() == QEvent.Enter: #hack for save state after drag$drop
            self.saveValue()
        return True

    def saveValue(self):
        pages_configs = []
        for i in range(self.listWidget.count()):
            lwi = self.listWidget.item(i)
            page_config = {}

            page_config[u'visible'] = lwi.data(self.DATA_ROLE_VISIBLE).toPyObject()
            if lwi.data(self.DATA_ROLE_STATE).toPyObject() == False:
                page_config[u'name'] = [
                    unicode(lwi.data(self.DATA_ROLE_PAGE_NAME_EN).toPyObject()),
                    unicode(lwi.data(self.DATA_ROLE_PAGE_NAME_TR).toPyObject())
                ]
                page_config[u'content_file'] = unicode(lwi.data(self.DATA_ROLE_PAGE_FILE).toPyObject())

            pages_configs.append(page_config)

        self.__option.value = pages_configs
