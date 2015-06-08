from distutils.core import setup
import py2exe

setup(
    windows=[{"script":"ngq_configurator.py", "icon_resources": [(1, "icons\\ng.ico")]}, {"script":"ngq_builds_manager.py", "icon_resources": [(1, "icons\\ng.ico")]}],
    options={"py2exe": {"includes":["sip", "urllib2"]}},
    data_files=[
        ('imageformats', [
                    r'd:\DevelopCases\Python279\Lib\site-packages\PyQt4\plugins\imageformats\qgif4.dll',
                    r'd:\DevelopCases\Python279\Lib\site-packages\PyQt4\plugins\imageformats\qico4.dll',
                    r'd:\DevelopCases\Python279\Lib\site-packages\PyQt4\plugins\imageformats\qjpeg4.dll',
                    r'd:\DevelopCases\Python279\Lib\site-packages\PyQt4\plugins\imageformats\qsvg4.dll',
                    r'd:\DevelopCases\Python279\Lib\site-packages\PyQt4\plugins\imageformats\qtga4.dll',
                    r'd:\DevelopCases\Python279\Lib\site-packages\PyQt4\plugins\imageformats\qtiff4.dll'
                    ])
    ]
)
