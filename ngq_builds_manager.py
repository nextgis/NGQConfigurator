# -*- coding: utf-8 -*-
import os
import sys
import logging
import traceback

from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtNetwork import *

from build_info import *
from ngq_jenkins_worker import JenkinsJobModel, JenkinsJobSetter

from ui.ui_ngq_builds_manager import Ui_MainWindow
from ui.ui_connection_settings import Ui_Dialog

from message_box import MessageDialog

import resources_rc

class ConnectionSettingsDialog(QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
        self.label.setVisible(False)
        self.leUserName.setVisible(False)
        self.label_2.setVisible(False)
        self.lePassword.setVisible(False)
        self.label_3.setVisible(False)
        self.leJobName.setVisible(False)
        
        settings = QSettings()
        self.leJenkinsURL.setText(settings.value("jenkins_url", "", type = unicode))
        #self.leUserName.setText(settings.value("jenkins_user_name", "", type = unicode))
        #self.lePassword.setText(settings.value("jenkins_user_pass", "", type = unicode))
        #self.leJobName.setText(settings.value("jenkins_job_name", "", type = unicode))
        self.adjustSize()
        
    def accept(self):
        settings = QSettings()
        settings.setValue("jenkins_url", self.leJenkinsURL.text())
        #settings.setValue("jenkins_user_name", self.leUserName.text())
        #settings.setValue("jenkins_user_pass", self.lePassword.text())
        #settings.setValue("jenkins_job_name", self.leJobName.text())
        settings.sync()
        super(ConnectionSettingsDialog, self).accept()
        
class BuildsManagerMain(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.setWindowIcon( QIcon(":/NGQConfigurator/icons/ng.ico") )
        
        self.vlBuildsContainer.setAlignment(Qt.AlignTop)
        self.clearStatus()
        
        self.pbBookBuild.clicked.connect(self.setJenkinsJob)        
        self.actionConnection.triggered.connect(self.connectionSettingsDialogAction)
        
        self.bsm = JenkinsJobModel(self)
        
        self.bsm.buildComeToState.connect(self.buildComeToState)
        self.bsm.buildLeftCurrentState.connect(self.buildLeftCurrentState)
        self.bsm.buildChangedStateParam.connect(self.buildChangedStateParam)
        
        self.bsm.modelChangeState.connect(self.modelChangeState)
        self.bsm.start()  
    
    #================
    def buildComeToState(self, build, state):
        if state == self.bsm.IN_QUEUE_BUILD_STATE:
            self.inQueueBuildWidget = InQueueBuildInfoWidget( build, self )
            self.vlInQueueBuilds.addWidget(self.inQueueBuildWidget)
            
        elif state == self.bsm.IN_PROCESS_BUILD_STATE:
            self.inBuildingBuildWidget = BuildingBuildInfoWidget( build, self )
            self.vlInBuildingBuilds.addWidget(self.inBuildingBuildWidget)
        elif state == self.bsm.IN_ARCHIVE_BUILD_STATE:
            w = BuildInfoWidget( build, self )
            self.vlBuildsContainer.insertWidget(0,w)
        else:
            pass
            #print "Build %d come to UNKNOWN state"% build.getNumber()
            
    def buildLeftCurrentState(self, build, state_id):
        #print "Build %d left %s state"%(build.getNumber(),state_id)
        if state_id == self.bsm.IN_ARCHIVE_BUILD_STATE:
            for i in range(0, self.vlBuildsContainer.count()):
                w = self.vlBuildsContainer.itemAt(i).widget()
                if w.build_number == build.getNumber():
                    self.vlBuildsContainer.takeAt(i)
                    w.setParent(None)
                    break
        elif state_id == self.bsm.IN_PROCESS_BUILD_STATE:
            self.vlInBuildingBuilds.takeAt(0).widget().setParent(None)
        elif state_id == self.bsm.IN_QUEUE_BUILD_STATE:
            self.vlInQueueBuilds.takeAt(0).widget().setParent(None)
        else:
            pass
        
    def buildChangedStateParam(self, build, state_id):
        #print "Build %d change current state parameters"% build.getNumber()
        if state_id == self.bsm.IN_ARCHIVE_BUILD_STATE:
            pass
        elif state_id == self.bsm.IN_PROCESS_BUILD_STATE:
            self.vlInBuildingBuilds.itemAt(0).widget().changeStatus(build)
        elif state_id == self.bsm.IN_QUEUE_BUILD_STATE:
            self.vlInQueueBuilds.itemAt(0).widget().changeStatus(build)
        else:
            pass
        
    #===============================
    #Build system connection state
    def modelChangeState(self, state):
        if state[0] == self.bsm.MODEL_STATE_NORMAL:
            self.pbBookBuild.setEnabled(True)
            self.vlBuildsContainer.setEnabled(True)
            self.vlInQueueBuilds.setEnabled(True)
            self.vlInBuildingBuilds.setEnabled(True)
            self.clearStatus()
        else:
            self.pbBookBuild.setDisabled(True)
            for i in range(0, self.vlBuildsContainer.count()):
                self.vlBuildsContainer.itemAt(i).widget().setDisabled(True)
            
            for i in range(0, self.vlInQueueBuilds.count()):
                self.vlInQueueBuilds.itemAt(i).widget().setDisabled(True)
                
            for i in range(0, self.vlInBuildingBuilds.count()):
                self.vlInBuildingBuilds.itemAt(i).widget().setDisabled(True)
            
            if state[0] == self.bsm.MODEL_STATE_ERROR:
                self.showStatus("<em style='color:red'>%s...</em>"%state[1])
            elif state[0] == self.bsm.MODEL_STATE_FIRST_INIT:
                self.showStatus("<em>%s...</em>"%self.tr("Initialization"))
            elif state[0] == self.bsm.MODEL_STATE_USER_RESATRT:
                self.showStatus("<em>%s...</em>"%self.tr("Resatrting"))
    #=================
    # Build system connection settrings dialog
    def connectionSettingsDialogAction(self, checked):
        d = ConnectionSettingsDialog()
        r = d.exec_()
        d.close()
        
        if r == 1:
            self.resetSettings()          
            return True
        
        return False
        
    def resetSettings(self):       
        self.bsm.resetModel()
    
    def setJenkinsJob(self):
        try:
            settings = QSettings()
            configuration_file_archive = settings.value(u'configuration_file_archive', defaultValue = unicode(), type=unicode) 
            fileName = QFileDialog.getOpenFileName(self,
                                                self.tr("Select ngq configuration archive"),
                                                configuration_file_archive,
                                                self.tr("NGQ configuration archive (*.ngqca)")
                                                )
            fileName = unicode(fileName)
            
            if fileName != "":
                settings.setValue(u'configuration_file_archive', fileName)
                
                self.__job_setter_thread = QThread(self)
                self.job_setter = JenkinsJobSetter(fileName)
                self.job_setter.moveToThread(self.__job_setter_thread)
                self.__job_setter_thread.started.connect(self.job_setter.start)
                
                self.job_setter.finished.connect(self.__job_setter_thread.quit)
                #self.job_setter.finished.connect(self.__job_setter_thread.deleteLater)
                
                self.job_setter.started.connect(self.setJobStartHandle)
                self.job_setter.finished.connect(self.setJobFinishHandle)
                self.job_setter.error.connect(self.setJobErrorHandle)
                
                self.__job_setter_thread.start()
        except:
            trace = traceback.format_exc()
            last_line = trace.splitlines()[-1]
            MessageDialog.critical(self, self.tr("Error"), last_line, trace)
            
    def setJobStartHandle(self):
        #print "setJobStartHandle" 
        self.menuBar().setEnabled(False)
        self.showStatus(self.tr("Set job..."))
    
    def setJobFinishHandle(self):
        #print "setJobFinishHandle"
        self.menuBar().setEnabled(True)
        self.clearStatus()
    
    def setJobErrorHandle(self, trace):
        #print "setJobErrorHandle"
        #mb = QMessageBox.critical(self, self.tr("Setting job failed!"), "%s<br/><em style='color:red'>%s...</em>"%(self.tr("Setting job failed!"), msg) )
        trace = unicode(trace.toUtf8(), encoding="UTF-8")
        MessageDialog.critical(self, self.tr("Error"), trace.splitlines()[-1], trace)
        
    def showStatus(self, html):
        self.lManagerStatus.setVisible(True)
        self.lManagerStatus.setText(html)
    
    def clearStatus(self):
        self.lManagerStatus.setVisible(False)
        self.lManagerStatus.setText("")
            
class BuildsManagerApp(QApplication):
    def __init__(self, args):
        super(QApplication, self).__init__(args)
        self.buid_system_user = u"customizator"
        self.buid_system_password = u"customizator"
        self.buid_system_proj_name = u"NGQ_custom"
        
        self.setOrganizationName("NextGIS")
        self.setOrganizationDomain("nextgis.ru")
        self.setApplicationName("NGQ Builds manager")
        
        self.translator = QTranslator()
        self.translator.load(":/NGQConfigurator/i18n/ngq_configurator.qm")
        QApplication.installTranslator(self.translator)
    
        self.logger = logging.getLogger(unicode(self.applicationName()))
        self.logger.setLevel(logging.DEBUG)
        
        log_file_name = "_".join(unicode(self.applicationName()).split(u" "))+"_log.txt"
        
        fh = logging.FileHandler(os.path.join(unicode(self.applicationDirPath()), log_file_name))
        fh.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        
        self.logger.info(os.getcwd())
        self.logger.info(self.applicationDirPath())
        
        
        self.mw = BuildsManagerMain()
        self.mw.show()
        
if __name__ == "__main__":
    app = BuildsManagerApp(sys.argv)

    sys.exit(app.exec_())