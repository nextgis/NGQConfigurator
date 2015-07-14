# -*- coding: utf-8 -*-
import os
import jenkins
import datetime
import time
import traceback

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtNetwork import *

from message_box import MessageDialog

class Downloader(QDialog):
    def __init__(self, url, parent=None):
        QDialog.__init__(self, parent)
        settings = QSettings()

        self.setWindowTitle(self.tr("Download file"))
        self.setWindowFlags(Qt.WindowFlags(Qt.Dialog))

        self.url = QUrl(url)

        self.jenkins_url = QApplication.instance().buid_system_path
        self.jenkins_user_name = QApplication.instance().buid_system_user
        self.jenkins_user_pass = QApplication.instance().buid_system_password
        self.jenkins_job_name = QApplication.instance().buid_system_proj_name

        self.manager = QNetworkAccessManager(self)

        self.layout = QVBoxLayout(self)
        self.progress_bar = QProgressBar()
        self.layout.addWidget(self.progress_bar)

        self.output = QFile()


    def exec_(self):
        try:
            settings = QSettings()
            last_dir_for_artifact = settings.value(u'last_dir_for_artifact', defaultValue = unicode(), type=unicode)
            last_dir_for_artifact = unicode(last_dir_for_artifact.toUtf8(), encoding="UTF-8")

            filename = QFileInfo(self.url.path()).fileName()
            if filename.isEmpty():
                filename = u"download"
            else:
                filename = unicode(filename.toUtf8(), encoding="UTF-8")

            fileName = QFileDialog.getSaveFileName(self,
                                                self.tr("Save artifact"),
                                                os.path.join(last_dir_for_artifact, filename)
                                                )

            if fileName.isNull() == False:
                fileName = unicode(fileName.toUtf8(), encoding="UTF-8")
                settings.setValue(u'last_dir_for_artifact', os.path.dirname(fileName))

                self.output.setFileName( fileName )
                if self.output.open(QIODevice.WriteOnly):
                    self.start()
                    QDialog.exec_(self)

        except:
            trace = traceback.format_exc()
            last_line = trace.splitlines()[-1]
            MessageDialog.critical(self, self.tr("Error"), last_line, trace)

        self.deleteLater()
        return QDialog.Rejected

    def start(self):
        req = QNetworkRequest( self.url )
        concatenated = QString(self.jenkins_user_name + ":" + self.jenkins_user_pass)
        data = concatenated.toLocal8Bit().toBase64()
        headerData = QString("Basic " + data)
        req.setRawHeader("Authorization", headerData.toLocal8Bit())

        self.currentDownload = self.manager.get(req)
        self.currentDownload.downloadProgress.connect(self.progress)
        self.currentDownload.finished.connect(self.finish)
        self.currentDownload.readyRead.connect(self.readyRead)

    def progress(self, a, b):
        self.progress_bar.setMaximum(b)
        self.progress_bar.setValue(a)

    def finish(self):
        self.output.close()
        self.hide()
        self.deleteLater()

    def readyRead(self):
        self.output.write(self.currentDownload.readAll())
        self.output.flush()

class BuildInfoWidget(QWidget):
    def __init__(self, build, parent=None):
        QWidget.__init__(self, parent)

        self.build_number = build.getNumber()
        settings = QSettings()

        self.jenkins_url = QApplication.instance().buid_system_path
        self.jenkins_user_name = QApplication.instance().buid_system_user
        self.jenkins_user_pass = QApplication.instance().buid_system_password
        self.jenkins_job_name = QApplication.instance().buid_system_proj_name

        self.j = jenkins.Jenkins(self.jenkins_url, self.jenkins_user_name, self.jenkins_user_pass)

        self.layout = QVBoxLayout(self)
        self.label = QLabel( self.tr("# %1\t%2").arg(self.build_number). arg(datetime.datetime.fromtimestamp(build.getTimestamp()/1000.0).strftime("%a %b %d %H:%M:%S %Y")), self )
        self.info = QLabel(self)
        self.info.setTextFormat(Qt.RichText)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.info)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        build_time = datetime.datetime.fromtimestamp( (build.getTimestamp() + build.getDuration()) / 1000.0).strftime('%H:%M:%S %d/%m/%y')

        artifacts = {}
        for artifact in build.getArtifacts():
            artifacts[artifact[u'fileName']] = self.j.server + "job/%s/%d/artifact/%s"%(self.jenkins_job_name, self.build_number, artifact[u'relativePath'])

        msg = "<stong>%s: %s</stong>"%(
            self.tr("Build time"),
            build_time)

        for artifact_filename in artifacts.keys():
            msg = msg + "<br/><a href=\"%s\">%s</a>"%(artifacts[artifact_filename], artifact_filename)

        self.info.setText( msg )
        self.info.linkActivated.connect(self.linkAct)

    def linkAct(self, link_url):
        self.d = Downloader(link_url, self)
        self.d.exec_()

class BuildingBuildInfoWidget(QWidget):
    def __init__(self, build, parent=None):
        QWidget.__init__(self, parent)
        self.layout = QVBoxLayout(self)
        self.label = QLabel( "# %d - %s"%(build.getNumber(), self.tr("Building")) )
        self.status = QLabel()
        self.status.setTextFormat(Qt.RichText)
        self.status.setText( "<em>%s...</em>"%self.tr("loading") )

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.status)

    def changeStatus(self, build):
        start_time = datetime.datetime.fromtimestamp(build.getTimestamp() / 1000.0).strftime('%H:%M:%S %d/%m/%y')
        estimated_end_time = datetime.datetime.fromtimestamp(build.getTimestamp() / 1000.0 + build.getEstimatedDuration() / 1000.0).strftime('%H:%M:%S %d/%m/%y')
        #msg = self.tr("Start time: %1 Estimated end time: %2").arg(start_time).arg(estimated_end_time)
        time_to_end = build.getTimestamp() / 1000.0 + build.getEstimatedDuration() / 1000.0 - time.mktime(datetime.datetime.now().timetuple())

        if time_to_end < 0:
            time_to_end = self.tr("Unknown")
        else:
            time_to_end = "%d %s"%(time_to_end / 60, self.tr("minutes"))

        msg = "<stong>%s: %s</stong><br><stong>%s: %s</stong><br><stong>%s: %s</stong>"%(
            self.tr("Start time"),
            start_time,
            self.tr("Estimated end time"),
            estimated_end_time,
            self.tr("Time to end"),
            time_to_end,
                )

        self.status.setText( msg )

class InQueueBuildInfoWidget(QWidget):
    def __init__(self, build, parent=None):
        QWidget.__init__(self, parent)
        self.layout = QVBoxLayout(self)
        self.label = QLabel( self.tr("# %1 - In queue").arg(build.getNumber()) )
        self.status = QLabel()
        self.status.setText( "<em>%s...</em>"%self.tr("loading") )
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.status)

    def changeStatus(self, build):
        self.status.setText( self.tr("Waiting status: %1").arg(build.getWhy()) )


if __name__ == "__main__":
    pass
