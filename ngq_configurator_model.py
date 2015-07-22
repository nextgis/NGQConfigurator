# -*- coding: utf-8 -*-
import os
import re
import json
import shutil
import tempfile
import zipfile
import traceback

from PyQt4.QtCore import *
from PyQt4.QtNetwork import *

from logger import Log


class CustomizationOption(QObject):
    changed = pyqtSignal()
    prepareForArchiveError = pyqtSignal(unicode)
    prepareForArchiveProcess = pyqtSignal(int, int)

    def __init__(self, name, parent=None, **kwargs):
        # kwargs:
        #   u'default_value' -
        #    default option value may be unicode or tuple(option, dened_func)
        QObject.__init__(self, parent)
        self.__name = name
        self.__value = None
        self.__defalut_value = None

        if kwargs.has_key(u'default_value'):
            self.__defalut_value = kwargs[u'default_value']

            if type(self.__defalut_value) == tuple:
                self.__defalut_value[0].changed.connect(self.changed.emit)

    def __str__(self):
        return "CustomizationOption with name '%s'" % self.__name

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
        Log(u"Prepare option {0} ({1})".format(self.getName(), self.__class__.__name__), u'debug')
        try:
            res = self._prepareForArchive(archive_root_dir)
            Log(u"Prepare res: {0}".format(res), u'debug')
            return res
        except:
            trace = traceback.format_exc()
            Log(u"Prepare option FAIL:\n{0}".format(trace), u'error')
            self.prepareForArchiveError.emit(trace)
            return {}

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
        self.prepareForArchiveProcess.emit(0, 0)

        res = {}

        if self.value is not None:
            res = {self.getName(): self.value}

        return res


class FileCustomizationOption(CustomizationOption):
    def __init__(self, name, parent=None, **kwargs):
        CustomizationOption.__init__(self, name, parent, **kwargs)

    def _asDict(self):
        return {self.getName(): self.value}

    def _prepareForArchive(self, archive_root_dir):
        self.prepareForArchiveProcess.emit(0, 1)

        if self.value is None:
            self.prepareForArchiveProcess.emit(1, 1)
            return {}

        if QFileInfo(self.value).isFile():
            file_base_name = os.path.basename(self.value)
            shutil.copyfile(self.value,
                            os.path.join(archive_root_dir, file_base_name))

            self.prepareForArchiveProcess.emit(1, 1)
            return {self.getName(): file_base_name}
        else:
            dir_base_name = os.path.basename(self.value)
            shutil.copytree(
                self.value,
                os.path.join(archive_root_dir, dir_base_name))

            self.prepareForArchiveProcess.emit(1, 1)
            return {self.getName(): dir_base_name}


class QGISOptionsOption(CustomizationOption):
    """
        {"<options set name>": "<options set dir>", ...}
    """
    def __init__(self, parent=None, **kwargs):
        CustomizationOption.__init__(
            self,
            u"default_qgis_options_dirs",
            parent, **kwargs)

    def _asDict(self):
        return {self.getName(): self.value}

    def _prepareForArchive(self, archive_root_dir):
        configuration = {}
        if self.value is None:
            return {}

        for opt_set_name in self.value.keys():
            Log(u"QGIS options name: {0}".format(opt_set_name), u'debug')

            qgis_options_dir_name = "{0}-{1}".format(opt_set_name,
                                                     os.path.basename(self.value[opt_set_name]))

            Log(u"QGIS options dir name: {0}".format(qgis_options_dir_name), u'debug')

            shutil.copytree(self.value[opt_set_name],
                            os.path.join(archive_root_dir, qgis_options_dir_name))

            configuration[opt_set_name] = qgis_options_dir_name

        return {self.getName(): configuration}


class PluginsCustomizationOption(CustomizationOption):
    def __init__(self, name, parent=None, **kwargs):
        CustomizationOption.__init__(self, name, parent, **kwargs)

    def _asDict(self):
        return {self.getName(): self.value}

    def _prepareForArchive(self, archive_root_dir):
        if self.value is None:
            return {self.getName(): []}

        configuration = []
        plugins_dir = os.path.join(archive_root_dir, "plugins")
        os.mkdir(plugins_dir)

        self.prepareForArchiveProcess.emit(0, len(self.value))
        counter = 0

        for plugin in self.value:
            Log(u"Plugin name: {0}".format(plugin[u'name']), u'debug')

            get_plugin_fail = False

            if plugin[u'type'] == 0:
                Log(u"Copy plugin from local PC: {0} START".format(os.path.join(plugin[u'dest'], plugin[u'name'])), u'debug')

                shutil.copytree(
                    os.path.join(plugin[u'dest'], plugin[u'name']),
                    os.path.join(plugins_dir, plugin[u'name']))

                Log(u"Copy plugin from local PC FINISH", u'debug')
            elif plugin[u'type'] == 1:
                Log(u"Download plugin from: {0} START".format(plugin[u'dest']), u'debug')

                self.pd = PluginDownloader(plugin[u'dest'])
                pl_name = self.pd.download(plugins_dir)

                if pl_name is None:
                    get_plugin_fail = True
                    Log(u"Download plugin FAIL", u'error')
                else:
                    plugin[u'name'] = pl_name
                    Log(u"Download plugin with name: {0} FINISH".format(plugin[u'name']), u'debug')

            if not get_plugin_fail:
                configuration.append({u'name': plugin[u'name']})

            counter += 1
            self.prepareForArchiveProcess.emit(counter, len(self.value))

        return {self.getName(): configuration}


class AboutPagesCustomizationOption(CustomizationOption):
    def __init__(self, name, parent=None, **kwargs):
        CustomizationOption.__init__(self, name, parent, **kwargs)

    def _asDict(self):
        return {self.getName(): self.value}

    def _prepareForArchive(self, archive_root_dir):
        if self.value is None:
            return {}

        configuration = []
        files_dir = os.path.join(archive_root_dir, "about_pages_contents")
        os.mkdir(files_dir)

        self.prepareForArchiveProcess.emit(0, len(self.value))
        counter = 0
        for page in self.value:
            configuration.append(page)

            if page.has_key(u'content_file'):
                Log(u"New page name: {0}".format(page[u'name'][0]), u'debug')
                Log(u"New page content: {0}".format(page[u'content_file']), u'debug')

                src_file = open(page[u'content_file'], "r")
                dst_file = open(os.path.join(files_dir,
                                             os.path.basename(page[u'content_file'])),
                                "w")

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
        Log(u"Add option: %s" % option.getName(), u'info')
        self.__options.append(option)

    def saveAsLocalSettings(self, filename):
        Log(u"Save as local settings in %s START" % filename, u'info')

        configuration = {}
        for option in self.__options:
            configuration.update(option.asDict())

        file = QFile(filename)
        file.open(QIODevice.WriteOnly | QIODevice.Text)

        json_str = json.dumps(configuration, ensure_ascii=False, indent=4).encode('utf8')
        file.write(json_str)

        file.close()

        Log(u"Save as local settings in %s FINISH" % filename, u'info')

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
        self.w.errorOcured.connect(self.t.quit)
        self.w.errorOcured.connect(self.saveArchiveProgressError)

        self.t.start()

    def loadFromLocalSettings(self, filename):
        Log(u"Load local settings from %s START" % filename, u'info')

        if not os.path.exists(filename):
            Log(u"Load from local settings: %s" % filename, u'error')
            return

        with open(filename, 'r') as f:
            data = f.read().decode('utf8')

            try:
                configuration = json.loads(data)

                for option in self.__options:
                    Log(u"Reset option {0} from json START".format(option.getName()), u'debug')
                    option.resetFromJson(configuration)
                    Log(u"Reset option {0} from json FINISH".format(option.getName()), u'debug')

            except ValueError as err:
                Log(u"Reset option from {0}: {1}".format(filename, err), u'error')

        Log(u"Load local settings from %s FINISH" % filename, u'info')

    def loadFromArchive(self, filename):
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
            self.__archive_prepare_dir = tempfile.mkdtemp('', 'ngq_configurator_result_')

            self.__options = options

            self.__progress = [0, len(options)]
            self.__progress[1] += 1  # for zipping process

            self.__must_stop = False

        def run(self):
            Log(u"Prepare configuration archive: {0} START".format(self.__archive_name), u'info')
            self.started.emit()
            self.progress.emit(self.__progress[0], self.__progress[1])

            configuration = {}

            for option in self.__options:
                if self.__must_stop is True:
                    return

                option.prepareForArchiveProcess.connect(self.subProgress.emit)
                option.prepareForArchiveError.connect(self.__optionPrepareError)

                configuration.update(option.prepareForArchive(self.__archive_prepare_dir))

                self.__progress[0] += 1
                self.progress.emit(self.__progress[0], self.__progress[1])

            settings_file = open(os.path.join(self.__archive_prepare_dir, "settings.txt"), 'w')
            json_str = json.dumps(configuration, ensure_ascii=False, indent=4).encode('utf8')
            settings_file.write(json_str)
            settings_file.close()

            self.__zipping()

            self.__progress[0] += 1
            self.progress.emit(self.__progress[0], self.__progress[1])

            # shutil.rmtree(settings_dir, True)
            self.finished.emit()
            Log(u"Prepare configuration archive: {0} FINISH".format(self.__archive_name), u'info')

        def __optionPrepareError(self, trace):
            self.errorOcured.emit(trace)
            self.__must_stop = True

        def stop(self):
            self.__must_stop = True

        def __zipping(self):
            total_files_count = 0
            for root, dirs, files in os.walk(self.__archive_prepare_dir):
                for file in files:
                    total_files_count += 1

            def zipdir(path, zip):
                files_counter = 0
                for root, dirs, files in os.walk(path):
                    for file in files:
                        zip.write(os.path.join(root, file), os.path.join(os.path.relpath(root, path), file))
                        self.subProgress.emit(files_counter, total_files_count)
                        files_counter += 1

            zipf = zipfile.ZipFile(self.__archive_name, 'w')
            zipdir(self.__archive_prepare_dir, zipf)

            self.subProgress.emit(total_files_count, total_files_count)

            zipf.close()


class PluginDownloader(QObject):
    def __init__(self, download_url, parent=None):
        QObject.__init__(self, parent)

        self.__download_url = download_url

        self.__net_manager = QNetworkAccessManager()
        self.__net_request = QNetworkRequest(QUrl(self.__download_url))

    def download(self, dest_dir):
        # Log(u"Download plugin with url: %s" % self.__download_url, u'info' )

        self.loop = QEventLoop()
        self.__net_request = QNetworkRequest(QUrl(self.__download_url))

        self.__replay = self.__net_manager.get(self.__net_request)
        self.__replay.finished.connect(self.loop.quit)
        self.loop.exec_()

        download_file = "unknown_plugin"

        if self.__download_url.split('/')[-1] != "":
            download_file = self.__download_url.split('/')[-1]
        else:
            content_desp = unicode(QString(self.__replay.rawHeader('Content-Disposition')),
                                   encoding="UTF-8") + ";"

            m = re.search("filename=.*;", content_desp)
            if m is not None:
                download_file = m.group()[9:-1]

        download_file = os.path.join(dest_dir,
                                     download_file)

        # Log(u"Download plugin to file: %s" % download_file, u'info')

        with open(download_file, 'wb') as f:
            f.write(self.__replay.readAll())

        pl_name = self.unzip(download_file, dest_dir)

        os.remove(download_file)

        return pl_name

    def unzip(self, source_filename, dest_dir):
        with zipfile.ZipFile(source_filename) as zf:
            zf.extractall(dest_dir)
            return zf.namelist()[0].strip('/')
