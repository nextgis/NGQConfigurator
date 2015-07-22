# -*- coding: utf-8 -*-
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
import traceback

from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtNetwork import *

from ngq_configurator_options import *
from ngq_configurator_option_plugins import *
from ngq_configurator_option_qgs_opts import *
from ngq_configurator_model import *
from message_box import MessageDialog

from ui.ui_ngq_configurator import Ui_NGQConfigurator
from ui.ui_qgis_repos import Ui_QGISReposDialog
from ui.ui_qgis_repo_settings import Ui_RepoSettingsDialog

import resources_rc


class ConfigPackageMakerDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle(self.tr("Make configuration package"))
        self.setFixedSize(250, 75)

        l = QVBoxLayout(self)
        self.pb_total = QProgressBar(self)
        l.addWidget(self.pb_total)
        self.pb_sub = QProgressBar(self)
        l.addWidget(self.pb_sub)

    def totalProgressHandel(self, i, j):
        if i == 0:
            self.pb_total.setRange(i, j)
        else:
            self.pb_total.setValue(i)

    def subProgressHandel(self, i, j):
        if i == 0:
            self.pb_sub.setRange(i, j)
        else:
            self.pb_sub.setValue(i)


class QGISReposModel(QAbstractTableModel):
    def __init__(self, parent=None, *args):
        QAbstractTableModel.__init__(self, parent, *args)

        self.arraydata = []
        self.headerdata = [self.tr("Name"), self.tr("URL")]

        settings = QSettings()
        settings.beginGroup(u"qgis_repos")

        for repo_name in settings.allKeys():
            repo_url = settings.value(repo_name, type=QString)
            self.arraydata.append([repo_name, repo_url])

    def removeRow(self, row, parent=QtCore.QModelIndex()):
        self.beginRemoveRows(parent, row, row)

        settings = QSettings()
        settings.beginGroup(u"qgis_repos")

        repo = self.arraydata.pop(row)
        settings.remove(repo[0])

        self.endRemoveRows()

    def insertRow(self, row, repo_name, repo_url, parent=QtCore.QModelIndex()):
        self.beginInsertRows(parent, row, row)

        settings = QSettings()
        settings.beginGroup(u"qgis_repos")

        self.arraydata.insert(row, [repo_name, repo_url])
        settings.setValue(repo_name, repo_url)

        self.endInsertRows()

    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()

        settings = QSettings()
        settings.beginGroup(u"qgis_repos")

        settings.remove(self.data(index, Qt.DisplayRole).toPyObject())
        settings.setValue(value[0], value[1])

        self.arraydata[row] = value

    def rowCount(self, parent):
        return len(self.arraydata)

    def columnCount(self, parent):
        return len(self.headerdata)

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        elif role == Qt.UserRole:
            return self.arraydata[index.row()]
        elif role != Qt.DisplayRole:
            return QVariant()
        return QVariant(self.arraydata[index.row()][index.column()])

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(self.headerdata[col])
        return QVariant()


class QGISRepoSettings(QDialog, Ui_RepoSettingsDialog):
    def __init__(self, repo_name, repo_url, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.gridLayout.setAlignment(Qt.AlignTop)

        self.repo_name = repo_name
        self.repo_url = repo_url

        self.leRepoName.setText(self.repo_name)
        self.leRepoURL.setText(self.repo_url)

    def accept(self):
        self.repo_name = self.leRepoName.text()
        self.repo_url = self.leRepoURL.text()

        QDialog.accept(self)


class QGISReposDialog(QDialog, Ui_QGISReposDialog):
    def __init__(self, parent = None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.pbAddRepo.clicked.connect(self.addRepoDialog)
        self.pbEditRepo.clicked.connect(self.editRepoDialog)
        self.pbDelRepo.clicked.connect(self.delRepo)

        self.model = QGISReposModel()
        self.tableView.setModel(self.model)

        self.tableView.setShowGrid(False)

        vh = self.tableView.verticalHeader()
        vh.setVisible(False)

        hh = self.tableView.horizontalHeader()
        hh.setClickable(False)
        hh.setStretchLastSection(True)

        self.tableView.resizeColumnsToContents()
        self.tableView.resizeRowsToContents()

        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)

        sm = self.tableView.selectionModel()
        sm.currentRowChanged.connect(self.selectRow)
        sm.setCurrentIndex(self.model.index(0, 0), QItemSelectionModel.Rows|QItemSelectionModel.Select)

    def addRepoDialog(self):
        dlg = QGISRepoSettings("","")
        if dlg.exec_():
            self.model.insertRow(0, dlg.repo_name, dlg.repo_url )

    def editRepoDialog(self):
        curModelIndex = self.tableView.currentIndex()
        r = self.model.data(curModelIndex, Qt.UserRole)
        dlg = QGISRepoSettings(r[0], r[1])
        if dlg.exec_():
            self.model.setData(curModelIndex, [dlg.repo_name, dlg.repo_url],  Qt.UserRole)

    def delRepo(self):
        curModelIndex = self.tableView.currentIndex()
        self.model.removeRow(curModelIndex.row())

    def selectRow(self, current, previous):
        self.pbDelRepo.setEnabled(True)
        self.pbEditRepo.setEnabled(True)


class NGQConfigurator(QMainWindow, Ui_NGQConfigurator):
    def __init__(self, load_conf, parent=None):
        QMainWindow.__init__(self, parent)
        self.setupUi(self)

        self.setWindowIcon(QIcon(":/NGQConfigurator/icons/ng.ico"))

        self.menuHelp.addAction(QWhatsThis.createAction(self))

        self.actionSave.triggered.connect(self.saveLocalConfiguration)
        self.actionSave.setShortcut(QKeySequence("Ctrl+S"))
        settings = QSettings()
        configuration_file = settings.value(u'configuration_file', defaultValue=unicode(), type=unicode)
        if configuration_file.isEmpty():
            self.actionSave.setEnabled(False)

        self.actionOpen.setShortcut(QKeySequence("Ctrl+O"))
        self.actionOpen.triggered.connect(self.openLocalConfiguration)

        self.actionSaveAs.triggered.connect(self.saveAsLocalConfiguration)
        self.actionImport.triggered.connect(self.importConfigurationFromArchive)

        self.actionExport.setShortcut(QKeySequence("Ctrl+E"))
        self.actionExport.triggered.connect(self.exportConfigurationToArchive)

        self.actionNew.triggered.connect(self.resetModel)

        self.actionQGIS_repositories.triggered.connect(self.editQGISrepos)

        self._model = NGQConfiguratorModel(self)
        self.__conf_pack_maker_dialog = ConfigPackageMakerDialog(self)
        self._model.saveArchiveProgressStarted.connect(self.__conf_pack_maker_dialog.show)
        self._model.saveArchiveProgressFinished.connect(self.__conf_pack_maker_dialog.hide)
        self._model.saveArchiveProgressFinished.connect(self.__conf_pack_maker_dialog.close)
        self._model.saveArchiveTotalProgress.connect(self.__conf_pack_maker_dialog.totalProgressHandel)
        self._model.saveArchiveSubProgress.connect(self.__conf_pack_maker_dialog.subProgressHandel)
        self._model.saveArchiveProgressError.connect(self.__conf_pack_maker_dialog.close)
        self._model.saveArchiveProgressError.connect(self.__show_error)

        self.common_options_container.setAlignment(Qt.AlignTop)
        self.advanced_options_container.setAlignment(Qt.AlignTop)

        prog_name_option = StringCustomizationOption(u'prog_name', default_value=u'Super GIS')
        self._model.addOption(prog_name_option)
        prog_name_view = StringOption(prog_name_option, self.tr(u'Program name'), self)
        prog_name_view.setToolTip(self.tr(u'Only Latin characters!'))
        prog_name_view.setStatusTip(self.tr(u'Only Latin characters!'))
        prog_name_view.setWhatsThis(self.tr(u'Name of program - identificator for Windows. Only Latin characters!'))
        self.common_options_container.addWidget(prog_name_view)

        ngq_icon_option = FileCustomizationOption(u'ngq_icon')
        self._model.addOption(ngq_icon_option)
        ngq_icon_view = ImageOption(ngq_icon_option, u'%s (only ico format)' % self.tr(u'NGQ Icon'), self)
        ngq_icon_view.setFilter("%s %s" % (self.tr(u'Image'), u'(*.ico)'))
        self.common_options_container.addWidget(ngq_icon_view)

        ngq_icon_x_16_option = FileCustomizationOption(u'ngq_icon_png_16')
        self._model.addOption(ngq_icon_x_16_option)
        ngq_icon_x_16_view = ImageOption(ngq_icon_x_16_option, u'%s x16 (only png format)' % self.tr(u'NGQ Icon'), self)
        ngq_icon_x_16_view.setFilter("%s %s" % (self.tr(u'Image'), u'(*.png)'))
        self.common_options_container.addWidget(ngq_icon_x_16_view)

        ngq_icon_x_64_option = FileCustomizationOption(u'ngq_icon_png_64')
        self._model.addOption(ngq_icon_x_64_option)
        ngq_icon_x_64_view = ImageOption(ngq_icon_x_64_option, u'%s x64 (only png format)' % self.tr(u'NGQ Icon'), self)
        ngq_icon_x_64_view.setFilter("%s %s" % (self.tr(u'Image'), u'(*.png)'))
        self.common_options_container.addWidget(ngq_icon_x_64_view)

        ngq_icon_svg_option = FileCustomizationOption(u'ngq_icon_svg')
        self._model.addOption(ngq_icon_svg_option)
        ngq_icon_svg_view = ImageOption(ngq_icon_svg_option, u'%s (only svg format)' % self.tr(u'NGQ Icon'), self)
        ngq_icon_svg_view.setFilter("%s %s" % (self.tr(u'Image'), u'(*.svg)'))
        self.common_options_container.addWidget(ngq_icon_svg_view)

        ngq_splash_option = FileCustomizationOption(u'ngq_splash')
        self._model.addOption(ngq_splash_option)
        ngq_splash_view = ImageOption(ngq_splash_option, u'%s (only png format)' % self.tr(u'NGQ Splash'), self)
        ngq_splash_view.setFilter("%s %s" % (self.tr(u'Image'), u'(*.png)'))
        self.common_options_container.addWidget(ngq_splash_view)

        installer_name_option = StringCustomizationOption(
            u'installer_name',
            default_value=(prog_name_option, lambda option: '_'.join(option.value.lower().split(' ')))
        )
        self._model.addOption(installer_name_option)
        installer_name_view = StringOption(installer_name_option, self.tr(u'Installer name'), self)
        # installer_name_view.setToolTip(self.tr(u'Only Latin characters!'))
        # installer_name_view.setStatusTip(self.tr(u'Only Latin characters!'))
        installer_name_view.setWhatsThis(self.tr(u'Only Latin characters!'))
        self.advanced_options_container.addWidget(installer_name_view)

        run_link_name_option = StringCustomizationOption(
            u'ngq_shortcut_name',
            default_value=(prog_name_option, lambda option: option.value.upper())
        )
        self._model.addOption(run_link_name_option)
        run_link_name_view = StringOption(run_link_name_option, self.tr(u'Run shortcut name'), self)
        self.advanced_options_container.addWidget(run_link_name_view)

        ngq_title_en_option = StringCustomizationOption(
            u'ngq_title_en',
            default_value=u'GIS \'NextGIS QGIS\''
        )
        self._model.addOption(ngq_title_en_option)
        ngq_title_en_view = StringOption(ngq_title_en_option, self.tr(u'NGQ Title eng'), self)
        # ngq_title_en_view.setToolTip(self.tr(u'Only Latin characters!'))
        # ngq_title_en_view.setStatusTip(self.tr(u'Only Latin characters!'))
        ngq_title_en_view.setWhatsThis(self.tr(u'Only Latin characters!'))
        self.advanced_options_container.addWidget(ngq_title_en_view)

        ngq_title_ru_option = StringCustomizationOption(
            u'ngq_title_tr',
            default_value=u'ГИС \'NextGIS QGIS\''
        )
        self._model.addOption(ngq_title_ru_option)
        ngq_title_ru_view = StringOption(ngq_title_ru_option, self.tr(u'NGQ Title tr'), self)
        self.advanced_options_container.addWidget(ngq_title_ru_view)

        default_proj_option = FileCustomizationOption(u'def_project')
        self._model.addOption(default_proj_option)
        default_proj_view = FileOption(default_proj_option, self.tr(u'Default project'))
        default_proj_view.setFilter(
            "%s %s" % (self.tr(u'QGIS Project'), u'(*.qgs)'))
        self.advanced_options_container.addWidget(default_proj_view)

        default_qgis_opts_option = QGISOptionsOption()
        self._model.addOption(default_qgis_opts_option)
        default_qgis_opts_view = QGISOptions(default_qgis_opts_option, self.tr(u'Default qgis options'))
        self.advanced_options_container.addWidget(default_qgis_opts_view)

        ngq_plugins_option = PluginsCustomizationOption(u'ngq_plugins')
        self._model.addOption(ngq_plugins_option)
        ngq_plugins_view = PluginsOption(ngq_plugins_option)
        self.plugins_option_container.addWidget(ngq_plugins_view)

        ngq_about_pages_option = AboutPagesCustomizationOption(u'ngq_about_pages')
        self._model.addOption(ngq_about_pages_option)
        ngq_about_pages_view = AboutPagesManagerOption(ngq_about_pages_option)
        self.about_pages_container.addWidget(ngq_about_pages_view)

        settings = QSettings()
        if load_conf is not None:
            configuration_file = load_conf
            settings.setValue(u'configuration_file', load_conf)

        configuration_file = settings.value(u'configuration_file', defaultValue=QString(), type=QString)

        if QFileInfo(configuration_file).exists():
            self._model.loadFromLocalSettings(configuration_file)

    def __show_error(self, trace):
        trace = unicode(trace.toUtf8(), encoding="UTF-8")
        last_line = trace.splitlines()[-1]
        MessageDialog.critical(self, self.tr("Error"), last_line, trace)

    def resetModel(self):
        self._model.reset()

    def saveLocalConfiguration(self):
        settings = QSettings()
        configuration_file = settings.value(u'configuration_file', defaultValue=unicode(), type=unicode)
        self._model.saveAsLocalSettings(configuration_file)

    def saveAsLocalConfiguration(self):
        try:
            settings = QSettings()
            configuration_file = settings.value(u'configuration_file', defaultValue=unicode(), type=unicode)
            fileName = QFileDialog.getSaveFileName(self,
                                                   self.tr("Save configuration file"),
                                                   configuration_file,
                                                   self.tr("NGQ configuration file (*.ngqc)"))

            if fileName.isNull() is False:
                fileName = unicode(fileName.toUtf8(), encoding="UTF-8")

                if os.path.splitext(fileName)[1] != u".ngqc":
                    fileName = "%s.ngqc" % fileName

                settings.setValue(u'configuration_file', fileName)
                if not self.actionSave.isEnabled():
                    self.actionSave.setEnabled(True)

                self._model.saveAsLocalSettings(fileName)

        except:
            trace = traceback.format_exc()
            last_line = trace.splitlines()[-1]
            MessageDialog.critical(self, self.tr("Error"), last_line, trace)

    def openLocalConfiguration(self):
        try:
            settings = QSettings()
            configuration_file = settings.value(u'configuration_file', defaultValue=unicode(), type=unicode)
            fileName = QFileDialog.getOpenFileName(self,
                                                   self.tr("Save configuration file"),
                                                   configuration_file,
                                                   self.tr("NGQ configuration file (*.ngqc)"))
            if fileName.isNull() is False:
                fileName = unicode(fileName.toUtf8(), encoding="UTF-8")
                settings.setValue(u'configuration_file', fileName)
                self._model.loadFromLocalSettings(fileName)

        except:
            trace = traceback.format_exc()
            last_line = trace.splitlines()[-1]
            MessageDialog.critical(self, self.tr("Error"), last_line, trace)

    def importConfigurationFromArchive(self):
        pass

    def exportConfigurationToArchive(self):
        try:
            settings = QSettings()
            configuration_file_archive = settings.value(u'configuration_file_archive', defaultValue=unicode(), type=unicode)
            fileName = QFileDialog.getSaveFileName(self,
                                                   self.tr("Open configuration file"),
                                                   configuration_file_archive,
                                                   self.tr("NGQ configuration archive (*.ngqca)"))
            if fileName.isNull() is False:
                fileName = unicode(fileName.toUtf8(), encoding="UTF-8")

                if os.path.splitext(fileName)[1] != u".ngqca":
                    fileName = "%s.ngqca" % fileName

                settings.setValue(u'configuration_file_archive', fileName)

                self._model.saveAsArchive(fileName)
        except:
            trace = traceback.format_exc()
            last_line = trace.splitlines()[-1]
            MessageDialog.critical(self, self.tr("Error"), last_line, trace)

    def editQGISrepos(self):
        dlg = QGISReposDialog()
        if dlg.exec_():
            print "Save "


class NGQConfiguratorApp(QApplication):
    def __init__(self, args):
        super(QApplication, self).__init__(args)

        self.setOrganizationName("NextGIS")
        self.setOrganizationDomain("nextgis.ru")
        self.setApplicationName("NGQ Configurator")

        self.translator = QTranslator()
        self.translator.load(":/NGQConfigurator/i18n/ngq_configurator.qm")
        QApplication.installTranslator(self.translator)

        self.logger = logging.getLogger(unicode(self.applicationName()))
        self.logger.setLevel(logging.DEBUG)

        log_file_name = "_".join(unicode(self.applicationName()).split(u" ")) + "_log.txt"

        fh = RotatingFileHandler(
            os.path.join(unicode(self.applicationDirPath()), log_file_name),
            mode='a',
            maxBytes=102400,
            backupCount=5,
            encoding='utf-8')

        fh.setLevel(logging.DEBUG)
        sh = logging.StreamHandler()
        sh.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        sh.setFormatter(formatter)

        self.logger.addHandler(fh)

        if "--with-consol" in args:
            self.logger.addHandler(sh)

        load_conf = None
        if "--load_conf" in args:
            load_conf = args[args.index("--load_conf") + 1]

        QApplication.instance().logger.info("NGQ Configurator START")
        QApplication.instance().logger.info("args: {0}".format(args))
        QApplication.instance().logger.info("use resources: {0}".format(resources_rc.__file__))
        self.mw = NGQConfigurator(load_conf)
        self.mw.show()

if __name__ == "__main__":
    app = NGQConfiguratorApp(sys.argv)
    res = app.exec_()
    QApplication.instance().logger.info("NGQ Configurator FINISH. " +
                                        "Exit code: {0}".format(res))
    sys.exit(res)
