# -*- coding: utf-8 -*-
import urlparse
import xml.etree.ElementTree as ET

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtSvg import *
from PyQt4.QtNetwork import *

from ui.ui_plugins_manager import Ui_PluginsManagerWidget
from ui.ui_plugin_settings import Ui_AddPluginsDialog


class PluginSettings(object):
    TypeLocal = 0
    TypeRemote = 1

    def __init__(self, name, type, dest):
        self.name = name
        self.type = type
        self.dest = dest
        self.repo_name = ""


class PluginSettingsWidget(QDialog, Ui_AddPluginsDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.plugins = []

        self.leFilter.textChanged.connect(self.applayFilter)

        settings = QSettings()
        settings.beginGroup(u"qgis_repos")
        for repo_name in settings.allKeys():
            repo_url = settings.value(repo_name, type=QString)
            self.qgisRepos.addItem(repo_name)

        self.model = QStandardItemModel()
        #self.model = QSortFilterProxyModel()

        self.listView.setModel(self.model)
        self.listView.selectionModel().currentRowChanged.connect(self.loadPluginInfo)

        self.qgisRepos.currentIndexChanged.connect(self.loadPluginsFromRepo)

        self.loadPluginsFromRepo(self.qgisRepos.currentIndex())

    def loadPluginsFromRepo(self, index):
        self.model.clear()
        repo_name = self.qgisRepos.itemText(index)

        settings = QSettings()
        settings.beginGroup(u"qgis_repos")
        repo_url = settings.value(repo_name, type=QString)

        self.__net_manager = QNetworkAccessManager()
        self.__net_request = QNetworkRequest(QUrl(repo_url))

        self.__replay = self.__net_manager.get(self.__net_request)
        self.__replay.finished.connect(self.__loadPlugins)

    def applayFilter(self, text):
        indexes = range(0, self.model.rowCount())
        for i in indexes:
            item = self.model.item(i)
            pl_name = item.data(Qt.DisplayRole).toPyObject()
            self.listView.setRowHidden(i, not pl_name.startsWith(text, Qt.CaseInsensitive))

    def __loadPlugins(self, name_filter = None):
        xml_conf = self.__replay.readAll()
        root = ET.fromstring( xml_conf )

        for pyqgis_plugin in root.findall('pyqgis_plugin'):
            item = QStandardItem()
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setData(QVariant(Qt.Unchecked), Qt.CheckStateRole)
            item.setData(QVariant(pyqgis_plugin.get('name')), Qt.DisplayRole)
            attrinbutes = {}
            attrinbutes['name'] = pyqgis_plugin.get('name')
            add_attr = lambda attr_name: attrinbutes.update( {attr_name: pyqgis_plugin.find(attr_name).text} ) if pyqgis_plugin.find(attr_name) is not None else attrinbutes.update( {attr_name: ""} )
            add_attr('description')
            add_attr('about')
            add_attr('author_name')
            add_attr('download_url')
            add_attr('file_name')

            item.setData(QVariant(attrinbutes), Qt.UserRole + 1)
            self.model.appendRow(item)

    def loadPluginInfo(self, current, previous):
        res = self.model.data(current, Qt.UserRole + 1).toPyObject()
        self.textBrowser.setHtml(
            """ <h1> %s </h1>
                <h3> %s </h3>
                %s <br/>
                %s: %s <br/>
                %s: %s <br/>
                """ % (
                    res[QString('name')],
                    res[QString('description')],
                    res[QString("about")],
                    self.tr("Author"), res[QString("author_name")],
                    self.tr("Download url"), res[QString("download_url")]))

    def accept(self):
        indexes = range(0, self.model.rowCount())
        for i in indexes:
            item = self.model.item(i)
            pl_attrs = item.data(Qt.UserRole + 1).toPyObject()
            pl_checked = item.data(Qt.CheckStateRole).toPyObject()
            if pl_checked == Qt.Checked:
                pl_name = pl_attrs[QString('name')]
                pl_name = unicode(pl_name.toUtf8(), encoding="UTF-8")

                pl_dwn_url = unicode(pl_attrs[QString('download_url')].toUtf8(), encoding="UTF-8")

                pl = PluginSettings(pl_name,
                                    PluginSettings.TypeRemote,
                                    pl_dwn_url)

                pl.repo_name = unicode(self.qgisRepos.currentText().toUtf8(), encoding="UTF-8")

                self.plugins.append(pl)

        super(PluginSettingsWidget, self).accept()


class PluginsOption(QWidget, Ui_PluginsManagerWidget):
    def __init__(self, option, parent=None):
        QWidget.__init__(self, parent)

        self.__option = option
        self.__option.changed.connect(self.__setOptionValue)

        self.setupUi(self)
        self.pushButton_3.setEnabled(False)

        self.pbAddPluginsFromRepo.clicked.connect(self.addPluginFromRepo)
        self.pdAddPluginFromLocal.clicked.connect(self.addPluginFromLocal)
        self.pushButton_3.clicked.connect(self.deletePlugin)

        self.__setOptionValue()

        self.listWidget.itemClicked.connect(self.choosePluginInList)

    def __setOptionValue(self):
        self.listWidget.clear()
        if self.__option.value is not None:
            for plugin_settings in self.__option.value:
                item = QListWidgetItem(self.listWidget)

                if plugin_settings[u'type'] == PluginSettings.TypeLocal:
                    plugin = PluginSettings(plugin_settings[u'name'], plugin_settings[u'type'], plugin_settings[u'dest'])
                    item.setData(Qt.DisplayRole, plugin_settings[u'name'] + " [%s]"%plugin_settings[u'dest'])
                    item.setData(Qt.UserRole + 1, plugin)

                if plugin_settings[u'type'] == PluginSettings.TypeRemote:
                    plugin = PluginSettings(plugin_settings[u'name'], plugin_settings[u'type'], plugin_settings[u'dest'])
                    plugin.repo_name = plugin_settings['repo_name']
                    item.setData(Qt.DisplayRole, plugin_settings[u'name'] + " [%s]"%plugin_settings[u'repo_name'])
                    item.setData(Qt.UserRole + 1, plugin)

    def choosePluginInList(self, item):
        self.pushButton_3.setEnabled(True)

    def deletePlugin(self):
        item = self.listWidget.takeItem(self.listWidget.currentRow())
        self.updatePluginsSettings()

    def addPluginFromRepo(self):
        plug_set_dialog = PluginSettingsWidget()
        if plug_set_dialog.exec_():
            for plugin_settings in plug_set_dialog.plugins:
                item = QListWidgetItem(self.listWidget)
                item.setData(Qt.DisplayRole, plugin_settings.name + " [%s]" % plugin_settings.repo_name)
                item.setData(Qt.UserRole + 1, plugin_settings)

            self.updatePluginsSettings()

    def addPluginFromLocal(self):
        dirPath = QFileDialog.getExistingDirectory(
                    self,
                    self.tr("Select plugin directory"))

        if not dirPath.isNull():
            file_info = QFileInfo(dirPath)
            settings = PluginSettings(
                    unicode(file_info.baseName().toUtf8(), encoding="UTF-8"),
                    PluginSettings.TypeLocal,
                    unicode(file_info.absolutePath().toUtf8(), encoding="UTF-8"),
            )
            item = QListWidgetItem(self.listWidget)
            item.setData(Qt.DisplayRole, settings.name + " [%s]"%settings.dest)
            item.setData(Qt.UserRole + 1, settings)
            self.updatePluginsSettings()

    def updatePluginsSettings(self):
        plugins_settings = []
        for i in range(0, self.listWidget.count()):
            item = self.listWidget.item(i)
            pl_set = item.data(Qt.UserRole + 1).toPyObject()
            plugins_settings.append({
                u'name': pl_set.name,
                u'type': pl_set.type,
                u'dest': pl_set.dest,
                u'repo_name': pl_set.repo_name,
            })

        self.__option.value = plugins_settings
