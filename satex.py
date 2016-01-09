# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SatEx
                                 A QGIS plugin
 L8 processing towards exposure
                              -------------------
        begin                : 2015-12-14
        git sha              : $Format:%H$
        copyright            : (C) 2015 by GFZ Michael Haas
        email                : mhaas@gfz-potsdam.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import PyQt4.QtCore
import PyQt4.QtGui
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from satex_dialog import PreprocessingDialog, ClassificationDialog
import os.path

class SatEx:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = PyQt4.QtCore.QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'SatEx_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = PyQt4.QtCore.QTranslator()
            self.translator.load(locale_path)

            if PyQt4.QtCore.qVersion() > '4.3.3':
                PyQt4.QtCore.QCoreApplication.installTranslator(self.translator)

        try:
            import otbApplication
        except:
            print 'Error: Plugin requires installation of OrfeoToolbox'
            raise RuntimeError

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&GFZ SatEx')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'SatEx')
        self.toolbar.setObjectName(u'SatEx')

        #create dialogs and keep reference
        self.Pdlg = PreprocessingDialog()
#        self.Cdlg = ClassificationDialog()

        #gui interactions
        self.Pdlg.lineEdit.clear()
        self.Pdlg.pushButton.clicked.connect(self.select_input_raster)
        self.Pdlg.lineEdit_2.clear()
        self.Pdlg.pushButton_2.clicked.connect(self.select_roi)
        self.Pdlg.lineEdit_3.clear()
        self.Pdlg.pushButton_3.clicked.connect(self.select_output_name)
        self.Pdlg.progressBar.reset()

        #TODO:defaults for development
        self.Pdlg.lineEdit.setText('/home/mhaas/PhD/Routines/rst/plugin/data/LC81740382015287LGN00')
        self.Pdlg.lineEdit_2.setText('/home/mhaas/PhD/Routines/rst/kerak.shp')
        self.Pdlg.lineEdit_3.setText('/home/mhaas/PhD/Routines/rst/test.vrt')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return PyQt4.QtCore.QCoreApplication.translate('SatEx', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = PyQt4.QtGui.QIcon(icon_path)
        action = PyQt4.QtGui.QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/SatEx/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Preprocessing'),
            callback=self.run_preprocessing,
            parent=self.iface.mainWindow())
        icon_path = ':/plugins/SatEx/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Classification'),
            callback=self.run_classification,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&GFZ SatEx'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def updatePForm(self):
        #get user edits
        self.ls_path = self.Pdlg.lineEdit.text()+'/'
        self.roi = self.Pdlg.lineEdit_2.text()
        self.out_fname = self.Pdlg.lineEdit_3.text()

    def select_input_raster(self):
        dirname = PyQt4.QtGui.QFileDialog.getExistingDirectory(self, "Select input directory ","",PyQt4.QtGui.QFileDialog.ShowDirsOnly)
        self.Pdlg.lineEdit.setText(dirname)

    def select_roi(self):
        filename = PyQt4.QtGui.QFileDialog.getOpenFileName(self, "Select region of interest ","","*.shp")
        self.Pdlg.lineEdit_2.setText(filename)

    def select_output_name(self):
        filename = PyQt4.QtGui.QFileDialog.getSaveFileName(self, "Select output file ","","*.vrt")
        self.Pdlg.lineEdit_3.setText(filename)

    def calculate_progress(self):
        self.processed = self.processed + 1
        percentage_new = (self.processed * 100) / self.ntasks
        if percentage_new > self.percentage:
            self.percentage = percentage_new

    def updateTextbox(self,msg):
        self.textBrowser.append(msg)

    def errorMsg(self,msg):
        self.iface.messageBar().pushMessage('Error: '+ msg,self.iface.messageBar().CRITICAL)

    def run_preprocessing(self):
        """Run method that performs all the real work"""
        #self.Pdlg.setModal(False)
        self.Pdlg.show()

        #Dialog event loop
        result = self.Pdlg.exec_()
        if result:
            self.processed = 0
            self.percentage = 0
            #TODO:fix
            self.ntasks = 3
            #Get user edits
            self.updatePForm()
            #self.Pdlg.startWorker(self.iface, self.ls_path, self.roi, self.out_fname)

            import utils
            import traceback
            import qgis.core
            import ogr
            import subprocess

            try:
                import otbApplication
            except:
                print 'Plugin requires installation of OrfeoToolbox'

            #find the number of different L8 scenes
            #by reading all TIFs splitting off '_Bxy.TIF' and getting unique strings
            try:
                try:
                    #instantiate utilities function
                    ut = utils.utils()
                    #delete any old tmp files that might be in the directory from a killed task
                    old=ut.delete_tmps(self.ls_path)
                    if old > 0: qgis.core.QgsMessageLog.logMessage('Old *satexTMP* files were present. They were deleted.')
                    scenes = set(['_'.join(s.split('_')[:-1]) for s in ut.findFiles(self.ls_path,'*.TIF')])
                    #adjust number of tasks
                    self.ntasks = self.ntasks*len(scenes)
                    qgis.core.QgsMessageLog.logMessage(str('Found {} Landsat 8 scene(s) in {}'.format(len(scenes),self.ls_path)))
                except Exception as e:
                    e = str('Found no Landsat 8 scene in {}'.format(self.ls_path))
                    raise Exception

                #check shapefile roi
                try:
                    driver = ogr.GetDriverByName('ESRI Shapefile')
                    dataSource = driver.Open(self.roi,0)
                    layer = dataSource.GetLayer()
                    qgis.core.QgsMessageLog.logMessage(str('Using {} as ROI'.format(self.roi)))
                except Exception as e:
                    e = str('Could not open {}'.format(self.roi))
                    raise Exception

                #loop through all scenes
                for scene in scenes:
                    #find all bands for scene exclude quality band BQA and B8
                    try:
                        bands = [b for b in ut.findFiles(self.ls_path,scene+'*.TIF') if '_BQA' not in b]
                        bands = [b for b in bands if '_B8' not in b]
                        #check if there are 10 bands
                        #if len(bands)!=11:
                        if len(bands)!=10:
                            e = str('Found {} instead of 10 bands (excluding B8 and BQA) for scene {}'.format(len(bands),scene))
                            raise Exception
                        else:
                            #self.status.emit('Found all 11 bands for scene {}'.format(scene))
                            qgis.core.QgsMessageLog.logMessage(str('Found all 10 bands (excluding B8 and BQA) for scene {} '.format(scene)))
                    except Exception as e:
                        e = str('Could not find all 10 bands (excluding B8 and BQA) for scene {}'.format(scene))
                        raise Exception

                    #use gdalwarp to cut bands to roi
                    try:
                        #go through bands
                        for band in bands:
                            #self.status.emit('Cropping band {} to ROI'.format(band))
                            qgis.core.QgsMessageLog.logMessage(str('Cropping band {} to ROI'.format(band)))
                            cmd = ['gdalwarp','-q','-cutline',self.roi,'-crop_to_cutline',self.ls_path+band,self.ls_path+band[:-4]+'_satexTMP_ROI.TIF']
                            subprocess.check_call(cmd)
                        self.calculate_progress()
                    except Exception as e:
                        e = str('Could not execute gdalwarp cmd: {}'.format(' '.join(cmd)))
                        raise Exception

                    # Layerstack
                    try:
                        #respect order B1,B2,B3,B4,B5,B6,B7,B9,B10,B11
                        #in_files = [str(self.ls_path+b[:-4]+'_satexTMP_ROI.TIF') for b in bands if '_B8' not in b]
                        in_files = [str(self.ls_path+b[:-4]+'_satexTMP_ROI.TIF') for b in bands]
                        in_files.sort()
                        #B10,B11 considered smaller --> resort
                        in_files = in_files[2:] + in_files[0:2]
                        out_file = str(self.ls_path+scene+'_satexTMP_mul.TIF')
                        #call otb wrapper
                        #self.status.emit('Concatenating bands for pansharpening scene {}'.format(scene))
                        qgis.core.QgsMessageLog.logMessage(str('Concatenate bands for pansharpening scene {}'.format(scene)))
                        ut.otb_concatenate(in_files,out_file)
                        self.calculate_progress()
                    except Exception as e:
                        e = str('Could not execute OTB ConcatenateImages for scene: {}\nin_files: {}\nout_file: {}'.format(scene,in_files,out_file))
                        raise Exception

                # after all scenes were processed combine them to a virtual raster tile
                try:
                    cmd = ["gdalbuildvrt","-srcnodata","0","-overwrite",self.out_fname]
                    files = [f for f in ut.findFiles(self.ls_path,'*satexTMP_mul.TIF')]
                    for f in files:
                        cmd.append(str(self.ls_path+f))
                    subprocess.check_call(cmd)
                    qgis.core.QgsMessageLog.logMessage(str('Merged {} different L8 scenes to {}'.format(len(files),self.out_fname)))
                    self.calculate_progress()
                except:
                    e = str('Could not execute gdalbuildvrt cmd: {}'.format(' '.join(cmd)))
                    raise Exception
            except:
                self.errorMsg(e)
                self.finished.emit('Failed')
                qgis.core.QgsMessageLog.logMessage(str('Deleting temporary files'))
                ut.delete_tmps(self.ls_path)
            else:
                qgis.core.QgsMessageLog.logMessage(str('Processing sucessfully completed'))
                qgis.core.QgsMessageLog.logMessage(str('Deleting temporary files'))
                self.iface.messageBar().pushMessage('Processing successfully completed, see log for details',self.iface.messageBar().SUCCESS,duration=3)
                ut.delete_tmps(self.ls_path)

    def run_classification(self):
        """Run method that performs all the real work"""
        self.Cdlg.setModal(False)
        self.Cdlg.show()