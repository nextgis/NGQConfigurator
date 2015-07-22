# -*- coding: utf-8 -*-
import sys
import os
import tempfile

from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtNetwork import *
from PyQt4.QtWebKit import *

from logger import Log

from ui.ui_about_page_config import Ui_Dialog as Ui_AboutPagesSettingsDialog
from ui.ui_html_editor import Ui_HTMLEditor


class HTMLEditor(QDialog, Ui_HTMLEditor):
    def __init__(self, text = "", parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.pteHTMLContent.setPlainText (text)
        self.__htmlContentChanged()

        self.pteHTMLContent.textChanged.connect(self.__htmlContentChanged)

    def __htmlContentChanged(self):
        #print self.pteHTMLContent.toPlainText().toUtf8()
        self.tbHTMLResult.setHtml( self.pteHTMLContent.toPlainText() )


class AboutPageSettings(QDialog, Ui_AboutPagesSettingsDialog):
    def __init__(self, (name_en, name_tr, filename), parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.lContent.setAlignment(Qt.AlignTop)
        self.pbChoosePage.clicked.connect(self.choosePageContentFile)
        self.pbMakePage.clicked.connect(self.makePageContentFile)
        self.pbEditPage.clicked.connect(self.editPageContentFile)

        self.lePageNameEn.setText(name_en)
        self.lePageNameTr.setText(name_tr)
        self.lePageContentFileName.setText(filename)

        self.hlPageContetntControls.setAlignment(Qt.AlignRight)

        if not self.lePageContentFileName.text().isNull():
            self.pbEditPage.setEnabled(True)

        Log(u"Open add\\edit about page dialog: {0}".format((name_en, name_tr, filename)), u'debug')

    def getValues(self):
        return (
            unicode(self.lePageNameEn.text().toUtf8(), encoding="UTF-8"),
            unicode(self.lePageNameTr.text().toUtf8(), encoding="UTF-8"),
            unicode(self.lePageContentFileName.text().toUtf8(), encoding="UTF-8")
        )

    def choosePageContentFile(self):
        settings = QSettings()
        about_page_content_file = settings.value(
                                        u'about_page_content_file',
                                        defaultValue=unicode(),
                                        type=unicode)

        fileName = QFileDialog.getOpenFileName(
                                    self,
                                    self.tr("Choose about page content file"),
                                    QFileInfo(about_page_content_file).path())

        if fileName.isNull() == False:
            fileName = unicode(fileName.toUtf8(), encoding="UTF-8")
            settings.setValue(u'about_page_content_file', fileName)
            self.lePageContentFileName.setText(fileName)

        self.pbEditPage.setEnabled(True)

    def makePageContentFile(self):
        dlg = HTMLEditor()

        if dlg.exec_():
            settings = QSettings()
            about_page_content_file = settings.value(u'about_page_content_file', defaultValue = unicode(), type=unicode)

            fileName = QFileDialog.getSaveFileName(self,
                                            self.tr("Save page content file"),
                                            QFileInfo(about_page_content_file).path()
                                            )
            if fileName.isNull() == False:
                fileName = unicode(fileName.toUtf8(), encoding="UTF-8")

                file_content = unicode(
                                dlg.pteHTMLContent.toPlainText().toUtf8(),
                                encoding="UTF-8")

                with open(fileName, 'w') as f:
                    f.write(file_content)

                settings.setValue(u'about_page_content_file', fileName)
                self.lePageContentFileName.setText(fileName)

        self.pbEditPage.setEnabled(True)

    def editPageContentFile(self):
        fileName = unicode(
            self.lePageContentFileName.text().toUtf8(),
            encoding="UTF-8")

        file_content = ""

        with open(fileName, 'r') as f:
            file_content = f.read()

        file_content = file_content.decode('UTF-8')

        dlg = HTMLEditor(file_content)
        if dlg.exec_():
            with open(fileName, 'w') as f:
                f.write(dlg.pteHTMLContent.toPlainText().toUtf8())

    def accept(self):
        is_bad_form = False
        if self.lePageNameEn.text().isEmpty():
            self.lePageNameEn.setPlaceholderText(self.tr("Fill this!"))
            is_bad_form = True

        if self.lePageNameTr.text().isEmpty():
            self.lePageNameTr.setPlaceholderText(self.tr("Fill this!"))
            is_bad_form = True

        if self.lePageContentFileName.text().isEmpty():
            self.lePageContentFileName.setPlaceholderText(self.tr("Fill this!"))
            is_bad_form = True

        if is_bad_form:
            return

        QDialog.accept(self)
