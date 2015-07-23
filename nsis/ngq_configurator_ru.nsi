SetCompressor /SOLID lzma
RequestExecutionLevel admin

;--- Common parameters ---
!define INSTALLER_ICON "..\icons\ng.ico"
!define SRC "..\dist"
!define PROGRAM_NAME "NGQ Configurator"
!define INSTALLER_NAME "ngq_configurator_setup"
!define PROGRAM_VERSION "0.1.3"
!define UNINSTALLER_NAME "uninstall.exe"
!define CONFIGURATOR_RUN_LNK_NAME "NGQ Configurator"
!define BUILD_MANAGER_RUN_LNK_NAME "Build manager"

Name "${PROGRAM_NAME}"
OutFile "${INSTALLER_NAME}-${PROGRAM_VERSION}.exe"
InstallDir "$PROGRAMFILES\NGQConfigurator"

!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "utils.nsh"
!include "FileAssoc.nsh"

ShowInstDetails show
ShowUnInstDetails show

!define MUI_ABORTWARNING

!define MUI_ICON "${INSTALLER_ICON}"
!define MUI_UNICON "${INSTALLER_ICON}"

!define MUI_WELCOMEPAGE_TITLE_3LINES

!insertmacro MUI_PAGE_WELCOME
;!insertmacro MUI_PAGE_LICENSE "Installer-Files\LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_INSTFILES

!define MUI_FINISHPAGE_TITLE_3LINES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "Russian"
;--------------------------------
;Installer Sections
Section "NGQConfigurator" NGQConfigurator
	SectionIn RO

	Var /GLOBAL INSTALL_DIR
	StrCpy $INSTALL_DIR "$INSTDIR"

	SetOverwrite try
	SetShellVarContext current

    SetOutPath "$INSTALL_DIR"
	File /r "${SRC}\*.*"

    SetOutPath "$INSTALL_DIR\icons"
	File "${INSTALLER_ICON}"

    WriteUninstaller "$INSTALL_DIR\${UNINSTALLER_NAME}"

	WriteRegStr HKLM "Software\${PROGRAM_NAME}" "Name" "${PROGRAM_NAME}"
	WriteRegStr HKLM "Software\${PROGRAM_NAME}" "VersionNumber" "${PROGRAM_VERSION}"
	WriteRegStr HKLM "Software\${PROGRAM_NAME}" "Publisher" "NextGIS"
	WriteRegStr HKLM "Software\${PROGRAM_NAME}" "WebSite" "http://nextgis.ru"
	WriteRegStr HKLM "Software\${PROGRAM_NAME}" "InstallPath" "$INSTALL_DIR"

	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PROGRAM_NAME}" "DisplayName" "${PROGRAM_NAME}"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PROGRAM_NAME}" "UninstallString" "$INSTALL_DIR\${UNINSTALLER_NAME}"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PROGRAM_NAME}" "DisplayVersion" "${PROGRAM_VERSION}"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PROGRAM_NAME}" "DisplayIcon" "$INSTALL_DIR\icons\ng.ico"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PROGRAM_NAME}" "EstimatedSize" 1
	;WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PROGRAM_NAME}" "HelpLink" "${WIKI_PAGE}"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PROGRAM_NAME}" "URLInfoAbout" "http://nextgis.ru"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PROGRAM_NAME}" "Publisher" "NextGIS"

SectionEnd

Section "-DONE"
    SetShellVarContext all
    CreateDirectory "$SMPROGRAMS\${PROGRAM_NAME}"
    GetFullPathName /SHORT $0 $INSTALL_DIR
    System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("OSGEO4W_ROOT", "$0").r0'
    System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("OSGEO4W_STARTMENU", "$SMPROGRAMS\${PROGRAM_NAME}").r0'

    ReadEnvStr $0 COMSPEC

    Delete "$DESKTOP\${CONFIGURATOR_RUN_LNK_NAME}.lnk"
    Delete "$DESKTOP\${BUILD_MANAGER_RUN_LNK_NAME}.lnk"
    CreateShortCut "$DESKTOP\${CONFIGURATOR_RUN_LNK_NAME}.lnk" "$INSTALL_DIR\ngq_configurator.exe" ""\
    "$INSTALL_DIR\ngq_configurator.exe" "" SW_SHOWNORMAL "" "Запустить конфигуратор NGQ"

    CreateShortCut "$DESKTOP\${BUILD_MANAGER_RUN_LNK_NAME}.lnk" "$INSTALL_DIR\ngq_builds_manager.exe" ""\
    "$INSTALL_DIR\ngq_builds_manager.exe" "" SW_SHOWNORMAL "" "Запустить менеджер сборок NGQ"

    Delete "$SMPROGRAMS\${PROGRAM_NAME}\${CONFIGURATOR_RUN_LNK_NAME}.lnk"
    Delete "$SMPROGRAMS\${PROGRAM_NAME}\${BUILD_MANAGER_RUN_LNK_NAME}.lnk"
    CreateShortCut "$SMPROGRAMS\${PROGRAM_NAME}\${CONFIGURATOR_RUN_LNK_NAME}.lnk" "$INSTALL_DIR\ngq_configurator.exe" ""\
    "$INSTALL_DIR\ngq_configurator.exe" "" SW_SHOWNORMAL "" "Запустить конфигуратор NGQ"
    CreateShortCut "$SMPROGRAMS\${PROGRAM_NAME}\${BUILD_MANAGER_RUN_LNK_NAME}.lnk" "$INSTALL_DIR\ngq_builds_manager.exe" ""\
    "$INSTALL_DIR\ngq_builds_manager.exe" "" SW_SHOWNORMAL "" "Запустить менеджер сборок NGQ"

    Delete "$SMPROGRAMS\${PROGRAM_NAME}\Удалить ${PROGRAM_NAME}.lnk"
    CreateShortCut "$SMPROGRAMS\${PROGRAM_NAME}\Удалить ${PROGRAM_NAME}.lnk" "$INSTALL_DIR\${UNINSTALLER_NAME}" "" \
    "$INSTALL_DIR\${UNINSTALLER_NAME}" "" SW_SHOWNORMAL "" "Удалить ${PROGRAM_NAME}"

    !insertmacro APP_ASSOCIATE "ngqc" "ngqc.config" "NGQ configuration" "$INSTALL_DIR\icons\ng.ico" "Open with ${PROGRAM_NAME}" \ 
    "$\"$INSTALL_DIR\ngq_configurator.exe$\" --load_conf $\"%1$\""
    !insertmacro UPDATEFILEASSOC
SectionEnd

Function .onInit
    Var /GLOBAL uninstaller_path
    Var /GLOBAL installer_path

    !insertmacro IfKeyExists HKLM "Software" "${PROGRAM_NAME}"
    Pop $R0

    ${If} $R0 = 1
        ReadRegStr $0 HKLM "Software\${PROGRAM_NAME}" "VersionNumber"

        MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
          "Уже установлен ($0). Переустановить (${PROGRAM_VERSION})?" \
          IDOK uninst  IDCANCEL  quit_uninstall

            uninst:
                ReadRegStr $uninstaller_path HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PROGRAM_NAME}" "UninstallString"
                ReadRegStr $installer_path HKLM "Software\${PROGRAM_NAME}" "InstallPath"
                ExecWait '$uninstaller_path _?=$installer_path' $1

                ${If} $1 = 0
                    Goto continue_uninstall
                ${Else}
                    Goto quit_uninstall
                ${EndIf}

            quit_uninstall:
                Abort

            continue_uninstall:
                RMDir /r "$installer_path"
    ${EndIf}
FunctionEnd

;--------------------------------
;Uninstaller Section
Section "Uninstall"
	RMDir /r "$INSTDIR"

	SetShellVarContext all
	Delete "$DESKTOP\${CONFIGURATOR_RUN_LNK_NAME}.lnk"
    Delete "$DESKTOP\${BUILD_MANAGER_RUN_LNK_NAME}.lnk"

	SetShellVarContext all
	RMDir /r "$SMPROGRAMS\${PROGRAM_NAME}\${CONFIGURATOR_RUN_LNK_NAME}.lnk"
    RMDir /r "$SMPROGRAMS\${PROGRAM_NAME}\${BUILD_MANAGER_RUN_LNK_NAME}.lnk"

	DeleteRegKey HKLM "Software\${PROGRAM_NAME}"
	DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PROGRAM_NAME}"

    !insertmacro APP_UNASSOCIATE "ngqc" "ngqc.config"
    !insertmacro UPDATEFILEASSOC
SectionEnd
