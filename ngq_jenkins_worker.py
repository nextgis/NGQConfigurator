# -*- coding: utf-8 -*-
import sys
import jenkins
import traceback

from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtNetwork import *

from logger import Log
from post_helper import encode_parameters
from ngq_builds_manager_model import BuildSystemModel, Build

class JenkinsJobSetter(QObject):
    started = pyqtSignal(unicode)
    finished = pyqtSignal()
    error = pyqtSignal(unicode)

    def __init__(self, config_archive, parent = None):
        QObject.__init__(self, parent)
        self.__config_archive = config_archive

    def start(self):
        settings = QSettings()
        jenkins_url = unicode(settings.value("jenkins_url", "", type = QString)).encode('utf-8')
        #jenkins_user_name = unicode(settings.value("jenkins_user_name", "", type = QString)).encode('utf-8')
        #jenkins_user_pass = unicode(settings.value("jenkins_user_pass", "", type = QString)).encode('utf-8')
        #jenkins_job_name = unicode(settings.value("jenkins_job_name", "", type = QString)).encode('utf-8')
        jenkins_user_name = QApplication.instance().buid_system_user.encode('utf-8')
        jenkins_user_pass = QApplication.instance().buid_system_password.encode('utf-8')
        jenkins_job_name = QApplication.instance().buid_system_proj_name.encode('utf-8')

        self.started.emit("Seting job with name %s"%jenkins_job_name)
        try:
            j = jenkins.Jenkins(jenkins_url, jenkins_user_name, jenkins_user_pass)
            url = jenkins_url + "/" + jenkins.BUILD_WITH_PARAMS_JOB%{"name":jenkins_job_name}

            values = {'settings.zip' : open( str(self.__config_archive), 'rb')}
            datagen, headers = encode_parameters(values)

            req = jenkins.Request( url, datagen, headers )
            resp = j.jenkins_open(req)

        #except jenkins.JenkinsException as ex:
        #    self.error.emit(ex.message)
        #except:
        #    self.error.emit("Unexpected error: %s"%sys.exc_info()[0])
        #    print sys.exc_info()
        #    print sys.exc_info()[0]
        except:
            trace = traceback.format_exc()
            self.error.emit(trace)

        self.finished.emit()


class JenkinsJobWorker(QObject):
    foundBuildInQueue = pyqtSignal(dict)
    foundBuildInBuilding = pyqtSignal(dict)
    allBuildsInArchive = pyqtSignal(list)
    foundBuildInArchive = pyqtSignal(dict)

    errorOccurred = pyqtSignal(unicode)

    finished = pyqtSignal()

    def __init__(
            self, check_time=10000000, done_builds_max_count=2, parent=None):
        QObject.__init__(self, parent)

        self.__check_time = check_time
        self.__done_builds_max_count = done_builds_max_count

        self.active = True

    def run(self):
        # QApplication.instance().logger.info("JenkinsJobWorker start")
        Log(u'info', "JenkinsJobWorker start")

        while(self.active):
            self.askJenkins()
            self.thread().usleep(self.__check_time)
        self.finished.emit()

    def askJenkins(self):
        # settings = QSettings("NextGIS", "NGQ Configurator")
        # self.jenkins_url = unicode(
        #                     settings.value("jenkins_url", "", type=QString))
        self.jenkins_url = QApplication.instance().buid_system_path
        self.jenkins_user_name = QApplication.instance().buid_system_user
        self.jenkins_user_pass = QApplication.instance().buid_system_password
        self.jenkins_job_name = QApplication.instance().buid_system_proj_name

        try:
            self.j = jenkins.Jenkins(
                                self.jenkins_url,
                                self.jenkins_user_name,
                                self.jenkins_user_pass)

            job_info = self.j.get_job_info(self.jenkins_job_name)

            if job_info['inQueue'] == True:
                build_id_in_queue = job_info['nextBuildNumber']
                build_info = job_info[u'queueItem']
                build_info.update({u'number': build_id_in_queue})
                self.foundBuildInQueue.emit( build_info )
            else:
                self.foundBuildInQueue.emit( {u'number':-1} )

            if len(job_info[u'builds']) > 0:
                last_build_info = self.j.get_build_info(self.jenkins_job_name, job_info[u'lastBuild'][u'number'])
                if last_build_info[u'building'] == True:
                    self.foundBuildInBuilding.emit( last_build_info )
                else:
                    self.foundBuildInBuilding.emit( {u'number':-1} )

                builds = job_info[u'builds']
                if last_build_info[u'building'] == True:
                    builds = builds[1:]
                builds = builds[:self.__done_builds_max_count]
                builds.reverse()
                self.allBuildsInArchive.emit([b[u'number'] for b in builds])

                for build in builds:
                    try:
                        build_info = self.j.get_build_info(self.jenkins_job_name, build[u'number'])
                        self.foundBuildInArchive.emit(build_info)
                    except jenkins.JenkinsException as ex:
                        pass

                return (job_info, last_build_info)
        except jenkins.JenkinsException as ex:
            self.errorOccurred.emit( ex.message.decode('cp1251') )
        except:
            self.errorOccurred.emit("Unexpected error: %s" % sys.exc_info()[0])


class JenkinsJobModel(BuildSystemModel):
    def __init__(self, parent=None):
        BuildSystemModel.__init__(self, parent)

        self.__update_info_time_interval = 1000000

        self.__thread = QThread(self)
        self.__j_worker = JenkinsJobWorker(self.__update_info_time_interval, 5)
        self.__j_worker.moveToThread(self.__thread)
        self.__j_worker.foundBuildInQueue.connect(self.__inQueueBuildProcess)
        self.__j_worker.foundBuildInBuilding.connect(
            self.__inBuildingBuildProcess)
        self.__j_worker.foundBuildInArchive.connect(self.__doneBuildProcess)
        self.__j_worker.allBuildsInArchive.connect(self.__doneBuildsProcess)
        self.__j_worker.errorOccurred.connect(self.__errorOccurredProcess)
        self.__j_worker.finished.connect(self.__thread.quit)
        self.__j_worker.finished.connect(self.__thread.deleteLater)
        self.__thread.started.connect(self.__j_worker.run)

    def _resetModel(self):
        if self.__thread.isRunning():
            self.__thread.terminate()

        self.__thread.start()

    def __inQueueBuildProcess(self, build_info):
        if self.isStoped():
            return

        build_number = build_info[u'number']

        if build_number == -1:
            if len(self._getBuildsByState(self.IN_QUEUE_BUILD_STATE)) != 0:
                for build in self._getBuildsByState(self.IN_QUEUE_BUILD_STATE):
                    self._removeBuild(
                        build.getNumber(), self.IN_QUEUE_BUILD_STATE)
        else:
            state_id = self._getStateBuidByNumber(build_number)
            if state_id is None:
                self._addBuild(Build(**build_info), self.IN_QUEUE_BUILD_STATE)
            elif state_id != self.IN_QUEUE_BUILD_STATE:
                self._removeBuild(build_number, state_id)
                self._addBuild(Build(**build_info), self.IN_QUEUE_BUILD_STATE)
            else:
                self._buildChangedStateParam(Build(**build_info))

        self.__noErrorProcess()

    def __inBuildingBuildProcess(self, build_info):
        if self.isStoped():
            return

        build_number = build_info[u'number']
        if build_number == -1:
            if len(self._getBuildsByState(self.IN_PROCESS_BUILD_STATE)) != 0:
                for build in self._getBuildsByState(
                                self.IN_PROCESS_BUILD_STATE):
                    self._removeBuild(
                        build.getNumber(), self.IN_PROCESS_BUILD_STATE)
        else:
            state_id = self._getStateBuidByNumber(build_number)
            if state_id is None:
                self._addBuild(
                    Build(**build_info), self.IN_PROCESS_BUILD_STATE)
            elif state_id != self.IN_PROCESS_BUILD_STATE:
                self._removeBuild(build_number, state_id)
                self._addBuild(
                    Build(**build_info), self.IN_ARCHIVE_BUILD_STATE)
            else:
                self._buildChangedStateParam(Build(**build_info))

        self.__noErrorProcess()

    def __doneBuildProcess(self, build_info):
        if self.isStoped():
            return

        build_number = build_info[u'number']
        state_id = self._getStateBuidByNumber(build_number)

        if state_id is None:
            self._addBuild(Build(**build_info), self.IN_ARCHIVE_BUILD_STATE)
        elif state_id != self.IN_ARCHIVE_BUILD_STATE:
            self._removeBuild(build_number, state_id)
            self._addBuild(Build(**build_info), self.IN_ARCHIVE_BUILD_STATE)

        self.__noErrorProcess()

    def __doneBuildsProcess(self, builds_ids):
        if self.isStoped():
            return

        removed_numbers = []
        for build in self._getBuildsByState(self.IN_ARCHIVE_BUILD_STATE):
            if build.getNumber() not in builds_ids:
                removed_numbers.append(build.getNumber())

        for number in removed_numbers:
            self._removeBuild(number, self.IN_ARCHIVE_BUILD_STATE)

        self.__noErrorProcess()

    def __errorOccurredProcess(self, msg):
        if self.isStoped():
            return

        self.modelChangeState.emit((self.MODEL_STATE_ERROR, msg))
        QApplication.instance().logger.error(msg)

    def __noErrorProcess(self):
        self.modelChangeState.emit((self.MODEL_STATE_NORMAL, None))

if __name__ == "__main__":
    pass
