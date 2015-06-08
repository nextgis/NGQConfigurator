# -*- coding: utf-8 -*-
import os

from PyQt4.QtGui import *
from PyQt4.QtCore import *

class MessageDialog(QMessageBox):
    @staticmethod
    def critical(parent, title, msg_short, msg_detail):
        mb = QMessageBox(parent) 
        mb.setWindowTitle(title)
        mb.setText(msg_short)
        mb.setDetailedText(msg_detail)
        mb.setIcon(QMessageBox.Critical)
        
        mb.exec_()
