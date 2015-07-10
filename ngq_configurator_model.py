# -*- coding: utf-8 -*-
import os
import re
import json
import shutil
import tempfile
import zipfile

from PyQt4.QtCore import *
import xml.etree.ElementTree as ET
from PyQt4.QtNetwork import *

from logger import *

class CustomizationOption(QObject):
    changed = pyqtSignal()
    prepareForArchiveError = pyqtSignal(unicode)
    prepareForArchiveProcess = pyqtSignal(int, int)

    def __init__(self, name, parent=None, **kwargs):
        # kwargs:
        #     u'default_value' - default option value may be unicode or tuple(option, dened_func)
        QObject.__init__(self, parent)
        self.__name = name
        self.__value = None
        self.__defalut_value = None

        if kwargs.has_key(u'default_value'):
            self.__defalut_value = kwargs[u'default_value']

            if type(self.__defalut_value) == tuple:
                self.__defalut_value[0].changed.connect(self.changed.emit)

    def __str__(self):
        return "CustomizationOption with name '%s'"%self.__name

    def setDefaultValue(self):
        self.__value = None

    def getName(self):
        return self.__name

    @property
    def value(self):
        if self.__value is not None:
            return self.__value
        elif self.__defalut_value:
            if type(self.__defalut_value) == tuple:
                return self.__defalut_value[1](self.__defalut_value[0])
            return self.__defalut_value
        else:
            return None

    @value.setter
    def value(self, v):
        self.__value = v
        self.changed.emit()

    def asDict(self):
        if self.value is None:
            return {}
        else:
            return self._asDict()

    def prepareForArchive(self, archive_root_dir):
        return self._prepareForArchive(archive_root_dir)

    def resetFromJson(self, configuration):
        if configuration.has_key(self.__name):
            self.value = configuration[self.__name]

    def reset(self):
        self.__value = None
        self.changed.emit()

class StringCustomizationOption(CustomizationOption):
    def __init__(self, name, parent=None, **kwargs):
        CustomizationOption.__init__(self, name, parent, **kwargs)

    def _asDict(self):
        return {self.getName(): self.value}

    def _prepareForArchive(self, archive_root_dir):
        self.prepareForArchiveProcess.emit(0,0)
        return {self.getName(): self.value}

class FileCustomizationOption(CustomizationOption):
    def __init__(self, name, parent=None, **kwargs):
        CustomizationOption.__init__(self, name, parent, **kwargs)

    def _prepareForArchive(self, archive_root_dir):
        self.prepareForArchiveProcess.emit(0,0)
        if self.value is not None:
            if QFileInfo(self.value).isFile():
                file_base_name = os.path.basename(self.value)
                shutil.copyfile( self.value, os.path.join(archive_root_dir,file_base_name) )
                return {self.getName(): file_base_name}
            else:
                dir_base_name = os.path.basename(self.value)
                shutil.copytree(
                    self.value,
                    os.path.join(archive_root_dir, dir_base_name) )
                return {self.getName(): dir_base_name}
        else:
            return {}

    def _asDict(self):
        return {self.getName(): self.value}

class QGISOptionsOption(CustomizationOption):
    """
        {"<options set name>": "<options set dir>", ...}
    """
    def __init__(self, parent=None, **kwargs):
        CustomizationOption.__init__(self, u"default_qgis_options_dirs", parent, **kwargs)

    def _prepareForArchive(self, archive_root_dir):
        configuration = {}
        for opt_set_name in self.value.keys():
            shutil.copytree(
                    self.value[opt_set_name],
                    os.path.join(archive_root_dir, opt_set_name + "-" + os.path.basename(self.value[opt_set_name])) )

            configuration[opt_set_name] = opt_set_name + "-" + os.path.basename(self.value[opt_set_name])

        return {self.getName(): configuration}

    def _asDict(self):
        return {self.getName(): self.value}

class PluginsCustomizationOption(CustomizationOption):
    def __init__(self, name, parent=None, **kwargs):
        CustomizationOption.__init__(self, name, parent, **kwargs)

    def _prepareForArchive(self, archive_root_dir):

        if self.value is None:
            return {self.getName(): []}

        configuration = []
        plugins_dir = os.path.join(archive_root_dir,"plugins")
        os.mkdir(plugins_dir)

        self.prepareForArchiveProcess.emit(0, len(self.value))
        counter = 0
        for plugin in self.value:
            download_fail = False
            if plugin[u'type'] == 0:
                shutil.copytree(
                    os.path.join(plugin[u'dest'], plugin[u'name']),
                    os.path.join(plugins_dir, plugin[u'name']) )

            elif plugin[u'type'] == 1:
                self.pd = PluginDownloader(plugin[u'dest'], plugin[u'name'])
                if self.pd.download(plugins_dir) == False:
                    download_fail = True

            if not download_fail:
                configuration.append({u'name': plugin[u'name']})

            counter += 1
            self.prepareForArchiveProcess.emit(counter, len(self.value))

        return {self.getName(): configuration}

    def _asDict(self):
        return {self.getName(): self.value}

class AboutPagesCustomizationOption(CustomizationOption):
    def __init__(self, name, parent=None, **kwargs):
        CustomizationOption.__init__(self, name, parent, **kwargs)

    def _prepareForArchive(self, archive_root_dir):
        configuration = []
        files_dir = os.path.join(archive_root_dir,"about_pages_contents")
        os.mkdir(files_dir)

        self.prepareForArchiveProcess.emit(0, len(self.value))
        counter = 0
        for page in self.value:
            configuration.append(page)

            if page.has_key(u'content_file'):
                src_file = open( page[u'content_file'], "r" )
                dst_file = open( os.path.join(files_dir, os.path.basename(page[u'content_file'])), "w" )

                for src_line in src_file:
                    dst_line = src_line
                    m = re.search('src=".+"', src_line)
                    if m is not None:
                        file_path = re.search('".+"', m.group()).group().strip('"')
                        file_name = os.path.basename(file_path)
                        dst_line = dst_line.replace(file_path, file_name)

                        if not os.path.exists(file_path):
                            reletive_dir = os.path.dirname(page[u'content_file'])
                            file_path = os.path.join(reletive_dir, file_path)
                            if not os.path.exists(file_path):
                                continue

                        shutil.copyfile(
                            file_path,
                            os.path.join(files_dir, file_name)
                        )
                    dst_file.write(dst_line)

                src_file.close()
                dst_file.close()
                configuration[counter][u'content_file'] = os.path.basename(page[u'content_file'])

            counter += 1

        return {self.getName(): configuration}

    def _asDict(self):
        return {self.getName(): self.value}

class NGQConfiguratorModel(QObject):
    saveArchiveProgressStarted = pyqtSignal()
    saveArchiveProgressFinished = pyqtSignal()
    saveArchiveProgressError = pyqtSignal(unicode)
    saveArchiveTotalProgress = pyqtSignal(int, int)
    saveArchiveSubProgress = pyqtSignal(int, int)

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self.__options = []

    def addOption(self, option):
        #Check for same name
        self.__options.append(option)

    def saveAsLocalSettings(self, filename):
        Log("Save as local settings: %s"%filename, u'debug' )

        configuration = {}
        for option in self.__options:
            configuration.update( option.asDict() )

        file = QFile(filename)
        file.open(QIODevice.WriteOnly | QIODevice.Text)

        file.write( json.dumps(configuration, ensure_ascii=False).encode('utf8') )

        file.close()

    def saveAsArchive(self, filename):
        self.saveArchiveProgressStarted.emit()
        self.t = QThread(self)
        self.w = ConfigArchiveMaker(filename, self.__options)
        self.w.moveToThread(self.t)

        self.t.started.connect(self.w.run)
        self.w.finished.connect(self.t.quit)
        self.w.finished.connect(self.saveArchiveProgressFinished.emit)
        self.w.progress.connect(self.saveArchiveTotalProgress.emit)
        self.w.subProgress.connect(self.saveArchiveSubProgress.emit)

        self.t.start()

    def loadFromLocalSettings(self, filename):
        Log("Load from local settings: %s"%filename, u'debug' )

        if not os.path.exists(filename):
            Log("Load from local settings: %s"%filename, u'error' )
            return

        with open(filename, 'r') as f:
            data = f.read().decode('utf8')

            try:
                configuration = json.loads(data)

                for option in self.__options:
                    option.resetFromJson(configuration)

            except ValueError:
                pass


    def loadFromArchive(self,filename):
        pass

    def reset(self):
        for option in self.__options:
                option.reset()

class ConfigArchiveMaker(QObject):
        started = pyqtSignal()
        finished = pyqtSignal()
        errorOcured = pyqtSignal(unicode)
        progress = pyqtSignal(int, int)

        subProgress = pyqtSignal(int, int)

        def __init__(self, archive_name, options, parent=None):
            QObject.__init__(self, parent)
            self.__archive_name = archive_name
            self.__archive_prepare_dir = tempfile.mkdtemp('','ngq_configurator_result_')

            self.__options = options

            self.__progress = [0, len(options)]
            self.__progress[1] += 1 # for zipping process

            self.__must_stop = False

        def run(self):
            self.started.emit()
            self.progress.emit(self.__progress[0], self.__progress[1])

            configuration = {}

            for option in self.__options:

                if self.__must_stop == True:
                    return

                option.prepareForArchiveProcess.connect(self.subProgress.emit)
                option.prepareForArchiveError.connect(self.__optionPrepareError)
                configuration.update(option.prepareForArchive(self.__archive_prepare_dir))

                self.__progress[0] += 1
                self.progress.emit(self.__progress[0], self.__progress[1])

            settings_file = open(os.path.join(self.__archive_prepare_dir,"settings.txt"), 'w')
            settings_file.write( json.dumps(configuration) )
            settings_file.close()

            self.__zipping()

            self.__progress[0] += 1
            self.progress.emit(self.__progress[0], self.__progress[1])

            #shutil.rmtree(settings_dir, True)
            self.finished.emit()

        def __optionPrepareError(self, unicode):
            self.errorOcured.emit()
            self.__must_stop = True

        def stop(self):
            self.__must_stop = True

        def __zipping(self):
            total_files_count = 0
            for root, dirs, files in os.walk(self.__archive_prepare_dir):
                for file in files:
                    total_files_count +=1

            def zipdir(path, zip):
                files_counter = 0
                for root, dirs, files in os.walk(path):
                    for file in files:
                        zip.write(os.path.join(root, file), os.path.join( os.path.relpath(root, path), file) )
                        self.subProgress.emit(files_counter, total_files_count)
                        files_counter += 1

            zipf = zipfile.ZipFile(self.__archive_name, 'w')
            zipdir(self.__archive_prepare_dir, zipf)

            self.subProgress.emit(total_files_count, total_files_count)

            zipf.close()

class PluginDownloader(QObject):
    def __init__(self, download_url, plugin_name, parent = None):
        QObject.__init__(self, parent)

        self.__download_url = download_url
        self.__plugin_name = plugin_name

        self.__net_manager = QNetworkAccessManager()
        self.__net_request = QNetworkRequest(QUrl(self.__download_url))

    def download(self, dest_dir):
        print "self.__download_url: ", self.__download_url
        if self.__download_url.split('/')[-1] == "":
            return False

        download_file = os.path.join(dest_dir, self.__download_url.split('/')[-1])

        print "download_file: ", download_file
        print "download_file: ", len(download_file)


        self.loop = QEventLoop()
        #self.__net_request = QNetworkRequest(QUrl(self.__download_url))
        self.__replay = self.__net_manager.get(self.__net_request)
        self.__replay.finished.connect(self.loop.quit)
        self.loop.exec_()

        with open(download_file, 'wb') as f:
            f.write(self.__replay.readAll())

        self.unzip(download_file, dest_dir)

        os.remove(download_file)

        return True
    def unzip(self, source_filename, dest_dir):
        with zipfile.ZipFile(source_filename) as zf:
            zf.extractall(dest_dir)
