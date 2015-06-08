# -*- coding: utf-8 -*-

from PyQt4.QtCore import QObject, pyqtSignal

class Build(object):
    def __init__(self, **kwargs):
        self.__kwargs = kwargs
        
    def __getAttribute(self, key):
        if self.__kwargs.has_key(key):
            return self.__kwargs[key]
        else:
            return None
        
    def getNumber(self):
        return self.__getAttribute(u'number')
    
    def getTimestamp(self):
        return self.__getAttribute(u'timestamp')
    
    def getDuration(self):
        return self.__getAttribute(u'duration')
    
    def getEstimatedDuration(self):
        return self.__getAttribute(u'estimatedDuration')
    
    def getWhy(self):
        return self.__getAttribute(u'why')
    
    def getArtifacts(self):
        artifacts = self.__getAttribute(u'artifacts')
        if artifacts is None:
            artifacts = []
        return artifacts
    
class BuildSystemModel(QObject):
    IN_QUEUE_BUILD_STATE = 1
    IN_PROCESS_BUILD_STATE = 2
    IN_ARCHIVE_BUILD_STATE = 3
    
    MODEL_STATE_NORMAL = 0
    MODEL_STATE_FIRST_INIT = 1
    MODEL_STATE_USER_RESATRT = 2
    MODEL_STATE_ERROR = 3 
    
    buildComeToState = pyqtSignal(Build, int)
    buildLeftCurrentState = pyqtSignal(Build, int)
    buildChangedStateParam = pyqtSignal(Build, int)
    
    modelChangeState = pyqtSignal(tuple)
    
    def __init__(self, parent = None):
        QObject.__init__(self, parent)
        
        self.__model_started = False
        
        self.__builds_list = {
            self.IN_QUEUE_BUILD_STATE:[],
            self.IN_PROCESS_BUILD_STATE:[], 
            self.IN_ARCHIVE_BUILD_STATE:[]
        }
    
    def isStoped(self):
        return  not self.__model_started
    
    def __resetModel(self, model_state):
        self.__model_started = False
        self.modelChangeState.emit( (model_state, None) )

        for state_id in self.__builds_list.keys():
            while len(self.__builds_list[state_id])>0 :
                build = self.__builds_list[state_id].pop()
                self.buildLeftCurrentState.emit(build, state_id)
        
        self._resetModel()
        self.__model_started = True
        
    def start(self):
        if self.__model_started == False:
            self.__resetModel( self.MODEL_STATE_FIRST_INIT )
        
    def resetModel(self):
        self.__resetModel( self.MODEL_STATE_USER_RESATRT )    
    
    def _getBuildsByState(self, state_id):
        if self.__builds_list.has_key(state_id):
            return self.__builds_list[state_id]
        return []
    
    def _getBuildByNumber(self, number, state_id):
        for state_id in self.__builds_list.keys():
            for build in self.__builds_list[state_id]:
                if build.getNumber() == number:
                    return build
        return None
    
    def _getStateBuidByNumber(self, number):
        for state_id in self.__builds_list.keys():
            for build in self.__builds_list[state_id]:
                if build.getNumber() == number:
                    return state_id
        return None
    
    def _addBuild(self, build, state_id):
        self.__builds_list[state_id].append(build)
        self.buildComeToState.emit(build, state_id)
    
    def _removeBuild(self, build_number, state_id):
        for build in self.__builds_list[state_id]:
            if build.getNumber() == build_number:
                self.__builds_list[state_id].remove(build)
                self.buildLeftCurrentState.emit(build, state_id)
                return True
            
        return False
    
    def _buildChangedStateParam(self, build):
        state_id = self._getStateBuidByNumber(build.getNumber())
        if state_id is not None:
            self.buildChangedStateParam.emit(build, state_id)
        