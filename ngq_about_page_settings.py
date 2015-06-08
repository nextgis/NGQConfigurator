# -*- coding: utf-8 -*-
import sys
import os
import tempfile

from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtNetwork import *
from PyQt4.QtWebKit import *

from ui.ui_about_page_config import Ui_Dialog as Ui_AboutPagesSettingsDialog
from ui.ui_html_editor import Ui_HTMLEditor

class HTMLEditor(QDialog, Ui_HTMLEditor):
    def __init__(self, text = "", parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
        self.tbHTMLResult.setHtml(text)
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
        
        self.lePageNameEn.setText(name_en)
        self.lePageNameTr.setText(name_tr)
        self.lePageContentFileName.setText(filename)
        
        self.hlPageContetntControls.setAlignment(Qt.AlignRight)

    def getValues(self):
        return (
            unicode(self.lePageNameEn.text()), 
            unicode(self.lePageNameTr.text()),
            unicode(self.lePageContentFileName.text())
        )
    
    def choosePageContentFile(self):
        settings = QSettings()
        about_page_content_file = settings.value(u'about_page_content_file', defaultValue = unicode(), type=unicode) 
        fileName = QFileDialog.getOpenFileName(self,
                                            self.tr("Choose about page content file"),
                                            QFileInfo(about_page_content_file).path()
                                            )
        
        if fileName.isNull() == False:
            fileName = unicode(fileName.toUtf8(), encoding="UTF-8")
            settings.setValue(u'about_page_content_file', fileName)
            self.lePageContentFileName.setText(fileName)
            
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
                
                with open(fileName, 'w') as f:
                    f.write(dlg.pteHTMLContent.toPlainText().toUtf8())
            
                settings.setValue(u'about_page_content_file', fileName)
                self.lePageContentFileName.setText(fileName)