# -*- coding: utf-8 -*-
import os
import sys

from PyQt4.QtGui import *
from PyQt4.QtCore import *

def Log(message, level = u'info'):
    logger = QApplication.instance().logger
    
    if level == u'debug':
        logger.debug(message)
    elif level == u'info':
        logger.info(message)
    elif level == u'debug':
        logger.debug (message)
    elif level == u'error':
        logger.error(msg)